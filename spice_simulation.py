from PySpice.Spice.Netlist import Circuit
import matplotlib.pyplot as plt
import re

# --- Function to update netlist ---
def update_netlist(file, v_amp, freq):
    file = re.sub(r"\.param v_amp=.*", f".param v_amp={v_amp} freq={freq} cycles=1000", file)
    file = re.sub(r"\.end", "", file)
    return file


# --- Load base netlist once ---
with open("./netlists/six_pulse_rectifier.net") as f:
    base_netlist = f.read()

# --- Simulation parameters ---
v_amp = [400, 420]
freq = 50
cycles = 100
r_in = 0.2
l_in = 0.005
l_choke = 0.02
r_out = 1000
stop_time = 0.1

plt.figure()

for v_amp in v_amp:
    # Update netlist for this run
    netlist = update_netlist(base_netlist, v_amp, freq)
    netlist += "\n.tran 10p 100m 0 1u\n.end\n"
    print(netlist)
    # Create new circuit each time (important!)
    circuit = Circuit(f'Rectifier v_amp={v_amp}')
    circuit.raw_spice += netlist

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)

    analysis = simulator.transient(step_time=1e-6, end_time=100e-3)

    # Plot each result
    plt.plot(analysis.time, analysis['net_out'], label=f'v_amp={v_amp} V')

# --- Plot formatting ---
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')

plt.xlim(0.06, 0.1)
plt.ylim(0, 550)
plt.title('Rectifier Output for Different v_amp')
plt.legend()
plt.grid()
plt.show()

print("Last netlist: \n" + str(circuit))