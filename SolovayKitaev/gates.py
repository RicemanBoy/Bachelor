import qutip as qt
import numpy as np
from qutip import gates
from utils import det

# 1 qubit gates
I = qt.qeye(2)
X = qt.sigmax()
Y = qt.sigmay()
Z = qt.sigmaz()
H = gates.hadamard_transform()
S = gates.phasegate(np.pi / 2)
T = gates.phasegate(np.pi / 4)
adjT = gates.phasegate(-np.pi / 4)
SQNOT = gates.sqrtnot()

#SQNOT = [[0.5 + 0.5j, 0.5 - 0.5j], [0.5 - 0.5j, 0.5 + 0.5j]]

def Rx(angle):
    # return [[np.cos(angle/2), -1j*np.sin(angle/2)], [-1j*np.sin(angle/2), np.cos(angle/2)]]
    return gates.rx(angle)

def Ry(angle):
    # return [[np.cos(angle/2), -np.sin(angle/2)], [np.sin(angle/2), np.cos(angle/2)]]
    return gates.ry(angle)

def Rz(angle):
    # return [[np.exp(-1j*(angle/2)), 0], [0, np.exp(1j*(angle/2))]]
    return gates.rz(angle)

#H = np.matmul(X,Ry(np.pi/2))

# S = Rz(np.pi/2)

# T = Rz(np.pi/4)

def R(axis, angle):
    angle = np.remainder(angle, 2 * np.pi)
    if not (type(axis) is np.ndarray):
        axis = np.array(axis)
    axis = axis / np.linalg.norm(axis)
    return qt.Qobj(np.cos(angle / 2) * I - 1j * np.sin(angle / 2) * (axis[0] * X + axis[1] * Y + axis[2] * Z))

def Phase(angle):
    return qt.phasegate(angle)

# 2 qubit gates
CNOT = gates.cnot()
CZ = gates.csign()
Berkeley = gates.berkeley()
SWAP = gates.swap()
iSWAP = gates.iswap()
SQSWAP = gates.sqrtswap()
SQiSWAP = gates.sqrtiswap()

def aSWAP(angle):
    return gates.swapalpha(angle)

# 3 qubit gates
Fredkin = gates.fredkin()
Toffoli = gates.toffoli()



# Get unitary axis and angle
def bloch(U):
    if isinstance(U, qt.Qobj):
        U = U.full()
    angle = np.real(2 * np.arccos(np.trace(U) / 2))
    sin = np.sin(angle / 2)
    eps = 1e-10
    if sin < eps:
        axis = [0, 0, 1]
    else:
        nz = np.imag(U[1, 1] - U[0, 0]) / (2 * sin)
        nx = -np.imag(U[1, 0]) / sin
        ny = np.real(U[1, 0]) / sin
        axis = [nx, ny, nz]
    return axis, angle

# Create SU2 operator
def su2(U):
    t = 0.0j + det(U)
    phase = np.sqrt(1 / t)
    return phase * U
