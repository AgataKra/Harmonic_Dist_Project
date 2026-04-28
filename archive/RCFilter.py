import math
import PySpice
import numpy as np
import matplotlib.pyplot as plt
import PySpice.Logging.Logging as Logging
from PySpice.Plot.BodeDiagram import bode_diagram
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# Test using subckt in this circuit (R as 'parallel-resistor from SubCircuitFactoryTest.py)
from SubCircuitFactoryTest import ParallelResistor

import os
#os.environ["path"] += os.pathsep + r"C:\Python38\lib\site-packages\PySpice\Spice\NgSpice\Spice64_dll\dll-vs"

logger = Logging.setup_logging()
circuit = Circuit('Low-Pass RC Filter')

circuit.SinusoidalVoltageSource('input', 'in', circuit.gnd, amplitude=1@u_V)
#R1 = circuit.R(1, 'in', 'out', 1@u_kΩ)
circuit.subcircuit(ParallelResistor(R1=2@u_kΩ,R2=2@u_kΩ))
R1 = circuit.X('1', 'parallel_resistor', 'in', 'out')
C1 = circuit.C(1, 'out', circuit.gnd, 1@u_uF)
R1_val = 2@u_kΩ
R2_val = 2@u_kΩ
Req = R1_val * R2_val / (R1_val + R2_val)

#break_frequency = 1 / (2 * math.pi * float(R1.resistance * C1.capacitance))
break_frequency = 1 / (2 * math.pi * float(Req * C1.capacitance))
print("Break frequency = {:.1f} Hz".format(break_frequency))
print(str(circuit))

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=1@u_MHz,
                        number_of_points=10, variation='dec')
print(analysis.out)

figure, axes = plt.subplots(2, figsize=(20, 10))
plt.title("Bode Diagram of a Low-Pass RC Filter")
bode_diagram(axes=axes, frequency=analysis.frequency,
             gain=20*np.log10(np.absolute(analysis.out)),
             phase=np.angle(analysis.out, deg=False), marker='.', color='blue',
             linestyle='-', )
for ax in axes: ax.axvline(x=break_frequency, color='red')

plt.tight_layout()
plt.show()