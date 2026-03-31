from PySpice.Spice.Netlist import Circuit
import matplotlib.pyplot as plt
import re

# --- Function to update netlist ---
def update_netlist(file, Vin, Fin):
    file = re.sub(r"\.param Vin=.*", f".param Vin={Vin}", file)
    file = re.sub(r"\.param Fin=.*", f".param Fin={Fin}", file)
    file = re.sub(r"\.tran .*", "", file)
    file = re.sub(r"\.end", "", file)
    return file


# --- Load base netlist once ---
with open("./netlists/single_phase_rectifier_param.net") as f:
    base_netlist = f.read()

# --- Sweep values ---
Vin_values = [5, 10, 15, 20]   # sweep input amplitude
Fin = 50                       # keep frequency fixed

plt.figure()

for Vin in Vin_values:
    # Update netlist for this run
    netlist = update_netlist(base_netlist, Vin, Fin)

    # Create new circuit each time (important!)
    circuit = Circuit(f'Rectifier Vin={Vin}')
    circuit.raw_spice += netlist

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)

    analysis = simulator.transient(step_time=1e-6, end_time=100e-3)

    # Plot each result
    plt.plot(analysis.time, analysis['N002'], label=f'Vin={Vin} V')

# --- Plot formatting ---
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.title('Rectifier Output for Different Vin')
plt.legend()
plt.grid()
plt.show()

print("Last netlist: \n" + str(circuit))