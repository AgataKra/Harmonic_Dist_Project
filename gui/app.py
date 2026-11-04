from pathlib import Path
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import traceback

from PIL import Image, ImageTk
HAS_PIL = True

from optimization import OptimizationRunner
from spice_simulation import SimulationParameters, SimulationRunner
from gui.results import ResultsWindow, SweepResultsWindow

# Define path to the assets directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_PATH = PROJECT_ROOT / "img" / "rectifier_diag.png"


class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("Harmonic distortion simulator")
        # Compact vertical bounds (~1.5x image height of 310px = ~465-490px total height)
        self.root.minsize(1470, 735)

        self.runner = SimulationRunner()
        self.optimizer = OptimizationRunner(self.runner)

        self.status = tk.StringVar(value="Ready")
        self.limit_v_drop_var = tk.BooleanVar(value=True)

        self.param_vars = {
            "v_phase_rms": tk.DoubleVar(value=230.0),
            "frequency": tk.DoubleVar(value=50.0),
            "r_source": tk.DoubleVar(value=0.2),
            "l_ac": tk.DoubleVar(value=0.005),
            "l_dc": tk.DoubleVar(value=0.02),
            "r_load": tk.DoubleVar(value=100.0),
            "c_load": tk.DoubleVar(value=0.001),
            "step_time": tk.DoubleVar(value=1e-6),
            "stop_time": tk.DoubleVar(value=0.2),
        }

        self._build_ui()

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root, padding=8)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Left Column: Parameter Form (sticky="w" centers it vertically on the left)
        form_frame = ttk.LabelFrame(main_frame, text="Simulation parameters", padding=10)
        form_frame.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Right Column: Diagram Image (no sticky centers it vertically and horizontally in its cell)
        if IMAGE_PATH.exists() and HAS_PIL:
            try:
                img = Image.open(IMAGE_PATH)
                img = img.resize((675, 465), Image.Resampling.LANCZOS)
                self.diagram_img = ImageTk.PhotoImage(img)

                diagram_label = ttk.Label(main_frame, image=self.diagram_img)
                diagram_label.grid(row=0, column=1, padx=(10, 0))
            except Exception as e:
                self._render_image_placeholder(main_frame, f"Failed to load image: {e}")
        elif IMAGE_PATH.exists() and not HAS_PIL:
            try:
                self.diagram_img = tk.PhotoImage(file=str(IMAGE_PATH))
                diagram_label = ttk.Label(main_frame, image=self.diagram_img)
                diagram_label.grid(row=0, column=1, padx=(10, 0))
            except Exception:
                self._render_image_placeholder(main_frame, "Pillow library missing (pip install pillow)")
        else:
            self._render_image_placeholder(
                main_frame,
                f"Schematic image not found.\nPlace 'rectifier_diag.png' in:\n{PROJECT_ROOT / 'img'}"
            )

        labels = [
            ("Phase voltage RMS [V]", "v_phase_rms"),
            ("Frequency [Hz]", "frequency"),
            ("Source resistance [Ohm]", "r_source"),
            ("AC-side inductance l_ac [H]", "l_ac"),
            ("DC-side inductance l_dc [H]", "l_dc"),
            ("Load resistance [Ohm]", "r_load"),
            ("Load capacitance [F]", "c_load"),
            ("Simulation maximum step [s]", "step_time"),
            ("Stop time [s]", "stop_time"),
        ]

        for row, (label_text, var_key) in enumerate(labels):
            ttk.Label(form_frame, text=label_text).grid(row=row, column=0, sticky="w", pady=2)
            entry = ttk.Entry(form_frame, textvariable=self.param_vars[var_key], width=18)
            entry.grid(row=row, column=1, sticky="e", pady=2, padx=(8, 0))

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Button(btn_frame, text="Run simulation", command=self._on_run_clicked).grid(row=0, column=0, padx=(0, 2))
        ttk.Button(btn_frame, text="Run sweep", command=self._on_sweep_clicked).grid(row=0, column=1, padx=2)
        ttk.Button(btn_frame, text="Optimize L", command=self._on_optimize_clicked).grid(row=0, column=2, padx=2)
        ttk.Button(btn_frame, text="Reset", command=self._reset_defaults).grid(row=0, column=3, padx=(2, 0))

        ttk.Checkbutton(
            form_frame,
            text="Limit L_ac + L_dc voltage drop <= 3%",
            variable=self.limit_v_drop_var,
        ).grid(row=len(labels) + 1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        status_bar = ttk.Label(main_frame, textvariable=self.status, relief="sunken", anchor="w", padding=4)
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    @staticmethod
    def _render_image_placeholder(parent, message: str):
        placeholder = ttk.LabelFrame(parent, text="Circuit Schematic", padding=12)
        placeholder.grid(row=0, column=1, padx=(10, 0))
        ttk.Label(placeholder, text=message, justify="center", foreground="gray").pack(expand=True, fill="both")

    def _get_parameters(self) -> SimulationParameters | None:
        try:
            params = SimulationParameters(
                v_phase_rms=self.param_vars["v_phase_rms"].get(),
                frequency=self.param_vars["frequency"].get(),
                r_source=self.param_vars["r_source"].get(),
                l_ac=self.param_vars["l_ac"].get(),
                l_dc=self.param_vars["l_dc"].get(),
                r_load=self.param_vars["r_load"].get(),
                c_load=self.param_vars["c_load"].get(),
                step_time=self.param_vars["step_time"].get(),
                stop_time=self.param_vars["stop_time"].get(),
            )
            params.validate()
            return params
        except Exception as err:
            messagebox.showerror("Invalid Input", str(err))
            return None

    def _reset_defaults(self):
        defaults = SimulationParameters()
        for key, var in self.param_vars.items():
            var.set(getattr(defaults, key))
        self.limit_v_drop_var.set(True)
        self.status.set("Reset to default values.")

    def _on_run_clicked(self):
        params = self._get_parameters()
        if params is None:
            return
        self.status.set("Simulation running...")
        threading.Thread(target=self._run_worker, args=(params,), daemon=True).start()

    def _run_worker(self, params):
        try:
            result = self.runner.run(params)
        except Exception as exc:
            err_msg = str(exc)
            details = traceback.format_exc()
            self.root.after(0, lambda e=err_msg, d=details: self._simulation_failed(e, d))
            return
        self.root.after(0, lambda: self._simulation_finished(result))

    def _simulation_finished(self, result):
        self.status.set("Simulation completed successfully.")
        ResultsWindow(self.root, result)

    def _on_sweep_clicked(self):
        params = self._get_parameters()
        if params is None:
            return
        values = [0.001, 0.005, 0.01, 0.02]
        self.status.set("Sweep running...")
        threading.Thread(
            target=self._sweep_worker,
            args=(params, "l_ac", "L_ac", values),
            daemon=True,
        ).start()

    def _sweep_worker(self, base_params, sweep_parameter, sweep_label, values):
        from dataclasses import dataclass, replace

        @dataclass
        class SweepCase:
            value: float
            label: str
            result: object

        results = []
        try:
            for index, value in enumerate(values, start=1):
                params = replace(base_params, **{sweep_parameter: value})
                result = self.runner.run(params)
                results.append(SweepCase(value=value, label=f"{sweep_label}={value:g}", result=result))
                self.root.after(0, lambda done=index, total=len(values): self.status.set(f"Sweep running {done}/{total}..."))
        except Exception as exc:
            err_msg = str(exc)
            details = traceback.format_exc()
            self.root.after(0, lambda e=err_msg, d=details: self._simulation_failed(e, d))
            return
        self.root.after(0, lambda: self._sweep_finished(sweep_label, results))

    def _sweep_finished(self, sweep_label, results):
        self.status.set("Sweep completed successfully.")
        SweepResultsWindow(self.root, sweep_label, results)

    def _on_optimize_clicked(self):
        params = self._get_parameters()
        if params is None:
            return
        limit_drop = self.limit_v_drop_var.get()
        self.status.set("Optimization running...")
        threading.Thread(
            target=self._optimization_worker,
            args=(params, limit_drop),
            daemon=True,
        ).start()

    def _optimization_worker(self, params, limit_drop):
        try:
            def on_progress(step, l_ac, l_dc):
                self.root.after(
                    0,
                    lambda s=step, ac=l_ac, dc=l_dc: self.status.set(
                        f"Optimization step {s}: L_ac={ac * 1e3:.3f}mH, L_dc={dc * 1e3:.3f}mH"
                    ),
                )

            best_params, best_result, score = self.optimizer.optimize(
                params,
                limit_v_drop=limit_drop,
                progress_callback=on_progress,
            )
        except Exception as exc:
            err_msg = str(exc)
            details = traceback.format_exc()
            self.root.after(0, lambda e=err_msg, d=details: self._simulation_failed(e, d))
            return

        self.root.after(0, lambda: self._optimization_finished(best_params, best_result, score))

    def _optimization_finished(self, best_params, best_result, score):
        self.param_vars["l_ac"].set(round(best_params.l_ac, 6))
        self.param_vars["l_dc"].set(round(best_params.l_dc, 6))
        self.status.set(f"Optimization done! Score: {score:.3f}")
        ResultsWindow(self.root, best_result)

    def _simulation_failed(self, exc_str, details):
        self.status.set("Simulation failed.")
        messagebox.showerror("Simulation Failed", f"{exc_str}\n\nDetails:\n{details}")


App = Application