import tkinter as tk
from tkinter import ttk

from matplotlib.figure import Figure

from gui.plotting import place_figure


class ResultsWindow:
    def __init__(self, parent, result):
        self.result = result
        self.window = tk.Toplevel(parent)
        self.window.title("Simulation results")
        self.window.minsize(1000, 720)
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self.window)
        notebook.grid(row=0, column=0, sticky="nsew")

        self._add_input_waveforms(notebook)
        self._add_output_waveforms(notebook)
        self._add_thd_table(notebook)
        self._add_harmonics_tab(notebook)

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
        notebook.add(frame, text="THD values")
        frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=("signal", "fundamental", "thd"), show="headings", height=12)
        tree.heading("signal", text="Signal")
        tree.heading("fundamental", text="Fundamental RMS")
        tree.heading("thd", text="THD [%]")
        tree.column("signal", width=260, anchor="w")
        tree.column("fundamental", width=180, anchor="e")
        tree.column("thd", width=120, anchor="e")
        tree.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)

        for name, spectrum in self.result.harmonics.items():
            tree.insert("", "end", values=(name, f"{spectrum.fundamental_rms:.4g}", f"{spectrum.thd_percent:.3f}"))

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

        for case in self.sweep_cases:
            time_ms = case.result.time * 1000.0
            voltage_line = voltage_axis.plot(time_ms, case.result.output_voltage, label=case.label)[0]
            current_line = current_axis.plot(time_ms, case.result.output_current, label=case.label)[0]
            line_groups[case.label] = (voltage_line, current_line)

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
        notebook.add(frame, text="THD values")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(
            frame,
            columns=("case", "input_voltage", "input_current", "output_voltage", "output_current"),
            show="headings",
            height=12,
        )
        tree.heading("case", text=self.sweep_label)
        tree.heading("input_voltage", text="Input U Phase A THD [%]")
        tree.heading("input_current", text="Input I Phase A THD [%]")
        tree.heading("output_voltage", text="Output U THD [%]")
        tree.heading("output_current", text="Output I THD [%]")
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
                axis.plot(spectrum.orders, spectrum.magnitudes, marker="o", linewidth=1.5, label=case.label)
            axis.set_title(f"Harmonic levels: {signal}")
            axis.set_xlabel("Harmonic order")
            axis.set_ylabel("RMS level [V or A]")
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
                row.extend((f"{magnitude:.6g}", f"{percent:.3f}"))
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
