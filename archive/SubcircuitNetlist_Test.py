from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt

circuit = Circuit('Rectifier Test')

# Add your subcircuit definition
with open("../netlists/rectifier_subc.sub", encoding="utf-16-le") as f:
    circuit.raw_spice = f.read()
circuit.raw_spice += "\n.model D D"
print(circuit.raw_spice)
# Add sinusoidal voltage source
circuit.SinusoidalVoltageSource('input', 'vin', circuit.gnd,
                                amplitude=10@u_V,
                                frequency=50@u_Hz)

# Instantiate subcircuit
circuit.X('1', 'rectifier_subc', 'vin', 'vout')

# Simulation
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=100@u_us, end_time=100@u_ms)

# Plot output
plt.plot(analysis.time, analysis['vout'])
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.title('Rectified Output')
plt.grid()
plt.show()