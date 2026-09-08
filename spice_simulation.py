from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np
from PySpice.Spice.Netlist import Circuit


PROJECT_ROOT = Path(__file__).resolve().parent

#This file handles SPICE simulation along with parsing the results.

@dataclass
class SimulationParameters:
    v_phase_rms: float = 230.0
    frequency: float = 50.0
    r_source: float = 0.2
    l_ac: float = 0.005
    l_dc: float = 0.02
    r_load: float = 100.0
    c_load: float = 0.001
    sim_mode: str = "auto"
    stop_time: float = 0.1
    step_time: float = 1e-5

    def validate(self):
        positive_fields = {
            "Phase voltage RMS": self.v_phase_rms,
            "Frequency": self.frequency,
            "Source resistance": self.r_source,
            "AC-side inductance l_ac": self.l_ac,
            "DC-side inductance l_dc": self.l_dc,
            "Load resistance": self.r_load,
            "Load capacitance": self.c_load,
            "Manual stop time": self.stop_time,
            "Simulation step": self.step_time,
        }
        for label, value in positive_fields.items():
            if value <= 0:
                raise ValueError(f"{label} must be greater than zero.")
        if self.sim_mode not in ("auto", "manual"):
            raise ValueError("Simulation mode must be 'auto' or 'manual'.")
        if self.step_time >= self.effective_stop_time():
            raise ValueError("Simulation step must be smaller than the stop time.")

    def estimated_stop_time(self) -> float:
        period = 1.0 / self.frequency
        lc_settle = 8.0 * np.sqrt(max(self.l_dc * self.c_load, 0.0))
        return max(12.0 * period, lc_settle, 0.12)

    def effective_stop_time(self) -> float:
        if self.sim_mode == "manual":
            return self.stop_time
        return self.estimated_stop_time()


@dataclass
class HarmonicSpectrum:
    orders: np.ndarray
    magnitudes: np.ndarray
    thd_percent: float
    fundamental_rms: float


@dataclass
class SimulationResult:
    time: np.ndarray
    input_voltages: dict
    input_currents: dict
    output_voltage: np.ndarray
    output_current: np.ndarray
    harmonics: dict
    thd: dict
    netlist: str
    params: SimulationParameters


class SimulationRunner:
    def __init__(self, netlist_path=None):
        self.netlist_path = Path(netlist_path) if netlist_path else PROJECT_ROOT / "netlists" / "six_pulse_rectifier.net"
        self.base_netlist = self.netlist_path.read_text(encoding="utf-8")

    def render_netlist(self, params: SimulationParameters) -> str:
        net = re.sub(r"(?im)^\s*\.param\s+.*$", "", self.base_netlist)
        net = re.sub(r"(?im)^\s*\.tran\s+.*$", "", net)
        net = re.sub(r"(?im)^\s*\.end\s*$", "", net).strip()
        param_lines = [

            f".param v_phase_rms={params.v_phase_rms}",
            ".param v_amp={sqrt(2)*v_phase_rms}",
            f".param freq={params.frequency}",
            f".param r_source={params.r_source}",
            f".param l_ac={params.l_ac}",
            f".param l_dc={params.l_dc}",
            f".param r_load={params.r_load}",
            f".param c_load={params.c_load}",
        ]
        stop_time = params.effective_stop_time()
        tran_line = f".tran {params.step_time} {stop_time} 0 {params.step_time}"
        return "\n".join([net, *param_lines, tran_line, ".end", ""])

    def run(self, params: SimulationParameters) -> SimulationResult:
        netlist = self.render_netlist(params)
        circuit = Circuit("Six pulse rectifier")
        circuit.raw_spice += netlist

        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.transient(
            step_time=params.step_time,
            end_time=params.effective_stop_time(),
        )

        time = self._vector_to_array(analysis.time)
        input_voltages = {
            "Phase A": self._node_voltage(analysis, "net_in1"),
            "Phase B": self._node_voltage(analysis, "net_in2"),
            "Phase C": self._node_voltage(analysis, "net_in3"),
        }
        input_currents = {
            "Phase A": self._branch_current(analysis, "v1"),
            "Phase B": self._branch_current(analysis, "v2"),
            "Phase C": self._branch_current(analysis, "v3"),
        }
        output_voltage = self._node_voltage(analysis, "load_p") - self._node_voltage(analysis, "net_dc_neg")
        output_current = self._branch_current(analysis, "vload")

        harmonics = {}
        thd = {}
        for name, values in input_voltages.items():
            key = f"Input voltage {name}"
            spectrum = calculate_harmonics(time, values, params.frequency)
            harmonics[key] = spectrum
            thd[key] = spectrum.thd_percent
        for name, values in input_currents.items():
            key = f"Input current {name}"
            spectrum = calculate_harmonics(time, values, params.frequency)
            harmonics[key] = spectrum
            thd[key] = spectrum.thd_percent

        output_voltage_spectrum = calculate_harmonics(time, output_voltage, params.frequency)
        output_current_spectrum = calculate_harmonics(time, output_current, params.frequency)
        harmonics["Output voltage"] = output_voltage_spectrum
        harmonics["Output current"] = output_current_spectrum
        thd["Output voltage"] = output_voltage_spectrum.thd_percent
        thd["Output current"] = output_current_spectrum.thd_percent

        return SimulationResult(
            time=time,
            input_voltages=input_voltages,
            input_currents=input_currents,
            output_voltage=output_voltage,
            output_current=output_current,
            harmonics=harmonics,
            thd=thd,
            netlist=netlist,
            params=params,
        )

    @staticmethod
    def _vector_to_array(vector) -> np.ndarray:
        return np.asarray(vector, dtype=float)

    @staticmethod
    def _node_voltage(analysis, node_name: str) -> np.ndarray:
        return SimulationRunner._vector_to_array(analysis[node_name])

    @staticmethod
    def _branch_current(analysis, branch_name: str) -> np.ndarray:
        return SimulationRunner._vector_to_array(analysis.branches[branch_name])


def calculate_harmonics(time, values, base_frequency, max_order=30) -> HarmonicSpectrum:
    time = np.asarray(time, dtype=float)
    values = np.asarray(values, dtype=float)
    if len(time) < 4 or base_frequency <= 0:
        orders = np.arange(1, max_order + 1)
        return HarmonicSpectrum(orders, np.zeros_like(orders, dtype=float), 0.0, 0.0)

    period = 1.0 / base_frequency
    start_time = max(time[0], time[-1] - 6.0 * period)
    mask = time >= start_time
    selected_time = time[mask]
    selected_values = values[mask]
    if len(selected_time) < 4:
        selected_time = time
        selected_values = values

    selected_values = selected_values - np.mean(selected_values)
    duration = selected_time[-1] - selected_time[0]
    sample_count = len(selected_time)
    if duration <= 0 or sample_count < 4:
        orders = np.arange(1, max_order + 1)
        return HarmonicSpectrum(orders, np.zeros_like(orders, dtype=float), 0.0, 0.0)

    uniform_time = np.linspace(selected_time[0], selected_time[-1], sample_count)
    uniform_values = np.interp(uniform_time, selected_time, selected_values)
    window = np.hanning(sample_count)
    coherent_gain = np.sum(window) / sample_count
    spectrum = np.fft.rfft(uniform_values * window)
    frequencies = np.fft.rfftfreq(sample_count, d=(uniform_time[1] - uniform_time[0]))
    peak_magnitudes = 2.0 * np.abs(spectrum) / (sample_count * coherent_gain)

    orders = np.arange(1, max_order + 1)
    rms_magnitudes = np.zeros_like(orders, dtype=float)
    for index, order in enumerate(orders):
        target = order * base_frequency
        bin_index = int(np.argmin(np.abs(frequencies - target)))
        rms_magnitudes[index] = peak_magnitudes[bin_index] / np.sqrt(2.0)

    fundamental_rms = rms_magnitudes[0]
    if fundamental_rms <= 1e-12:
        thd_percent = 0.0
    else:
        thd_percent = 100.0 * np.sqrt(np.sum(rms_magnitudes[1:] ** 2)) / fundamental_rms

    return HarmonicSpectrum(orders, rms_magnitudes, thd_percent, fundamental_rms)
