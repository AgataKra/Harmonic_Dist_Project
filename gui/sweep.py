import tkinter as tk
from tkinter import messagebox, ttk


class SweepCase:
    def __init__(self, value, label, result):
        self.value = value
        self.label = label
        self.result = result


class SweepDialog:
    SWEEP_PARAMETERS = {
        "AC choke inductance l_ac [H]": "l_ac",
        "DC choke inductance l_dc [H]": "l_dc",
        "Load resistance r_load [Ohm]": "r_load",
        "Load capacitance c_load [F]": "c_load",
        "Source resistance r_source [Ohm]": "r_source",
    }

    def __init__(self, parent, base_params, start_callback):
        self.base_params = base_params
        self.start_callback = start_callback
        self.window = tk.Toplevel(parent)
        self.window.title("Sweep simulation")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)
        self.parameter_label = tk.StringVar(value=next(iter(self.SWEEP_PARAMETERS)))
        self.values_text = tk.StringVar(value="0.002, 0.005, 0.01")
        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.window, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Sweep parameter").grid(row=0, column=0, sticky="w", pady=4)
        selector = ttk.Combobox(
            frame,
            textvariable=self.parameter_label,
            values=list(self.SWEEP_PARAMETERS),
            state="readonly",
            width=34,
        )
        selector.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)
        selector.bind("<<ComboboxSelected>>", self._load_default_values)

        ttk.Label(frame, text="Values").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, width=38, textvariable=self.values_text).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        ttk.Label(frame, text="Enter 3 to 5 positive numeric values separated by commas.").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, sticky="ew")
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        ttk.Button(buttons, text="Start sweep", command=self._start).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(buttons, text="Cancel", command=self.window.destroy).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _load_default_values(self, _event=None):
        parameter = self.SWEEP_PARAMETERS[self.parameter_label.get()]
        base_value = getattr(self.base_params, parameter)
        values = [base_value * factor for factor in (0.5, 1.0, 2.0)]
        self.values_text.set(", ".join(f"{value:g}" for value in values))

    def _start(self):
        try:
            values = self._parse_values()
        except ValueError as exc:
            messagebox.showerror("Invalid sweep values", str(exc), parent=self.window)
            return
        label = self.parameter_label.get()
        parameter = self.SWEEP_PARAMETERS[label]
        self.window.destroy()
        self.start_callback(self.base_params, parameter, label, values)

    def _parse_values(self):
        raw_values = [value.strip() for value in self.values_text.get().replace(";", ",").split(",")]
        values = []
        for raw_value in raw_values:
            if not raw_value:
                continue
            try:
                value = float(raw_value)
            except ValueError as exc:
                raise ValueError(f"'{raw_value}' is not a valid number.") from exc
            if value <= 0:
                raise ValueError("Sweep values must be greater than zero.")
            values.append(value)
        if not 3 <= len(values) <= 5:
            raise ValueError("Enter between 3 and 5 values.")
        return values
