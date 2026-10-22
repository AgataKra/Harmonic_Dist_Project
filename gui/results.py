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
        self.window.minsize(1050, 750)
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
        notebook.add(frame, text="THD / Ripple metrics")
        frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=("signal", "fundamental", "thd"), show="headings", height=12)
        tree.heading("signal", text="Signal")
        tree.heading("fundamental", text="Fundamental RMS / DC Avg")
        tree.heading("thd", text="THD / Ripple [%]")
        tree.column("signal", width=260, anchor="w")
        tree.column("fundamental", width=180, anchor="e")
        tree.column("thd", width=120, anchor="e")
        tree.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)

        for name, spectrum in self.result.harmonics.items():
            metric_val = self.result.thd[name]
            if "Output" in name:
                fund_val = abs(
                    float(np.mean(self.result.output_voltage if "voltage" in name else self.result.output_current)))
            else:
                fund_val = spectrum.fundamental_rms
            tree.insert("", "end", values=(name, f"{fund_val:.4g}", f"{metric_val:.3f}"))

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
            axis.clear()
            axis.bar(spectrum.orders, spectrum.magnitudes)
            axis.set_title(f"Harmonic levels: {selected_signal.get()}")
            axis.set_xlabel("Harmonic order")
            axis.set_ylabel("RMS level [V or A]")
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
            tree.insert("", "end", values=(int(order), f"{magnitude:.6g}", f"{percent:.3f}"))

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
        l_ac_list = [step.l_ac * 1000.0 for step in history]  # Convert H to mH
        l_dc_list = [step.l_dc * 1000.0 for step in history]  # Convert H to mH

        fig = Figure(figsize=(8, 6), dpi=100)

        # Subplot 1: THD & Ripple
        ax1 = fig.add_subplot(211)
        ax2 = ax1.twinx()
        p1 = ax1.plot(iterations, thd_list, "b-o", label="Input I Phase A THD [%]")[0]
        p2 = ax2.plot(iterations, ripple_list, "r-s", label="Output U Ripple [%]")[0]
        ax1.set_ylabel("Input Current THD [%]", color="b")
        ax2.set_ylabel("Output Voltage Ripple [%]", color="r")
        ax1.tick_params(axis="y", labelcolor="b")
        ax2.tick_params(axis="y", labelcolor="r")
        ax1.set_title("Harmonic & Ripple Metrics over Optimization Iterations")
        ax1.grid(True)
        ax1.legend([p1, p2], [p1.get_label(), p2.get_label()], loc="upper right")

        # Subplot 2: Inductance Values Progression
        ax_l = fig.add_subplot(212, sharex=ax1)
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
        frame.rowconfigure(1, weight=1)

        history = self.result.opt_history

        # Selection Control Panel
        controls = ttk.LabelFrame(frame, text="Select Iteration Steps to Compare", padding=8)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        default_selected = {1, len(history), max(1, len(history) // 2)}
        step_vars = {}

        plot_frame = ttk.Frame(frame)
        plot_frame.grid(row=1, column=0, sticky="nsew")

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

            for step in selected:
                time_ms = step.time * 1000.0
                label = f"Iter {step.iteration} (Lac={step.l_ac * 1e3:.1f}mH, Ldc={step.l_dc * 1e3:.1f}mH)"
                ax_i_in.plot(time_ms, step.i_phase_a, label=label)
                ax_v_out.plot(time_ms, step.v_out, label=label)
                ax_i_out.plot(time_ms, step.i_out, label=label)

            ax_i_in.set_title("Input Current Phase A [A]")
            ax_i_in.grid(True)
            ax_i_in.legend(fontsize=8, loc="upper right")

            ax_v_out.set_title("Output Voltage [V]")
            ax_v_out.grid(True)

            ax_i_out.set_title("Output Current [A]")
            ax_i_out.set_xlabel("Time [ms]")
            ax_i_out.grid(True)

            fig.tight_layout()
            interactive_plot.capture_default_view()
            interactive_plot.canvas.draw_idle()

        # Multi-row wrapping grid layout for iteration checkboxes
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

        for case in self.sweep_cases:
            time_ms = case.result.time * 1000.0
            voltage_line = voltage_axis.plot