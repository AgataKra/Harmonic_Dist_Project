from dataclasses import replace
import numpy as np
from scipy.optimize import minimize

from spice_simulation import (
    SimulationParameters,
    SimulationRunner,
    calculate_dc_ripple,
    calculate_harmonics,
)


class OptimizationRunner:
    def __init__(self, runner: SimulationRunner | None = None):
        self.runner = runner or SimulationRunner()

    def evaluate_objective(self, l_vector: list[float], base_params: SimulationParameters) -> float:
        l_ac, l_dc = l_vector

        # Hard penalty for non-physical zero or negative values
        if l_ac <= 1e-6 or l_dc <= 1e-6:
            return 1e6

        # Fast simulation configuration
        opt_step_time = max(base_params.step_time, 1e-5)
        sim_params = replace(
            base_params,
            l_ac=l_ac,
            l_dc=l_dc,
            step_time=opt_step_time,
            stop_time=0.26,
        )

        try:
            result = self.runner.run(sim_params, fast_mode=True)
        except Exception:
            return 1e6

        # Slice settled region between 0.20s and 0.26s
        t_mask = (result.time >= 0.20) & (result.time <= 0.26)
        if not np.any(t_mask) or np.sum(t_mask) < 4:
            return 1e6

        settled_time = result.time[t_mask]
        settled_v_out = result.output_voltage[t_mask]
        settled_i_phase_a = result.input_currents["Phase A"][t_mask]

        # 1. Input Current THD %
        harmonics_i_in = calculate_harmonics(settled_time, settled_i_phase_a, sim_params.frequency)
        thd_i_in = harmonics_i_in.thd_percent

        # 2. Output Voltage Ripple %
        ripple_v_out = calculate_dc_ripple(settled_time, settled_v_out, sim_params.frequency)

        # 3. Output DC Voltage Deviation Penalty (Deviation from Ideal 6-Pulse Output)
        v_dc_ideal = (3.0 * np.sqrt(6.0) / np.pi) * sim_params.v_phase_rms
        v_dc_actual = float(np.mean(settled_v_out))

        # Percentage difference from ideal DC output voltage
        v_dc_deviation_percent = 100.0 * abs(v_dc_ideal - v_dc_actual) / v_dc_ideal

        # 4. Inductance Reactance Cost Penalty
        x_ac = 2.0 * np.pi * sim_params.frequency * l_ac
        x_dc = 2.0 * np.pi * sim_params.frequency * l_dc
        inductance_cost = (x_ac / (sim_params.r_source + 1e-3)) + (x_dc / (sim_params.r_load + 1e-3))

        # Weight factors:
        # w1 = Input THD weight
        # w2 = DC Ripple weight
        # w3 = DC Voltage Drop/Deviation weight
        # w4 = Inductance scale penalty weight
        w1, w2, w3, w4 = 1.0, 1.0, 1.5, 0.05
        score = (w1 * thd_i_in) + (w2 * ripple_v_out) + (w3 * v_dc_deviation_percent) + (w4 * inductance_cost)
        return float(score)

    def optimize(self, base_params: SimulationParameters, progress_callback=None):
        initial_guess = [base_params.l_ac, base_params.l_dc]

        min_l = 1e-4
        max_lac = 0.05 * (50.0 / base_params.frequency)
        max_ldc = 0.1 * (50.0 / base_params.frequency)
        bounds = [(min_l, max_lac), (min_l, max_ldc)]
        eval_count = [0]

        def callback(xk):
            eval_count[0] += 1
            if progress_callback:
                progress_callback(eval_count[0], xk[0], xk[1])

        res = minimize(
            self.evaluate_objective,
            x0=initial_guess,
            args=(base_params,),
            method="Nelder-Mead",
            bounds=bounds,
            callback=callback,
            options={"maxiter": 20, "xatol": 5e-4, "fatol": 5e-2},
        )

        best_l_ac, best_l_dc = res.x

        best_params = replace(base_params, l_ac=best_l_ac, l_dc=best_l_dc)
        best_result = self.runner.run(best_params, fast_mode=False)
        return best_params, best_result, res.fun