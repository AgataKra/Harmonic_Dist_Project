import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.figure import Figure

from gui.plotting import place_figure


class ResultsWindow:
    def __init__(self, parent, result):
        self.result = result
        self.window = tk.Toplevel(parent)
        self.window.title("Simulation results")
        self.window.minsize(1050, 780)
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self.window)
        notebook.grid(row=0, column=0, sticky="nsew")

        self._add_input_waveforms(notebook)
        self._add_output_waveforms(notebook)
        self._add_thd_table(notebook)
        self._add_harmonics_tab(notebook)

        if hasattr(self.result, "opt_history") and self.result.opt_history:
            self._add_optimization_progress_tab(notebook)
            self._add_iteration_waveforms_tab(notebook)

    def _add_input_waveforms(self, notebook):
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text="Input waveforms")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        controls = ttk.LabelFrame(frame, text="Displayed phases", padding=8)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        phase_vars = {name: tk.BooleanVar(value=True) for name in self.result.input_voltages}
        for column, (name, var) in enumerate(phase_vars.items()):
            ttk.Checkbutton(
                controls,
                text=name,
                variable=var,
                command=lambda: redraw_phase_selection(),
            ).grid(row=0, column=column, sticky="w", padx=(0, 12))

        plot_frame = ttk.Frame(frame)
        plot_frame.grid(row=1, column=0, sticky="nsew")
        fig = Figure(figsize=(8, 6), dpi=100)
        voltage_axis = fig.add_subplot(211)
        current_axis = fig.add_subplot(212, sharex=voltage_axis)
        time_ms = self.result.time * 1000.0
        voltage_lines = {}
        current_lines = {}

        for name, values in self.result.input_voltages.items():
            line = voltage_axis.plot(time_ms, values, label=name)[0]
            voltage_lines[name] = line
        for name, values in self.result.input_currents.items():
            line = current_axis.plot(time_ms, values, label=name)[0]
            current_lines[name] = line

        voltage_axis.set_xlim(time_ms[0], time_ms[-1])

        voltage_axis.set_title("Input phase voltages")
        voltage_axis.set_ylabel("Voltage [V]")
        voltage_axis.grid(True)
        voltage_axis.legend()
        current_axis.set_title("Input source currents")
        current_axis.set_xlabel("Time [ms]")
        current_axis.set_ylabel("Current [A]")
        current_axis.grid(True)
        current_axis.legend()
        fig.tight_layout()
        interactive_plot = place_figure(plot_frame, fig)

        def redraw_phase_selection():
            if not any(var.get() for var in phase_vars.values()):
                next(iter(phase_vars.values())).set(True)
            for name, var in phase_vars.items():
                voltage_lines[name].set_visible(var.get())
                current_lines[name].set_visible(var.get())
            voltage_axis.legend()
            current_axis.legend()
            interactive_plot.canvas.draw_idle()

        redraw_phase_selection()

    def _add_output_waveforms(self, notebook):
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text="Output waveforms")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        fig = Figure(figsize=(8, 6), dpi=100)
        voltage_axis = fig.add_subplot(211)
        current_axis = fig.add_subplot(212, sharex=voltage_axis)
        time_ms = self.result.time * 1000.0

        voltage_axis.plot(time_ms, self.result.output_voltage, label="Load voltage")
        current_axis.plot(time_ms, self.result.output_current, label="Load current")

        voltage_axis.set_xlim(time_ms[0], time_ms[-1])

        voltage_axis.set_title("DC output voltage on load")
        voltage_axis.set_ylabel("Voltage [V]")
        voltage_axis.grid(True)
        voltage_axis.legend()
        current_axis.set_title("DC output current through load")
        current_axis.set_xlabel("Time [ms]")
        current_axis.set_ylabel("Current [A]")
        current_axis.grid(True)
        current_axis.legend()
        fig.tight_layout()
        place_figure(frame, fig)

    def _add_thd_table(self, notebook):
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="THD / Ripple / Voltage drop metrics")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        tree = ttk.Treeview(
            frame,
            columns=("signal", "fundamental", "thd", "drop_v", "drop_percent"),
            show="headings",
            height=14,
        )
        tree.heading("signal", text="Signal / Component")
        tree.heading("fundamental", text="Fundamental RMS / DC Avg")
        tree.heading("thd", text="THD / Ripple [%]")
        tree.heading("drop_v", text="Voltage Drop [V]")
        tree.heading("drop_percent", text="Drop [% of V_dc,ideal]")

        tree.column("signal", width=220, anchor="w")
        tree.column("fundamental", width=160, anchor="e")
        tree.column("thd", width=120, anchor="e")
        tree.column("drop_v", width=130, anchor="e")
        tree.column("drop_percent", width=160, anchor="e")
        tree.grid(row=0, column=0, sticky="nsew")

        for name, spectrum in self.result.harmonics.items():
            metric_val = self.result.thd[name]
            if "Output" in name:
                fund_val = abs(
                    float(np.mean(self.result.output_voltage if "voltage" in name else self.result.output_current)))
            else:
                fund_val = spectrum.fundamental_rms
            tree.insert("", "end", values=(name, f"{fund_val:.3f}", f"{metric_val:.3f}", "-", "-"))

        tree.insert("", "end", values=("--- Voltage Drop Metrics ---", "", "", "", ""))
        tree.insert("", "end",
                    values=("Ideal DC Output Voltage (V_dc,ideal)", f"{self.result.v_dc_ideal:.3f} V", "-", "-",
                            "0.000 %"))
        tree.insert("", "end",
                    values=("Actual DC Output Voltage (V_dc,actual)", f"{self.result.v_dc_actual:.3f} V", "-",
                            f"{self.result.v_dc_ideal - self.result.v_dc_actual:.3f} V",
                            f"{100.0 * (self.result.v_dc_ideal - self.result.v_dc_actual) / self.result.v_dc_ideal:.3f} %"))
        tree.insert("", "end",
                    values=("AC Inductor Drop (L_ac commutation)", "-", "-", f"{self.result.v_drop_lac_v:.3f} V",
                            f"{self.result.v_drop_lac_percent:.3f} %"))
        tree.insert("", "end", values=("DC Inductor Drop (L_dc choke)", "-", "-", f"{self.result.v_drop_ldc_v:.3f} V",
                                       f"{self.result.v_drop_ldc_percent:.3f} %"))

    def _add_harmonics_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text="Harmonics")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=0)

        signal_names = list(self.result.harmonics.keys())
        selected_signal = tk.StringVar(value=signal_names[0])
        selector = ttk.Combobox(frame, textvariable=selected_signal, values=signal_names, state="readonly")
        selector.grid(row=0, column=0, sticky="w", pady=(0, 8))

        plot_frame = ttk.Frame(frame)
        plot_frame.grid(row=1, column=0, sticky="nsew")
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        fig = Figure(figsize=(8, 5), dpi=100)
        axis = fig.add_subplot(111)
        interactive_plot = place_figure(plot_frame, fig)

        table_frame = ttk.LabelFrame(frame, text="Numerical harmonic levels", padding=8)
        table_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        table_frame.columnconfigure(0, weight=1)
        harmonic_table = ttk.Treeview(
            table_frame,
            columns=("order", "rms", "percent"),
            show="headings",
            height=6,
        )
        harmonic_table.heading("order", text="Harmonic order")
        harmonic_table.heading("rms", text="RMS level [V or A]")
        harmonic_table.heading("percent", text="% of fundamental")
        harmonic_table.column("order", width=130, anchor="e")
        harmonic_table.column("rms", width=180, anchor="e")
        harmonic_table.column("percent", width=160, anchor="e")
        harmonic_table.grid(row=0, column=0, sticky="ew")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=harmonic_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        harmonic_table.configure(yscrollcommand=scrollbar.set)

        def redraw(*_):
            spectrum = self.result.harmonics[selected_signal.get()]

            if spectrum.fundamental_rms > 1e-12:
                percent_magnitudes = 100.0 * (spectrum.magnitudes / spectrum.fundamental_rms)
            else:
                percent_magnitudes = np.zeros_like(spectrum.magnitudes)

            axis.clear()
            axis.bar(spectrum.orders, percent_magnitudes)
            axis.set_title(f"Harmonic levels (% of fundamental): {selected_signal.get()}")
            axis.set_xlabel("Harmonic order")
            axis.set_ylabel("Level [% of Fundamental]")
            axis.set_xticks(spectrum.orders[::2])
            axis.grid(True, axis="y")
            fig.tight_layout()
            interactive_plot.capture_default_view()
            interactive_plot.canvas.draw_idle()
            self._fill_single_harmonic_table(harmonic_table, spectrum)

        selector.bind("<<ComboboxSelected>>", redraw)
        redraw()

    @staticmethod
    def _fill_single_harmonic_table(tree, spectrum):
        tree.delete(*tree.get_children())
        for order, magnitude in zip(spectrum.orders, spectrum.magnitudes):
            percent = ResultsWindow._percentage_of_fundamental(magnitude, spectrum.fundamental_rms)
            tree.insert("", "end", values=(int(order), f"{magnitude:.3f}", f"{percent:.3f}"))

    @staticmethod
    def _percentage_of_fundamental(magnitude, fundamental_rms):
        if abs(fundamental_rms) <= 1e-12:
            return 0.0
        return 100.0 * magnitude / fundamental_rms

    def _add_optimization_progress_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text="Opt. Progress")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        history = self.result.opt_history
        iterations = [step.iteration for step in history]
        thd_list = [step.thd_i_in for step in history]
        ripple_list = [step.ripple_v_out for step in history]
        l_ac_list = [step.l_ac * 1000.0 for step in history]
        l_dc_list = [step.l_dc * 1000.0 for step in history]
        drop_lac_list = [step.v_drop_lac_percent for step in history]
        drop_ldc_list = [step.v_drop_ldc_percent for step in history]

        fig = Figure(figsize=(8, 7), dpi=100)

        ax1 = fig.add_subplot(311)
        ax2 = ax1.twinx()
        p1 = ax1.plot(iterations, thd_list, "b-o", label="Input I Phase A THD [%]")[0]
        p2 = ax2.plot(iterations, ripple_list, "r-s", label="Output U Ripple [%]")[0]
        ax1.set_ylabel("Input Current THD [%]", color="b")
        ax2.set_ylabel("Output Voltage Ripple [%]", color="r")
        ax1.tick_params(axis="y", labelcolor="b")
        ax2.tick_params(axis="y", labelcolor="r")
        ax1.set_title("Harmonic & Ripple Metrics over Iterations")
        ax1.grid(True)
        ax1.set_xlim(iterations[0], iterations[-1])
        ax1.legend([p1, p2], [p1.get_label(), p2.get_label()], loc="upper right")

        ax_drop = fig.add_subplot(312, sharex=ax1)
        ax_drop.plot(iterations, drop_lac_list, "c-D", label="L_ac Voltage Drop [% of V_dc,ideal]")
        ax_drop.plot(iterations, drop_ldc_list, "y-p", label="L_dc Voltage Drop [% of V_dc,ideal]")
        ax_drop.set_ylabel("Voltage Drop [%]")
        ax_drop.set_title("Inductor Voltage Drop Progression (% of V_dc,ideal)")
        ax_drop.grid(True)
        ax_drop.legend(loc="upper right")

        ax_l = fig.add_subplot(313, sharex=ax1)
        ax_l.plot(iterations, l_ac_list, "g-^", label="AC Inductance L_ac [mH]")
        ax_l.plot(iterations, l_dc_list, "m-d", label="DC Inductance L_dc [mH]")
        ax_l.set_xlabel("Optimization Iteration Step")
        ax_l.set_ylabel("Inductance [mH]")
        ax_l.set_title("Inductance Values Trajectory")
        ax_l.grid(True)
        ax_l.legend(loc="upper right")

        fig.tight_layout()
        place_figure(frame, fig)

    def _add_iteration_waveforms_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text="Iteration Waveforms")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        history = self.result.opt_history

        # 1. View Mode Radio Buttons (Settled vs. Beginning)
        view_mode_frame = ttk.LabelFrame(frame, text="Time Window Selection", padding=8)
        view_mode_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        view_mode_var = tk.StringVar(value="settled")
        ttk.Radiobutton(
            view_mode_frame,
            text="Settled Waveforms (Steady-state: 200 ms - 260 ms)",
            value="settled",
            variable=view_mode_var,
            command=lambda: redraw(),
        ).grid(row=0, column=0, padx=(0, 16), sticky="w")

        ttk.Radiobutton(
            view_mode_frame,
            text="Beginning Waveforms (Transient startup: 0 ms - 120 ms)",
            value="beginning",
            variable=view_mode_var,
            command=lambda: redraw(),
        ).grid(row=0, column=1, sticky="w")

        # 2. Step Comparison Selection Controls
        controls = ttk.LabelFrame(frame, text="Select Iteration Steps to Compare", padding=8)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        default_selected = {1, len(history), max(1, len(history) // 2)}
        step_vars = {}

        plot_frame = ttk.Frame(frame)
        plot_frame.grid(row=2, column=0, sticky="nsew")

        fig = Figure(figsize=(8, 6), dpi=100)
        ax_i_in = fig.add_subplot(311)
        ax_v_out = fig.add_subplot(312, sharex=ax_i_in)
        ax_i_out = fig.add_subplot(313, sharex=ax_i_in)
        interactive_plot = place_figure(plot_frame, fig)

        def redraw():
            ax_i_in.clear()
            ax_v_out.clear()
            ax_i_out.clear()

            selected = [step for step in history if step_vars[step.iteration].get()]
            if not selected:
                step_vars[history[-1].iteration].set(True)
                selected = [history[-1]]

            is_settled = (view_mode_var.get() == "settled")

            for step in selected:
                if is_settled:
                    t_ms = step.time * 1000.0
                    i_in = step.i_phase_a
                    v_out = step.v_out
                    i_out = step.i_out
                else:
                    # Filter for beginning transient window (0 ms to 120 ms)
                    t_full_ms = step.full_time * 1000.0
                    mask = t_full_ms <= 120.0
                    if not np.any(mask):
                        mask = np.ones_like(t_full_ms, dtype=bool)
                    t_ms = t_full_ms[mask]
                    i_in = step.full_i_phase_a[mask]
                    v_out = step.full_v_out[mask]
                    i_out = step.full_i_out[mask]

                label = f"Iter {step.iteration} (Lac={step.l_ac * 1e3:.3f}mH, Ldc={step.l_dc * 1e3:.3f}mH)"
                ax_i_in.plot(t_ms, i_in, label=label)
                ax_v_out.plot(t_ms, v_out, label=label)
                ax_i_out.plot(t_ms, i_out, label=label)

            # Strict zero horizontal margin on time axis
            ref_step = selected[0]
            if is_settled:
                ref_t = ref_step.time * 1000.0
            else:
                ref_t_mask = (ref_step.full_time * 1000.0) <= 60.0
                ref_t = (ref_step.full_time * 1000.0)[ref_t_mask] if np.any(ref_t_mask) else ref_step.full_time * 1000.0

            ax_i_in.set_xlim(ref_t[0], ref_t[-1])

            mode_title = "Settled Steady-State" if is_settled else "Transient Startup (Beginning)"
            ax_i_in.set_title(f"Input Current Phase A [A] — ({mode_title})")
            ax_i_in.grid(True)
            ax_i_in.legend(fontsize=8, loc="upper right")

            ax_v_out.set_title(f"Output Voltage [V] — ({mode_title})")
            ax_v_out.grid(True)

            ax_i_out.set_title(f"Output Current [A] — ({mode_title})")
            ax_i_out.set_xlabel("Time [ms]")
            ax_i_out.grid(True)

            fig.tight_layout()
            interactive_plot.capture_default_view()
            interactive_plot.canvas.draw_idle()

        max_cols_per_row = 10
        for idx, step in enumerate(history):
            row_num = idx // max_cols_per_row
            col_num = idx % max_cols_per_row

            var = tk.BooleanVar(value=step.iteration in default_selected)
            step_vars[step.iteration] = var
            cb = ttk.Checkbutton(
                controls,
                text=f"Step {step.iteration}",
                variable=var,
                command=redraw,
            )
            cb.grid(row=row_num, column=col_num, sticky="w", padx=4, pady=2)

        redraw()


class SweepResultsWindow(ResultsWindow):
    def __init__(self, parent, sweep_label, sweep_cases):
        self.sweep_label = sweep_label
        self.sweep_cases = sweep_cases
        self.window = tk.Toplevel(parent)
        self.window.title("Sweep simulation results")
        self.window.minsize(1050, 740)
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self.window)
        notebook.grid(row=0, column=0, sticky="nsew")

        self._add_sweep_input_waveforms(notebook)
        self._add_sweep_output_waveforms(notebook)
        self._add_sweep_thd_table(notebook)
        self._add_sweep_harmonics_tab(notebook)

    def _add_sweep_input_waveforms(self, notebook):
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text="Input waveforms")
        fig = Figure(figsize=(8, 6), dpi=100)
        voltage_axis = fig.add_subplot(211)
        current_axis = fig.add_subplot(212, sharex=voltage_axis)
        line_groups = {}

        t_start = self.sweep_cases[0].result.time[0] * 1000.0
        t_end = self.sweep_cases[0].result.time[-1] * 1000.0

        for case in self.sweep_cases:
            time_ms = case.result.time * 1000.0
            voltage_line = voltage_axis.plot(
                time_ms,
                case.result.input_voltages["Phase A"],
                label=case.label,
            )[0]
            current_line = current_axis.plot(
                time_ms,
                case.result.input_currents["Phase A"],
                label=case.label,
            )[0]
            line_groups[case.label] = (voltage_line, current_line)

        voltage_axis.set_xlim(t_start, t_end)
        voltage_axis.set_title("Input phase A voltage sweep comparison")
        voltage_axis.set_ylabel("Voltage [V]")
        voltage_axis.grid(True)
        voltage_axis.legend()
        current_axis.set_title("Input phase A current sweep comparison")
        current_axis.set_xlabel("Time [ms]")
        current_axis.set_ylabel("Current [A]")
        current_axis.grid(True)
        current_axis.legend()
        fig.tight_layout()
        self._place_sweep_plot(frame, fig, line_groups, [voltage_axis, current_axis])

    def _add_sweep_output_waveforms(self, notebook):
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text="Output waveforms")
        fig = Figure(figsize=(8, 6), dpi=100)
        voltage_axis = fig.add_subplot(211)
        current_axis = fig.add_subplot(212, sharex=voltage_axis)
        line_groups = {}

        t_start = self.sweep_cases[0].result.time[0] * 1000.0
        t_end = self.sweep_cases[0].result.time[-1] * 1000.0

        for case in self.sweep_cases:
            time_ms = case.result.time * 1000.0
            voltage_line = voltage_axis.plot(time_ms, case.result.output_voltage, label=case.label)[0]
            current_line = current_axis.plot(time_ms, case.result.output_current, label=case.label)[0]
            line_groups[case.label] = (voltage_line, current_line)

        voltage_axis.set_xlim(t_start, t_end)
        voltage_axis.set_title("Load voltage sweep comparison")
        voltage_axis.set_ylabel("Voltage [V]")
        voltage_axis.grid(True)
        voltage_axis.legend()
        current_axis.set_title("Load current sweep comparison")
        current_axis.set_xlabel("Time [ms]")
        current_axis.set_ylabel("Current [A]")
        current_axis.grid(True)
        current_axis.legend()
        fig.tight_layout()
        self._place_sweep_plot(frame, fig, line_groups, [voltage_axis, current_axis])

    def _add_sweep_thd_table(self, notebook):
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="THD / Ripple values")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(
            frame,
            columns=("case", "input_voltage", "input_current", "output_voltage", "output_current"),
            show="headings",
            height=12,
        )
        tree.heading("case", text=self.sweep_label)
        tree.heading("input_voltage", text="Input U Ph A THD [%]")
        tree.heading("input_current", text="Input I Ph A THD [%]")
        tree.heading("output_voltage", text="Output U Ripple [%]")
        tree.heading("output_current", text="Output I Ripple [%]")
        tree.column("case", width=240, anchor="w")
        for column in ("input_voltage", "input_current", "output_voltage", "output_current"):
            tree.column(column, width=170, anchor="e")
        tree.grid(row=0, column=0, sticky="nsew")

        for case in self.sweep_cases:
            tree.insert(
                "",
                "end",
                values=(
                    case.label,
                    f"{case.result.thd['Input voltage Phase A']:.3f}",
                    f"{case.result.thd['Input current Phase A']:.3f}",
                    f"{case.result.thd['Output voltage']:.3f}",
                    f"{case.result.thd['Output current']:.3f}",
                ),
            )

    def _add_sweep_harmonics_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text="Harmonics")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(3, weight=0)

        controls = ttk.Frame(frame)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(controls, text="Signal").grid(row=0, column=0, sticky="w")
        signal_names = [
            "Input voltage Phase A",
            "Input current Phase A",
            "Output voltage",
            "Output current",
        ]
        selected_signal = tk.StringVar(value=signal_names[0])
        selector = ttk.Combobox(controls, textvariable=selected_signal, values=signal_names, state="readonly", width=28)
        selector.grid(row=0, column=1, sticky="w", padx=(8, 0))

        plot_frame = ttk.Frame(frame)
        plot_frame.grid(row=1, column=0, sticky="nsew")
        fig = Figure(figsize=(8, 5), dpi=100)
        axis = fig.add_subplot(111)
        interactive_plot = place_figure(plot_frame, fig)
        case_vars = {case.label: tk.BooleanVar(value=True) for case in self.sweep_cases}

        case_controls = ttk.LabelFrame(frame, text="Displayed simulations", padding=8)
        case_controls.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        table_frame = ttk.LabelFrame(frame, text="Numerical harmonic levels", padding=8)
        table_frame.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        table_frame.columnconfigure(0, weight=1)
        columns = ["order"]
        for index, _case in enumerate(self.sweep_cases):
            columns.extend((f"case_{index}_rms", f"case_{index}_percent"))
        harmonic_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=6)
        harmonic_table.heading("order", text="Harmonic order")
        harmonic_table.column("order", width=120, anchor="e")
        for index, case in enumerate(self.sweep_cases):
            rms_column = f"case_{index}_rms"
            percent_column = f"case_{index}_percent"
            harmonic_table.heading(rms_column, text=f"{case.label} RMS")
            harmonic_table.heading(percent_column, text=f"{case.label} [%]")
            harmonic_table.column(rms_column, width=150, anchor="e")
            harmonic_table.column(percent_column, width=130, anchor="e")
        harmonic_table.grid(row=0, column=0, sticky="ew")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=harmonic_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        harmonic_table.configure(yscrollcommand=scrollbar.set)

        def redraw():
            if not any(var.get() for var in case_vars.values()):
                next(iter(case_vars.values())).set(True)
            axis.clear()
            signal = selected_signal.get()
            for case in self.sweep_cases:
                if not case_vars[case.label].get():
                    continue
                spectrum = case.result.harmonics[signal]

                if spectrum.fundamental_rms > 1e-12:
                    percent_magnitudes = 100.0 * (spectrum.magnitudes / spectrum.fundamental_rms)
                else:
                    percent_magnitudes = np.zeros_like(spectrum.magnitudes)

                axis.plot(spectrum.orders, percent_magnitudes, marker="o", linewidth=1.5, label=case.label)

            axis.set_title(f"Harmonic levels (% of fundamental): {signal}")
            axis.set_xlabel("Harmonic order")
            axis.set_ylabel("Level [% of Fundamental]")
            axis.set_xticks(self.sweep_cases[0].result.harmonics[signal].orders[::2])
            axis.grid(True)
            axis.legend()
            fig.tight_layout()
            interactive_plot.capture_default_view()
            interactive_plot.canvas.draw_idle()
            self._fill_sweep_harmonic_table(harmonic_table, signal)

        for column, (label, var) in enumerate(case_vars.items()):
            ttk.Checkbutton(
                case_controls,
                text=label,
                variable=var,
                command=redraw,
            ).grid(row=0, column=column, sticky="w", padx=(0, 12))

        selector.bind("<<ComboboxSelected>>", lambda _event: redraw())
        redraw()

    def _fill_sweep_harmonic_table(self, tree, signal):
        tree.delete(*tree.get_children())
        orders = self.sweep_cases[0].result.harmonics[signal].orders
        for index, order in enumerate(orders):
            row = [int(order)]
            for case in self.sweep_cases:
                spectrum = case.result.harmonics[signal]
                magnitude = spectrum.magnitudes[index]
                percent = self._percentage_of_fundamental(magnitude, spectrum.fundamental_rms)
                row.extend((f"{magnitude:.3f}", f"{percent:.3f}"))
            tree.insert("", "end", values=row)

    def _place_sweep_plot(self, frame, fig, line_groups, axes):
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        controls = ttk.LabelFrame(frame, text="Displayed simulations", padding=8)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        plot_frame = ttk.Frame(frame)
        plot_frame.grid(row=1, column=0, sticky="nsew")
        interactive_plot = place_figure(plot_frame, fig)

        case_vars = {label: tk.BooleanVar(value=True) for label in line_groups}

        def redraw():
            if not any(var.get() for var in case_vars.values()):
                next(iter(case_vars.values())).set(True)
            for label, lines in line_groups.items():
                visible = case_vars[label].get()
                for line in lines:
                    line.set_visible(visible)
            for axis in axes:
                axis.legend()
            interactive_plot.canvas.draw_idle()

        for column, (label, var) in enumerate(case_vars.items()):
            ttk.Checkbutton(
                controls,
                text=label,
                variable=var,
                command=redraw,
            ).grid(row=0, column=column, sticky="w", padx=(0, 12))

        redraw()