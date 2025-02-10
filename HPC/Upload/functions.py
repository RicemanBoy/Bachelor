from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
import numpy as np
from qiskit_aer import AerSimulator
from qiskit.transpiler.passes.synthesis import SolovayKitaev
from qiskit.synthesis import generate_basic_approximations

from qiskit_aer.noise import (NoiseModel, pauli_error)

from qiskit.circuit.library import UnitaryGate


matrix_h = ([[2**(-0.5),2**(-0.5)],[2**(-0.5),-2**(-0.5)]])
h_ideal = UnitaryGate(matrix_h)

matrix_cx = ([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]])
cx_ideal = UnitaryGate(matrix_cx)       #Erst Target, dann Control Qubit!!

matrix_x = ([[0,1],[1,0]])
x_ideal = UnitaryGate(matrix_x)

matrix_z = ([[1,0],[0,-1]])
z_ideal = UnitaryGate(matrix_z)
################################################################################################################################################################
def code_goto(n=2):             #encodes |00>_L
    qr = QuantumRegister(7*n+1,"q")
    cbits = ClassicalRegister(9+6,"c")
    qc = QuantumCircuit(qr, cbits)
    
    anc = qc.num_qubits - 1

    for i in range(7*n):                        #start noise
        qc.id(i)

    for i in range(n):
        # qc.h(0+7*i)                           #funktioniert auch, aber der goto code geht auch, bin bloß dumm
        # qc.h(1+7*i)
        # qc.h(3+7*i)

        # qc.cx(0+7*i,2+7*i)
        # qc.cx(3+7*i,4+7*i)

        # qc.cx(1+7*i,5+7*i)

        # qc.cx(0+7*i,6+7*i)

        # qc.cx(1+7*i,2+7*i)
        # qc.cx(3+7*i,5+7*i)

        # qc.cx(0+7*i,4+7*i)

        # qc.cx(5+7*i,6+7*i)

        # qc.cx(2+7*i,anc)
        # qc.cx(4+7*i,anc)
        # qc.cx(5+7*i,anc)

        qc.h(1+7*i)
        qc.h(2+7*i)
        qc.h(3+7*i)

        qc.cx(1+7*i,0+7*i)
        qc.cx(3+7*i,5+7*i)

        qc.cx(2+7*i,6+7*i)

        qc.cx(1+7*i,4+7*i)

        qc.cx(2+7*i,0+7*i)
        qc.cx(3+7*i,6+7*i)

        qc.cx(1+7*i,5+7*i)

        qc.cx(6+7*i,4+7*i)

        qc.cx(0+7*i,anc)
        qc.cx(5+7*i,anc)
        qc.cx(6+7*i,anc)

        qc.id(anc)
        qc.measure(anc,i)      
    return qc

def X_L(qc: QuantumCircuit, pos: int):
    qc.x(0+7*pos)
    qc.x(1+7*pos)
    qc.x(2+7*pos)

def Z_L(qc: QuantumCircuit, pos: int):
    qc.z(0+7*pos)
    qc.z(1+7*pos)
    qc.z(2+7*pos)
    
def H_L(qc: QuantumCircuit, pos: int):
    for i in range(7):
        qc.h(i+7*pos)

def S_L(qc: QuantumCircuit, pos: int):
    for i in range(7):
        qc.sdg(i+7*pos)

def CZ_L(qc: QuantumCircuit):
    H_L(qc, 0)
    CNOT_L(qc, 1)
    H_L(qc, 0)

def adj_S_L(qc: QuantumCircuit, pos: int):
    for i in range(7):
        qc.s(i+7*pos)

def CNOT_L(qc: QuantumCircuit, control: int):
    if control == 0:
        for i in range(7):
            qc.cx(i, i+7)
    else:
        for i in range(7):
            qc.cx(i+7,i)

def T_L(qc: QuantumCircuit, pos: int):
    magic = qc.num_qubits - 1
    
    qc.reset(magic)
    qc.append(h_ideal, [magic])
    qc.t(magic)

    qc.append(cx_ideal,[magic, 0+7*pos])
    qc.append(cx_ideal,[magic, 1+7*pos])
    qc.append(cx_ideal,[magic, 2+7*pos])

    qc.measure(magic,magic)

    for i in range(7):
        with qc.if_test((magic,1)):
            qc.sdg(i+7*pos)

def adj_T_L(qc: QuantumCircuit, pos: int):
    magic = qc.num_qubits - 1
    qc.reset(magic)
    qc.append(h_ideal, [magic])
    qc.tdg(magic)

    qc.append(cx_ideal,[magic, 0+7*pos])
    qc.append(cx_ideal,[magic, 1+7*pos])
    qc.append(cx_ideal,[magic, 2+7*pos])

    qc.measure(magic,magic)

    for i in range(7):
        with qc.if_test((magic,1)):
            qc.s(i+7*pos)

circ = QuantumCircuit(1)
circ.rz(np.pi/8, 0)
basis = ["t", "tdg", "z", "h"]
approx = generate_basic_approximations(basis, depth=3)
skd = SolovayKitaev(recursion_degree=2, basic_approximations=approx)
rootT = skd(circ)

def root_T_L(qc: QuantumCircuit, pos: int, err = False):
    instruction = rootT.data
    if err:
        for i in instruction:
            if i.name == "t":
                z_qec(qc, pos=pos)
                T_L(qc, pos=pos)
            if i.name == "tdg":
                z_qec(qc, pos=pos)
                adj_T_L(qc, pos=pos)
            if i.name == "h":
                H_L(qc, pos=pos)
    else:
        for i in instruction:
            if i.name == "t":
                T_L(qc, pos=pos)
            if i.name == "tdg":
                adj_T_L(qc, pos=pos)
            if i.name == "h":
                H_L(qc, pos=pos)

circ = QuantumCircuit(1)
circ.rz(-np.pi/8, 0)
basis = ["t", "tdg", "z", "h"]
approx = generate_basic_approximations(basis, depth=3)
skd = SolovayKitaev(recursion_degree=2, basic_approximations=approx)
adj_rootT = skd(circ)

def adj_root_T_L(qc: QuantumCircuit, pos: int, err = False):
    instruction = adj_rootT.data
    if err:
        for i in instruction:
            if i.name == "t":
                z_qec(qc, pos=pos)
                T_L(qc, pos=pos)
            if i.name == "tdg":
                z_qec(qc, pos=pos)
                adj_T_L(qc, pos=pos)
            if i.name == "h":
                H_L(qc, pos=pos)
    else:
        for i in instruction:
            if i.name == "t":
                T_L(qc, pos=pos)
            if i.name == "tdg":
                adj_T_L(qc, pos=pos)
            if i.name == "h":
                H_L(qc, pos=pos)

def CT_L(qc: QuantumCircuit):
    root_T_L(qc, 0)
    root_T_L(qc, 1)
    CNOT_L(qc, 0)
    adj_root_T_L(qc, 1)
    CNOT_L(qc, 0)

def CS_L(qc: QuantumCircuit, control: int, target: int):
    T_L(qc, 0)
    T_L(qc, 1)
    CNOT_L(qc, control=control)
    adj_T_L(qc, pos = target)
    CNOT_L(qc, control=control)

def readout(qc: QuantumCircuit, pos: int, shots: int, noise = 0):
    p = noise
    p_error = pauli_error([["X",p/2],["I",1-p],["Z",p/2]])
    p_error_2 = pauli_error([["XI",p/4],["IX",p/4],["II",1-p],["ZI",p/4],["IZ",p/4]])

    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(p_error, ['x', "z", 'h', "s", "sdg", "id"])  # Apply to single-qubit gates
    noise_model.add_all_qubit_quantum_error(p_error_2, ['cx'])  # Apply to 2-qubit gates
    
    if pos == 0:
        for i in range(7):
            qc.id(i)
            qc.measure(i,14-i)
    elif pos == 1:
        for i in range(7):
            qc.id(i+7)
            qc.measure(7+i,14-i)

    sim = AerSimulator()
    
    job = sim.run(qc, shots=shots, noise_model=noise_model)

    result = job.result()
    counts = result.get_counts()

    bitstring = list(counts.keys())
    hmm = list(counts.values())

    pre, preselected = [i[13:] for i in bitstring], 0
    bits = [i[:7] for i in bitstring]
    #stab = [i[7:13] for i in bitstring]

    #print(pre)
    #print(bits)
    #print(stab)

    for i in range(len(pre)):
        if pre[i].count("1") != 0:
            bits[i] = "pre"
            preselected += hmm[i]

    test_0 = ["0000000","1010101","0110011","1100110","0001111","1011010","0111100","1101001"]
    test_1 = ["1111111","0101010","1001100","0011001","1110000","0100101","1000011","0010110"]

    for i in range(len(bits)):
        for j in test_0:
            if j == bits[i]:
                bits[i] = 0
                break
        if bits[i] != 0:
            for j in test_1:
                if j == bits[i]:
                    bits[i] = 1
                    break
        if bits[i] != 1 and bits[i] != 0 and bits[i] != "pre":
            bits[i] = "post"

    ones = 0
    zeros = 0
    post = 0

    for i in range(len(bits)):
        if bits[i] == 0:
            zeros += hmm[i]
        if bits[i] == 1:
            ones += hmm[i]
        if bits[i] == "post":
            post += hmm[i]
    
    ones = (ones/shots)
    zeros = (zeros/shots)
    post = (post/shots)
    preselected = (preselected/shots)

    # print("0: ", zeros, "%")
    # print("1: ", ones, "%")
    # print("Preselection discarded: ", (preselected/shots)*100, "%")
    # print("Postselection discarded: ", err - (preselected/shots)*100, "%")
    return zeros, ones, preselected, post

def qec(qc: QuantumCircuit, pos: int):
    anc = qc.num_qubits - 1
    qc.reset(anc)
    ##################################Z-Stabilizers##########################################
    qc.cx(0+7*pos, anc)
    qc.cx(2+7*pos, anc)
    qc.cx(4+7*pos, anc)
    qc.cx(6+7*pos, anc)

    qc.id(anc)
    qc.measure(anc, 2)
    qc.reset(anc)
    qc.id(anc)

    qc.cx(1+7*pos, anc)
    qc.cx(2+7*pos, anc)
    qc.cx(5+7*pos, anc)
    qc.cx(6+7*pos, anc)

    qc.id(anc)
    qc.measure(anc, 1)
    qc.reset(anc)
    qc.id(anc)

    qc.cx(3+7*pos, anc)
    qc.cx(4+7*pos, anc)
    qc.cx(5+7*pos, anc)
    qc.cx(6+7*pos, anc)

    qc.id(anc)
    qc.measure(anc, 0)
    qc.reset(anc)
    qc.id(anc)
    ##################################X-Stabilizers##############################################
    qc.h(anc)
    qc.cx(anc, 0+7*pos)
    qc.cx(anc, 2+7*pos)
    qc.cx(anc, 4+7*pos)
    qc.cx(anc, 6+7*pos)
    qc.h(anc)

    qc.id(anc)
    qc.measure(anc, 5)
    qc.reset(anc)
    qc.id(anc)

    qc.h(anc)
    qc.cx(anc, 1+7*pos)
    qc.cx(anc, 2+7*pos)
    qc.cx(anc, 5+7*pos)
    qc.cx(anc, 6+7*pos)
    qc.h(anc)

    qc.id(anc)
    qc.measure(anc, 4)
    qc.reset(anc)
    qc.id(anc)

    qc.h(anc)
    qc.cx(anc, 3+7*pos)
    qc.cx(anc, 4+7*pos)
    qc.cx(anc, 5+7*pos)
    qc.cx(anc, 6+7*pos)
    qc.h(anc)

    qc.id(anc)
    qc.measure(anc, 3)
    qc.reset(anc)
    ##################################Bitflip Error correction##############################################
    
    with qc.if_test((0,0)):             #qbit 0
        with qc.if_test((1,0)):
            with qc.if_test((2,1)):
                qc.x(0+7*pos)

    with qc.if_test((0,0)):             #qbit 1
        with qc.if_test((1,1)):
            with qc.if_test((2,0)):
                qc.x(1+7*pos)
    
    with qc.if_test((0,0)):             #qbit 2
        with qc.if_test((1,1)):
            with qc.if_test((2,1)):
                qc.x(2+7*pos)
    
    with qc.if_test((0,1)):             #qbit 3
        with qc.if_test((1,0)):
            with qc.if_test((2,0)):
                qc.x(3+7*pos)
    
    with qc.if_test((0,1)):             #qbit 4
        with qc.if_test((1,0)):
            with qc.if_test((2,1)):
                qc.x(4+7*pos)
    
    with qc.if_test((0,1)):             #qbit 5
        with qc.if_test((1,1)):
            with qc.if_test((2,0)):
                qc.x(5+7*pos)
    
    with qc.if_test((0,1)):             #qbit 6
        with qc.if_test((1,1)):
            with qc.if_test((2,1)):
                qc.x(6+7*pos)

    ##################################Phaseflip Error correction##############################################
    
    with qc.if_test((3,0)):             #qbit 0
        with qc.if_test((4,0)):
            with qc.if_test((5,1)):
                qc.z(0+7*pos)

    with qc.if_test((3,0)):             #qbit 1
        with qc.if_test((4,1)):
            with qc.if_test((5,0)):
                qc.z(1+7*pos)
    
    with qc.if_test((3,0)):             #qbit 2
        with qc.if_test((4,1)):
            with qc.if_test((5,1)):
                qc.z(2+7*pos)
    
    with qc.if_test((3,1)):             #qbit 3
        with qc.if_test((4,0)):
            with qc.if_test((5,0)):
                qc.z(3+7*pos)
    
    with qc.if_test((3,1)):             #qbit 4
        with qc.if_test((4,0)):
            with qc.if_test((5,1)):
                qc.z(4+7*pos)
    
    with qc.if_test((3,1)):             #qbit 5
        with qc.if_test((4,1)):
            with qc.if_test((5,0)):
                qc.z(5+7*pos)
    
    with qc.if_test((3,1)):             #qbit 6
        with qc.if_test((4,1)):
            with qc.if_test((5,1)):
                qc.z(6+7*pos)

def qec_ideal(qc: QuantumCircuit, pos: int):
    anc = qc.num_qubits - 1
    qc.reset(anc)
    ##################################Z-Stabilizers##########################################
    qc.append(cx_ideal, [anc, 0+7*pos])
    qc.append(cx_ideal, [anc, 2+7*pos])
    qc.append(cx_ideal, [anc, 4+7*pos])
    qc.append(cx_ideal, [anc, 6+7*pos])

    qc.measure(anc, 4)
    qc.reset(anc)

    qc.append(cx_ideal, [anc, 1+7*pos])
    qc.append(cx_ideal, [anc, 2+7*pos])
    qc.append(cx_ideal, [anc, 5+7*pos])
    qc.append(cx_ideal, [anc, 6+7*pos])

    qc.measure(anc, 3)
    qc.reset(anc)

    qc.append(cx_ideal, [anc, 3+7*pos])
    qc.append(cx_ideal, [anc, 4+7*pos])
    qc.append(cx_ideal, [anc, 5+7*pos])
    qc.append(cx_ideal, [anc, 6+7*pos])

    qc.measure(anc, 2)
    qc.reset(anc)
    ##################################Bitflip Error correction##############################################
    
    with qc.if_test((2,0)):             #qbit 0
        with qc.if_test((3,0)):
            with qc.if_test((4,1)):
                qc.append(x_ideal,[0+7*pos])

    with qc.if_test((2,0)):             #qbit 1
        with qc.if_test((3,1)):
            with qc.if_test((4,0)):
                qc.append(x_ideal,[1+7*pos])
    
    with qc.if_test((2,0)):             #qbit 2
        with qc.if_test((3,1)):
            with qc.if_test((4,1)):
                qc.append(x_ideal,[2+7*pos])
    
    with qc.if_test((2,1)):             #qbit 3
        with qc.if_test((3,0)):
            with qc.if_test((4,0)):
                qc.append(x_ideal,[3+7*pos])
    
    with qc.if_test((2,1)):             #qbit 4
        with qc.if_test((3,0)):
            with qc.if_test((4,1)):
                qc.append(x_ideal,[4+7*pos])
    
    with qc.if_test((2,1)):             #qbit 5
        with qc.if_test((3,1)):
            with qc.if_test((4,0)):
                qc.append(x_ideal,[5+7*pos])
    
    with qc.if_test((2,1)):             #qbit 6
        with qc.if_test((3,1)):
            with qc.if_test((4,1)):
                qc.append(x_ideal,[6+7*pos])

    ##################################X-Stabilizers##############################################
    qc.append(h_ideal, [anc])
    qc.append(cx_ideal, [0+7*pos, anc])
    qc.append(cx_ideal, [2+7*pos, anc])
    qc.append(cx_ideal, [4+7*pos, anc])
    qc.append(cx_ideal, [6+7*pos, anc])
    qc.append(h_ideal, [anc])

    qc.measure(anc, 7)
    qc.reset(anc)

    qc.append(h_ideal, [anc])
    qc.append(cx_ideal, [1+7*pos, anc])
    qc.append(cx_ideal, [2+7*pos, anc])
    qc.append(cx_ideal, [5+7*pos, anc])
    qc.append(cx_ideal, [6+7*pos, anc])
    qc.append(h_ideal, [anc])

    qc.measure(anc, 6)
    qc.reset(anc)

    qc.append(h_ideal, [anc])
    qc.append(cx_ideal, [3+7*pos, anc])
    qc.append(cx_ideal, [4+7*pos, anc])
    qc.append(cx_ideal, [5+7*pos, anc])
    qc.append(cx_ideal, [6+7*pos, anc])
    qc.append(h_ideal, [anc])

    qc.measure(anc, 5)
    qc.reset(anc)
    ##################################Phaseflip Error correction##############################################
    
    with qc.if_test((5,0)):             #qbit 0
        with qc.if_test((6,0)):
            with qc.if_test((7,1)):
                qc.append(z_ideal,[0+7*pos])

    with qc.if_test((5,0)):             #qbit 1
        with qc.if_test((6,1)):
            with qc.if_test((7,0)):
                qc.append(z_ideal,[1+7*pos])
    
    with qc.if_test((5,0)):             #qbit 2
        with qc.if_test((6,1)):
            with qc.if_test((7,1)):
                qc.append(z_ideal,[2+7*pos])
    
    with qc.if_test((5,1)):             #qbit 3
        with qc.if_test((6,0)):
            with qc.if_test((7,0)):
                qc.append(z_ideal,[3+7*pos])
    
    with qc.if_test((5,1)):             #qbit 4
        with qc.if_test((6,0)):
            with qc.if_test((7,1)):
                qc.append(z_ideal,[4+7*pos])
    
    with qc.if_test((5,1)):             #qbit 5
        with qc.if_test((6,1)):
            with qc.if_test((7,0)):
                qc.append(z_ideal,[5+7*pos])
    
    with qc.if_test((5,1)):             #qbit 6
        with qc.if_test((6,1)):
            with qc.if_test((7,1)):
                qc.append(z_ideal,[6+7*pos])
    
def z_qec(qc: QuantumCircuit, pos: int):
    anc = qc.num_qubits - 1
    qc.reset(anc)
    qc.id(anc)

    qc.cx(0+7*pos, anc)
    qc.cx(2+7*pos, anc)
    qc.cx(4+7*pos, anc)
    qc.cx(6+7*pos, anc)

    qc.id(anc)
    qc.measure(anc, 2)
    qc.reset(anc)
    qc.id(anc)

    qc.cx(1+7*pos, anc)
    qc.cx(2+7*pos, anc)
    qc.cx(5+7*pos, anc)
    qc.cx(6+7*pos, anc)

    qc.id(anc)
    qc.measure(anc, 1)
    qc.reset(anc)
    qc.id(anc)

    qc.cx(3+7*pos, anc)
    qc.cx(4+7*pos, anc)
    qc.cx(5+7*pos, anc)
    qc.cx(6+7*pos, anc)

    qc.id(anc)
    qc.measure(anc, 0)
    qc.reset(anc)

    with qc.if_test((0,0)):             #qbit 0
        with qc.if_test((1,0)):
            with qc.if_test((2,1)):
                qc.x(0+7*pos)

    with qc.if_test((0,0)):             #qbit 1
        with qc.if_test((1,1)):
            with qc.if_test((2,0)):
                qc.x(1+7*pos)
    
    with qc.if_test((0,0)):             #qbit 2
        with qc.if_test((1,1)):
            with qc.if_test((2,1)):
                qc.x(2+7*pos)
    
    with qc.if_test((0,1)):             #qbit 3
        with qc.if_test((1,0)):
            with qc.if_test((2,0)):
                qc.x(3+7*pos)
    
    with qc.if_test((0,1)):             #qbit 4
        with qc.if_test((1,0)):
            with qc.if_test((2,1)):
                qc.x(4+7*pos)
    
    with qc.if_test((0,1)):             #qbit 5
        with qc.if_test((1,1)):
            with qc.if_test((2,0)):
                qc.x(5+7*pos)
    
    with qc.if_test((0,1)):             #qbit 6
        with qc.if_test((1,1)):
            with qc.if_test((2,1)):
                qc.x(6+7*pos)

def z_qec_ideal(qc: QuantumCircuit, pos: int):
    anc = qc.num_qubits - 1
    qc.reset(anc)
    ##################################Z-Stabilizers##########################################
    qc.append(cx_ideal, [anc, 0+7*pos])
    qc.append(cx_ideal, [anc, 2+7*pos])
    qc.append(cx_ideal, [anc, 4+7*pos])
    qc.append(cx_ideal, [anc, 6+7*pos])

    qc.measure(anc, 4)
    qc.reset(anc)

    qc.append(cx_ideal, [anc, 1+7*pos])
    qc.append(cx_ideal, [anc, 2+7*pos])
    qc.append(cx_ideal, [anc, 5+7*pos])
    qc.append(cx_ideal, [anc, 6+7*pos])

    qc.measure(anc, 3)
    qc.reset(anc)

    qc.append(cx_ideal, [anc, 3+7*pos])
    qc.append(cx_ideal, [anc, 4+7*pos])
    qc.append(cx_ideal, [anc, 5+7*pos])
    qc.append(cx_ideal, [anc, 6+7*pos])

    qc.measure(anc, 2)
    qc.reset(anc)
    ##################################Bitflip Error correction##############################################
    with qc.if_test((2,0)):             #qbit 0
        with qc.if_test((3,0)):
            with qc.if_test((4,1)):
                qc.append(x_ideal,[0+7*pos])

    with qc.if_test((2,0)):             #qbit 1
        with qc.if_test((3,1)):
            with qc.if_test((4,0)):
                qc.append(x_ideal,[1+7*pos])
    
    with qc.if_test((2,0)):             #qbit 2
        with qc.if_test((3,1)):
            with qc.if_test((4,1)):
                qc.append(x_ideal,[2+7*pos])
    
    with qc.if_test((2,1)):             #qbit 3
        with qc.if_test((3,0)):
            with qc.if_test((4,0)):
                qc.append(x_ideal,[3+7*pos])
    
    with qc.if_test((2,1)):             #qbit 4
        with qc.if_test((3,0)):
            with qc.if_test((4,1)):
                qc.append(x_ideal,[4+7*pos])
    
    with qc.if_test((2,1)):             #qbit 5
        with qc.if_test((3,1)):
            with qc.if_test((4,0)):
                qc.append(x_ideal,[5+7*pos])
    
    with qc.if_test((2,1)):             #qbit 6
        with qc.if_test((3,1)):
            with qc.if_test((4,1)):
                qc.append(x_ideal,[6+7*pos])
################################################################################################################################################################
def gen_data(name):
    x = np.linspace(0,0.05,25)
    pre, post, zero, one, pre_QEC, post_QEC, zero_QEC, one_QEC = [],[],[],[],[],[],[],[]
    shots = 100
    for i in x:
        qc = code_goto()

        X_L(qc, 1)
        H_L(qc, 0)
        ###############
        root_T_L(qc, 0, err=True)
        qec(qc, 0)

        root_T_L(qc, 1, err=True)
        qec(qc, 1)

        CNOT_L(qc, 0)

        adj_root_T_L(qc, 1, err=True)
        qec(qc, 1)

        CNOT_L(qc, 0)
        ################
        adj_T_L(qc, 0)
        H_L(qc, 0)

        qec(qc, 0)

        zeros, ones, preselec , postselec = readout(qc, 0, shots, i)

        pre_QEC.append(preselec), post_QEC.append(postselec), one_QEC.append(ones), zero_QEC.append(zeros)
        ###################################################################################################
        qc = code_goto()

        X_L(qc, 1)
        H_L(qc, 0)
        ###############
        root_T_L(qc, 0, err=False)
        root_T_L(qc, 1, err=False)
        CNOT_L(qc, 0)
        adj_root_T_L(qc, 1, err=False)
        CNOT_L(qc, 0)
        ################
        adj_T_L(qc, 0)
        H_L(qc, 0)

        qec(qc, 0)
        zeros, ones, preselec, postselec = readout(qc, 0, shots, i)
        pre.append(preselec), post.append(postselec), one.append(ones), zero.append(zeros)

    data = np.array((x,pre,post,zero,one,pre_QEC,post_QEC, zero_QEC, one_QEC))
    np.savetxt("Steane_3rd_5_noisyy{}.txt".format(name), data, delimiter=",")
