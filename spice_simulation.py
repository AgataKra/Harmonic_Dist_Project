from PySpice.Spice.Netlist import Circuit
import matplotlib.pyplot as plt
import re

class SimulationParameters:
    def __init__(self):
        self.v_amp = 400
        self.freq = 50
        self.cycles = 100
        self.r_in = 0.2
        self.l_in = 0.005
        self.l_choke = 0.02
        self.r_out = 1000
        self.stop_time = 0.1

class SimulationRunner:
    def __init__(self, netlist_path="./netlists/six_pulse_rectifier.net"):
        with open(netlist_path) as f:
            self.base_netlist = f.read()

    def update_netlist(self, v_amp, freq):
        net = re.sub(r"\.param v_amp=.*",
                     f".param v_amp={v_amp} freq={freq} cycles=1000",
                     self.base_netlist)
        net = re.sub(r"\.end", "", net)
        return net

    def run(self, params: SimulationParameters):
        plt.figure()

        for v_amp in params.v_amp:
            netlist = self.update_netlist(v_amp, params.freq)
            netlist += "\n.tran 10p 100m 0 1u\n.end\n"

            circuit = Circuit(f'Rectifier v_amp={v_amp}')
            circuit.raw_spice += netlist

            simulator = circuit.simulator(temperature=25, nominal_temperature=25)
            analysis = simulator.transient(step_time=1e-9, end_time=100e-3)

            plt.plot(analysis.time, analysis['net_out'], label=f'v_amp={v_amp} V')

        plt.xlabel('Time [s]')
        plt.ylabel('Voltage [V]')
        plt.xlim(0.06, 0.1)
        plt.ylim(0, 1.5*max(params.v_amp))
        plt.title('Rectifier Output for Different v_amp')
        plt.legend()
        plt.grid()
        plt.show()
