from dataclasses import replace
from pathlib import Path
import threading
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from gui.results import ResultsWindow, SweepResultsWindow
from gui.sweep import SweepCase, SweepDialog
from optimization import OptimizationRunner
from spice_simulation import SimulationParameters, SimulationRunner


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class App:
    def __init__(self, root):
        self.root = root
        self.default_params = SimulationParameters()
        self.runner = SimulationRunner()
        self.optimizer = OptimizationRunner(self.runner)
        self.entries = {}
        self.status = tk.StringVar(value="Ready")
        self._init_window()
        self._build_ui()

    def _init_window(self):
        self.root.title("Harmonic distortion simulator")
        self.root.minsize(1060, 680)
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _build_ui(self):
        form = ttk.Frame(self.root, padding=12)
        form.grid(row=0, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        schematic = ttk.Frame(self.root, padding=12)
        schematic.grid(row=0, column=1, sticky="nsew")
        schematic.columnconfigure(0, weight=1)
        schematic.rowconfigure(0, weight=1)

        fields = [
            ("v_phase_rms", "Phase voltage RMS [V]", self.default_params.v_phase_rms),
            ("frequency", "Frequency [Hz]", self.default_params.frequency),
            ("r_source", "Source resistance [Ohm]", self.default_params.r_source),
            ("l_ac", "AC-side inductance l_ac [H]", self.default_params.l_ac),
            ("l_dc", "DC-side inductance l_dc [H]", self.default_params.l_dc),
            ("r_load", "Load resistance [Ohm]", self.default_params.r_load),
            ("c_load", "Load capacitance [F]", self.default_params.c_load),
            ("step_time", "Simulation maximum step [s]", self.default_params.step_time),
            ("stop_time", "Stop time [s]", self.default_params.stop_time),
        ]

        for row, (name, label, value) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=str(value))
            entry = ttk.Entry(form, width=18, textvariable=var)
            entry.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=4)
            self.entries[name] = var

        buttons = ttk.Frame(form)
        buttons.grid(row=len(fields), column=0, columnspan=2, sticky="ew", pady=(12, 0))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        buttons.columnconfigure(2, weight=1)
        buttons.columnconfigure(3, weight=1)

        self.run_button = ttk.Button(buttons, text="Run simulation", command=self.run_sim)
        self.run_button.grid(row=0, column=0, sticky="ew", padx=(0, 2))

        self.sweep_button = ttk.Button(buttons, text="Run sweep", command=self.open_sweep_dialog)
        self.sweep_button.grid(row=0, column=1, sticky="ew", padx=2)

        self.optimize_button = ttk.Button(buttons, text="Optimize L", command=self.run_optimization)
        self.optimize_button.grid(row=0, column=2, sticky="ew", padx=2)

        ttk.Button(buttons, text="Reset", command=self.reset_values).grid(row=0, column=3, sticky="ew", padx=(2, 0))

        ttk.Label(form, textvariable=self.status, foreground="#345").grid(
            row=len(fields) + 1, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )

        self.img_schematic = tk.PhotoImage(file=str(PROJECT_ROOT / "img" / "rectifier_diag_placeholder.png"))
        ttk.Label(schematic, image=self.img_schematic, anchor="center").grid(row=0, column=0, sticky="nsew")
        ttk.Label(
            schematic,
            text="Six pulse three-phase rectifier with AC source impedance, DC choke, and parallel RC load",
            anchor="center",
        ).grid(row=1, column=0, sticky="ew", pady=(8, 0))

    def reset_values(self):
        for name, var in self.entries.items():
            var.set(str(getattr(self.default_params, name)))
        self.status.set("Ready")

    def _read_float(self, name, label, positive=True):
        raw_value = self.entries[name].get().strip()
        try:
            value = float(raw_value)
        except ValueError as exc:
            raise ValueError(f"{label} must be a number.") from exc
        if positive and value <= 0:
            raise ValueError(f"{label} must be greater than zero.")
        return value

    def _read_params(self):
        params = SimulationParameters(
            v_phase_rms=self._read_float("v_phase_rms", "Phase voltage RMS"),
            frequency=self._read_float("frequency", "Frequency"),
            r_source=self._read_float("r_source", "Source resistance"),
            l_ac=self._read_float("l_ac", "AC-side inductance l_ac"),
            l_dc=self._read_float("l_dc", "DC-side inductance l_dc"),
            r_load=self._read_float("r_load", "Load resistance"),
            c_load=self._read_float("c_load", "Load capacitance"),
            stop_time=self._read_float("stop_time", "Stop time"),
            step_time=self._read_float("step_time", "Simulation step"),
        )
        params.validate()
        return params

    def run_sim(self):
        try:
            params = self._read_params()
        except ValueError as exc:
            messagebox.showerror("Invalid parameter", str(exc))
            self.status.set("Correct the highlighted input and run again.")
            return

        self._set_run_buttons_state("disabled")
        self.status.set("Simulation running...")
        worker = threading.Thread(target=self._run_worker, args=(params,), daemon=True)
        worker.start()

    def open_sweep_dialog(self):
        try:
            params = self._read_params()
        except ValueError as exc:
            messagebox.showerror("Invalid parameter", str(exc))
            self.status.set("Correct the highlighted input and run again.")
            return
        SweepDialog(self.root, params, self._start_sweep)

    def _run_worker(self, params):
        try:
            result = self.runner.run(params)
        except Exception as exc:
            details = traceback.format_exc()
            self.root.after(0, lambda: self._simulation_failed(exc, details))
            return
        self.root.after(0, lambda: self._simulation_finished(result))

    def _start_sweep(self, base_params, sweep_parameter, sweep_label, values):
        self._set_run_buttons_state("disabled")
        self.status.set(f"Sweep running 0/{len(values)}...")
        worker = threading.Thread(
            target=self._sweep_worker,
            args=(base_params, sweep_parameter, sweep_label, values),
            daemon=True,
        )
        worker.start()

    def _sweep_worker(self, base_params, sweep_parameter, sweep_label, values):
        results = []
        try:
            for index, value in enumerate(values, start=1):
                params = replace(base_params, **{sweep_parameter: value})
                result = self.runner.run(params)
                results.append(SweepCase(value=value, label=f"{sweep_label}={value:g}", result=result))
                self.root.after(0, lambda done=index, total=len(values): self.status.set(f"Sweep running {done}/{total}..."))
        except Exception as exc:
            details = traceback.format_exc()
            self.root.after(0, lambda: self._simulation_failed(exc, details))
            return
        self.root.after(0, lambda: self._sweep_finished(sweep_label, results))

    def _simulation_failed(self, exc, details):
        self._set_run_buttons_state("normal")
        self.status.set("Simulation failed.")
        messagebox.showerror("Simulation failed", f"{exc}\n\nDetails:\n{details}")

    def _simulation_finished(self, result):
        self._set_run_buttons_state("normal")
        self.status.set("Ready")
        ResultsWindow(self.root, result)

    def _sweep_finished(self, sweep_label, results):
        self._set_run_buttons_state("normal")
        self.status.set("Ready")
        SweepResultsWindow(self.root, sweep_label, results)

    def run_optimization(self):
        try:
            params = self._read_params()
        except ValueError as exc:
            messagebox.showerror("Invalid parameter", str(exc))
            self.status.set("Correct the highlighted input and run again.")
            return

        self._set_run_buttons_state("disabled")
        self.status.set("Optimizing inductances...")
        worker = threading.Thread(target=self._optimization_worker, args=(params,), daemon=True)
        worker.start()

    def _optimization_worker(self, params):
        try:
            def on_progress(step, l_ac, l_dc):
                self.root.after(
                    0,
                    lambda: self.status.set(
                        f"Optimization step {step}: L_ac={l_ac * 1e3:.2f}mH, L_dc={l_dc * 1e3:.2f}mH"
                    ),
                )

            best_params, best_result, score = self.optimizer.optimize(params, progress_callback=on_progress)
        except Exception as exc:
            details = traceback.format_exc()
            self.root.after(0, lambda: self._simulation_failed(exc, details))
            return

        self.root.after(0, lambda: self._optimization_finished(best_params, best_result, score))

    def _optimization_finished(self, best_params, best_result, score):
        self._set_run_buttons_state("normal")
        self.entries["l_ac"].set(f"{best_params.l_ac:.6g}")
        self.entries["l_dc"].set(f"{best_params.l_dc:.6g}")
        self.status.set(f"Optimization done! Score: {score:.3f}")

        messagebox.showinfo(
            "Optimization complete",
            f"Optimal values found:\nL_ac = {best_params.l_ac:.6f} H\nL_dc = {best_params.l_dc:.6f} H\n\nForm entries have been updated.",
        )
        ResultsWindow(self.root, best_result)

    def _set_run_buttons_state(self, state):
        self.run_button.configure(state=state)
        self.sweep_button.configure(state=state)
        self.optimize_button.configure(state=state)