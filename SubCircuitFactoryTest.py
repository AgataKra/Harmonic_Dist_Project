import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging()
import PySpice
from PySpice.Spice.Netlist import Circuit, SubCircuit, SubCircuitFactory
from PySpice.Unit import *

# Test of creating subckt with SubCircuitFactory
class ParallelResistor(SubCircuitFactory):
    NAME = 'parallel_resistor'
    NODES = ('n1', 'n2')
    def __init__(self, R1=1@u_Ω, R2=2@u_Ω):
        super().__init__()
        r1 = self.R(1, 'n1', 'n2', R1)
        r2 = self.R(2, 'n1', 'n2', R2)
        self.resistance =  r1.resistance * r2.resistance / (r1.resistance + r2.resistance)


circuit = Circuit('Test')
circuit.subcircuit(ParallelResistor(R2=3@u_Ω))
# X for custom model, name = X1, model = 'parallel_resistor' (NAME), two nodes: 1 and gnd
circuit.X('1', 'parallel_resistor', 1, circuit.gnd)
# Add voltage source
circuit.VoltageSource('1', 1, circuit.gnd, 10)

print(circuit)

# Test of creating subckt with SubCircuit
