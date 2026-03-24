from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt

# Load netlist from file
with open("./netlists/single_phase_rectifier.net") as f:
    netlist = f.read()

circuit = Circuit('Rectifier')
# NOTE: Requires fixing TSTEP as nonzero
circuit.raw_spice += netlist  #Add netlist as raw spice

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=100e-6, end_time=100e-3)
print(str(circuit))


# Plot output voltage
plt.plot(analysis.time, analysis['N002'])
plt.xlabel('Time [s]')
plt.ylabel('Voltage [V]')
plt.show()

'''
Possible fixes / enhancements:
 - Create netlists without defining .tran
 - Find a way to create netlists in a "pure" form i.e. no lib references
 - Remember (and check?) μ isn't read, has to be u
 - Add in .tran during creation (either find a way to finish netlist later, or just load file and add a line)
 - Netlists SHOULD BE PARAMETRIZED to enable edition in code!
'''