import tkinter as tk
from tkinter import ttk
from spice_simulation import SimulationRunner, SimulationParameters


class App:
    def __init__(self, root):
        self.root = root
        self.init_window()
        # Used to send simulation parameters from here to spice_simulation
        self.default_params = SimulationParameters()
        self.params = SimulationParameters()
        self.runner = SimulationRunner()
        # Default values for entries
        self.v_amp_val = tk.StringVar(value=str(self.default_params.v_amp))
        self.freq_val = tk.StringVar(value=str(self.default_params.freq))
        self.r_in_val = tk.StringVar(value=str(self.default_params.r_in))
        self.l_in_val = tk.StringVar(value=str(self.default_params.l_in))
        self.l_choke_val = tk.StringVar(value=str(self.default_params.l_choke))
        self.r_out_val = tk.StringVar(value=str(self.default_params.r_out))
        self.build_ui()

    def init_window(self):
        self.root.title("Harmonic distortion simulator")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width / 2)
        window_height = int(screen_height / 2)
        center_x = int((screen_width / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.resizable(False, False)

        for r in range(7):
            self.root.rowconfigure(r, weight=1)
        for c in range(3):
            self.root.columnconfigure(c, weight=1 if c < 2 else 6)

    def build_ui(self):
        ttk.Label(self.root, text="Source amplitude [V]").grid(row=0, column=0)
        ttk.Label(self.root, text="Frequency [Hz]").grid(row=1, column=0)
        ttk.Label(self.root, text="R_in [Ω]").grid(row=2, column=0)
        ttk.Label(self.root, text="L_in [H]").grid(row=3, column=0)
        ttk.Label(self.root, text="L_choke [H]").grid(row=4, column=0)
        ttk.Label(self.root, text="R_out [Ω]").grid(row=5, column=0)

        self.v_amp_entry = ttk.Entry(self.root, width=20, textvariable=self.v_amp_val)
        self.v_amp_entry.grid(row=0, column=1)

        self.freq_entry = ttk.Entry(self.root, width=20, textvariable=self.freq_val)
        self.freq_entry.grid(row=1, column=1)

        self.r_in_entry = ttk.Entry(self.root, width=20, textvariable=self.r_in_val)
        self.r_in_entry.grid(row=2, column=1)

        self.l_in_entry = ttk.Entry(self.root, width=20, textvariable=self.l_in_val)
        self.l_in_entry.grid(row=3, column=1)

        self.l_choke_entry = ttk.Entry(self.root, width=20, textvariable=self.l_choke_val)
        self.l_choke_entry.grid(row=4, column=1)

        self.r_out_entry = ttk.Entry(self.root, width=20, textvariable=self.r_out_val)
        self.r_out_entry.grid(row=5, column=1)

        ttk.Button(self.root, text="Reset", command=self.reset_values).grid(row=6, column=0)
        ttk.Button(self.root, text="Run simulation", command=self.run_sim).grid(row=6, column=1)

        self.img_schematic = tk.PhotoImage(file="./img/rectifier_diag_placeholder.png")
        ttk.Label(self.root, image=self.img_schematic).grid(row=0, column=2, rowspan=7)

    def reset_values(self):
        self.v_amp_val.set(str(self.default_params.v_amp))
        self.freq_val.set(str(self.default_params.freq))
        self.r_in_val.set(str(self.default_params.r_in))
        self.l_in_val.set(str(self.default_params.l_in))
        self.l_choke_val.set(str(self.default_params.l_choke))
        self.r_out_val.set(str(self.default_params.r_out))

    def run_sim(self):
        self.params.v_amp = [float(self.v_amp_entry.get())]
        self.params.freq = float(self.freq_entry.get())
        self.params.r_in = float(self.r_in_entry.get())
        self.params.l_in = float(self.l_in_entry.get())
        self.params.l_choke = float(self.l_choke_entry.get())
        self.params.r_out = float(self.r_out_entry.get())

        self.runner.run(self.params)

root = tk.Tk()
app = App(root)
root.mainloop()
