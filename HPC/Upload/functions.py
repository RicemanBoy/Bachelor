from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
import numpy as np
from qiskit_aer import AerSimulator
from qiskit.transpiler.passes.synthesis import SolovayKitaev
from qiskit.synthesis import generate_basic_approximations

from qiskit_aer.noise import (NoiseModel, pauli_error)

from qiskit.circuit.library import UnitaryGate

################################################################################################################################################################
matrix_h = ([[2**(-0.5),2**(-0.5)],[2**(-0.5),-2**(-0.5)]])
h_ideal = UnitaryGate(matrix_h)

matrix_cx = ([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]])
cx_ideal = UnitaryGate(matrix_cx)       #Erst Target, dann Control Qubit!!

matrix_x = ([[0,1],[1,0]])
x_ideal = UnitaryGate(matrix_x)

matrix_z = ([[1,0],[0,-1]])
z_ideal = UnitaryGate(matrix_z)

def idk(new: list, a: list, b:list, c:list):
    for i in a:
        for j in b:
            for k in c:
                new.append(i+j+k)

def X_L(qc: QuantumCircuit, q: list, pos: int):
    qc.x(q[3])
    qc.x(q[10])
    if pos == 0:
        qc.x(q[0])
        qc.x(q[11])
    elif pos == 1:
        qc.x(q[1])
        qc.x(q[9])

def Z_L(qc: QuantumCircuit, q: list, pos: int):
    qc.z(q[0])
    qc.z(q[9])
    if pos == 0:
        qc.z(q[3])
        qc.z(q[11])
    elif pos == 1:
        qc.z(q[1])
        qc.z(q[10])

def CNOT_L(qc: QuantumCircuit, q: list, control = 0):
    for i in range(4):
        q[i], q[i+8] = q[i+8], q[i]
    
    if control == 0:
        q[0], q[1] = q[1], q[0]
        q[4], q[5] = q[5], q[4]
        q[8], q[9] = q[9], q[8]
    else:
        q[0], q[2] = q[2], q[0]
        q[4], q[6] = q[6], q[4]
        q[8], q[10] = q[10], q[8]

def H_L(qc: QuantumCircuit, q: list, pos: int):                 #state injection vom hadamard für einzelnes hadamard
    anc = qc.num_qubits - 1
    if pos != 2:
        qc.reset(anc)
    
        Z_L(qc, q, pos=pos)

        if pos == 0:                  #hier zu Z_L
            qc.append(cx_ideal, [anc,q[0]])
            qc.append(cx_ideal, [anc,q[3]])
            qc.append(cx_ideal, [anc,q[9]])
            qc.append(cx_ideal, [anc,q[11]])
        elif pos == 1:
            qc.append(cx_ideal, [anc,q[0]])
            qc.append(cx_ideal, [anc,q[1]])
            qc.append(cx_ideal, [anc,q[9]])
            qc.append(cx_ideal, [anc,q[10]])
        qc.append(h_ideal,[anc])
        if pos == 0:
            qc.append(cx_ideal, [q[0],anc])
            qc.append(cx_ideal, [q[3],anc])
            qc.append(cx_ideal, [q[10],anc])
            qc.append(cx_ideal, [q[11],anc])
        elif pos == 1:
            qc.append(cx_ideal, [q[1],anc])
            qc.append(cx_ideal, [q[3],anc])
            qc.append(cx_ideal, [q[9],anc])
            qc.append(cx_ideal, [q[10],anc])
        qc.append(h_ideal,[anc])
        qc.measure(anc, 7)
        if pos == 0:                        #hier zu X_L
            with qc.if_test((7,1)):
                qc.z(q[0])
                qc.z(q[3])
                qc.z(q[9])
                qc.z(q[11])

                qc.x(q[0])
                qc.x(q[3])
                qc.x(q[10])
                qc.x(q[11])
            #q[9], q[10] = q[10], q[9]
        elif pos == 1:
            with qc.if_test((7,1)):
                qc.z(q[0])
                qc.z(q[1])
                qc.z(q[9])
                qc.z(q[10])

                qc.x(q[1])
                qc.x(q[3])
                qc.x(q[9])
                qc.x(q[10])
            #q[0], q[3] = q[3], q[0]
    if pos == 2:
        for i in range(12):
            qc.h(q[i])
        q[0], q[3] = q[3], q[0]
        q[5], q[6] = q[6], q[5]
        q[9], q[10] = q[10], q[9]

def CZ_L(qc: QuantumCircuit, q:list):
    H_L(qc, q, 0)
    CNOT_L(qc, q, 1)
    H_L(qc, q, 0)

def S_L(qc: QuantumCircuit, q: list, pos: int):
    anc = qc.num_qubits - 1
    qc.reset(anc)
    qc.append(h_ideal,[anc])
    qc.s(anc)
    if pos == 0:                        #zu Z_L
        qc.append(cx_ideal, [anc,q[0]])
        qc.append(cx_ideal, [anc,q[3]])
        qc.append(cx_ideal, [anc,q[9]])
        qc.append(cx_ideal, [anc,q[11]])
    elif pos == 1:
        qc.append(cx_ideal, [anc,q[0]])
        qc.append(cx_ideal, [anc,q[1]])
        qc.append(cx_ideal, [anc,q[9]])
        qc.append(cx_ideal, [anc,q[10]])

    qc.measure(anc,7)
    if pos == 0:
        with qc.if_test((7,1)):
            qc.z(q[0])
            qc.z(q[9])
            qc.z(q[3])
            qc.z(q[11])
    elif pos == 1:
        with qc.if_test((7,1)):
            qc.z(q[0])
            qc.z(q[9])
            qc.z(q[1])
            qc.z(q[10])

def adj_S_L(qc: QuantumCircuit, q: list, pos: int):
    anc = qc.num_qubits - 1
    qc.reset(anc)
    qc.append(h_ideal,[anc])
    qc.sdg(anc)

    if pos == 0:                        #zu Z_L
        qc.append(cx_ideal, [anc,q[0]])
        qc.append(cx_ideal, [anc,q[3]])
        qc.append(cx_ideal, [anc,q[9]])
        qc.append(cx_ideal, [anc,q[11]])
    elif pos == 1:
        qc.append(cx_ideal, [anc,q[0]])
        qc.append(cx_ideal, [anc,q[1]])
        qc.append(cx_ideal, [anc,q[9]])
        qc.append(cx_ideal, [anc,q[10]])

    qc.measure(anc,7)
    if pos == 0:
        with qc.if_test((7,1)):
            qc.z(q[0])
            qc.z(q[9])
            qc.z(q[3])
            qc.z(q[11])
    elif pos == 1:
        with qc.if_test((7,1)):
            qc.z(q[0])
            qc.z(q[9])
            qc.z(q[1])
            qc.z(q[10])

def T_L(qc: QuantumCircuit, q: list, pos: int):
    anc = qc.num_qubits - 1
    qc.reset(anc)
    qc.append(h_ideal,[anc])
    qc.t(anc)

    if pos == 0:                        #zu Z_L
        qc.append(cx_ideal, [anc,q[0]])
        qc.append(cx_ideal, [anc,q[3]])
        qc.append(cx_ideal, [anc,q[9]])
        qc.append(cx_ideal, [anc,q[11]])
    elif pos == 1:
        qc.append(cx_ideal, [anc,q[0]])
        qc.append(cx_ideal, [anc,q[1]])
        qc.append(cx_ideal, [anc,q[9]])
        qc.append(cx_ideal, [anc,q[10]])
    qc.measure(anc,7)
    if pos == 0:
        with qc.if_test((7,1)):
            qc.reset(anc)
            qc.append(h_ideal,[anc])
            qc.s(anc)
            qc.append(cx_ideal, [anc,q[0]])
            qc.append(cx_ideal, [anc,q[3]])
            qc.append(cx_ideal, [anc,q[9]])
            qc.append(cx_ideal, [anc,q[11]])
            qc.measure(anc,7)
            with qc.if_test((7,1)):
                qc.z(q[0])
                qc.z(q[3])
                qc.z(q[9])
                qc.z(q[11])
    elif pos == 1:
        with qc.if_test((7,1)):
            qc.reset(anc)
            qc.append(h_ideal,[anc])
            qc.s(anc)
            qc.append(cx_ideal, [anc,q[0]])
            qc.append(cx_ideal, [anc,q[1]])
            qc.append(cx_ideal, [anc,q[9]])
            qc.append(cx_ideal, [anc,q[10]])
            qc.measure(anc,7)
            with qc.if_test((7,1)):
                qc.z(q[0])
                qc.z(q[1])
                qc.z(q[9])
                qc.z(q[10])

def adj_T_L(qc: QuantumCircuit, q: list, pos: int):
    anc = qc.num_qubits - 1
    qc.reset(anc)
    qc.append(h_ideal,[anc])
    qc.tdg(anc)

    if pos == 0:                        #zu Z_L
        qc.append(cx_ideal, [anc,q[0]])
        qc.append(cx_ideal, [anc,q[3]])
        qc.append(cx_ideal, [anc,q[9]])
        qc.append(cx_ideal, [anc,q[11]])
    elif pos == 1:
        qc.append(cx_ideal, [anc,q[0]])
        qc.append(cx_ideal, [anc,q[1]])
        qc.append(cx_ideal, [anc,q[9]])
        qc.append(cx_ideal, [anc,q[10]])

    qc.measure(anc,7)
    if pos == 0:
        with qc.if_test((7, 1)):
            qc.reset(anc)
            qc.append(h_ideal,[anc])
            qc.sdg(anc)
            qc.append(cx_ideal, [anc,q[0]])
            qc.append(cx_ideal, [anc,q[3]])
            qc.append(cx_ideal, [anc,q[9]])
            qc.append(cx_ideal, [anc,q[11]])
            qc.measure(anc,7)
            with qc.if_test((7 ,1)):
                qc.z(q[0])
                qc.z(q[3])
                qc.z(q[9])
                qc.z(q[11])
    elif pos == 1:
        with qc.if_test((7, 1)):
            qc.reset(anc)
            qc.append(h_ideal,[anc])
            qc.sdg(anc)
            qc.append(cx_ideal, [anc,q[0]])
            qc.append(cx_ideal, [anc,q[1]])
            qc.append(cx_ideal, [anc,q[9]])
            qc.append(cx_ideal, [anc,q[10]])
            qc.measure(anc,7)
            with qc.if_test((7, 1)):
                qc.z(q[0])
                qc.z(q[1])
                qc.z(q[9])
                qc.z(q[10])

circ = QuantumCircuit(1)
circ.rz(np.pi/8, 0)
basis = ["t", "tdg", "z", "h"]
approx = generate_basic_approximations(basis, depth=3)
skd = SolovayKitaev(recursion_degree=2, basic_approximations=approx)
rootT = skd(circ)

def root_T_L(qc: QuantumCircuit, q: list, pos: int, m: list, tracker):
    instruction = rootT.data
    for i in instruction:
        if i.name == "t":
            T_L(qc, q, pos=pos)
        if i.name == "tdg":
            adj_T_L(qc, q, pos=pos)
        if i.name == "h":
            H_L(qc, q, pos=pos)

circ = QuantumCircuit(1)
circ.rz(-np.pi/8, 0)
basis = ["t", "tdg", "z", "h"]
approx = generate_basic_approximations(basis, depth=3)
skd = SolovayKitaev(recursion_degree=2, basic_approximations=approx)
rootadjT = skd(circ)

def adj_root_T_L(qc: QuantumCircuit, q: list, pos: int, m:list, tracker):
    instruction = rootadjT.data
    for i in instruction:
        if i.name == "t":
            T_L(qc, q, pos=pos)
        if i.name == "tdg":
            adj_T_L(qc, q, pos=pos)
        if i.name == "h":
            H_L(qc, q, pos=pos)

def U2(qc: QuantumCircuit, q: list, pos: int):
    gate = ['s', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 'sdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 'tdg', 'h', 'sdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 't', 'h', 't', 'h', 's', 'h', 't', 'h', 'tdg', 'h', 'sdg', 'h', 'sdg', 'tdg', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 's', 'h', 's', 'h', 't', 'h', 'tdg', 'h', 'sdg', 'h', 'tdg', 'h', 'tdg', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 't']
    for i in gate:
        if i == "s":
            S_L(qc, q, pos=pos)
        if i == "sdg":
            adj_S_L(qc, q, pos=pos)
        if i == "t":
            T_L(qc, q, pos=pos)
        if i == "tdg":
            adj_T_L(qc, q, pos=pos)
        if i == "h":
            H_L(qc, q, pos=pos)

def adjU2(qc: QuantumCircuit, q: list, pos: int):
    gate = ['s', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 'sdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 'tdg', 'h', 'sdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 't', 'h', 't', 'h', 's', 'h', 't', 'h', 'tdg', 'h', 'sdg', 'h', 'sdg', 'tdg', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 's', 'h', 's', 'h', 't', 'h', 'tdg', 'h', 'sdg', 'h', 'tdg', 'h', 'tdg', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 'tdg', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 'tdg', 'h', 'tdg', 'h', 't', 'h', 't', 'h', 't']
    gate.reverse()
    for i in gate:
        if i == "sdg":
            S_L(qc, q, pos=pos)
        if i == "s":
            adj_S_L(qc, q, pos=pos)
        if i == "tdg":
            T_L(qc, q, pos=pos)
        if i == "t":
            adj_T_L(qc, q, pos=pos)
        if i == "h":
            H_L(qc, q, pos=pos)

def CU_L(qc: QuantumCircuit, q: list, n: list, tracker, err = False):
    if err:
        qec_ft(qc, q, tracker)
    U2(qc, q, 0)
    if err:
        qec_ft(qc, q, tracker)
    U2(qc, q, 1)
    CNOT_L(qc, q, 0)
    if err:
        qec_ft(qc, q, tracker)
    adjU2(qc, q, 1)
    CNOT_L(qc, q, 0)

def CT_L(qc: QuantumCircuit, q: list, n: list, tracker, err = False):
    # if err:
    #     qec_ft(qc, q, tracker)
    root_T_L(qc, q, 0, n, tracker)
    if err:
        qec_ft(qc, q, tracker)
    root_T_L(qc, q, 1, n, tracker)
    CNOT_L(qc, q, 0)
    # if err:
    #     qec_ft(qc, q, tracker)
    adj_root_T_L(qc, q, 1, n, tracker)
    CNOT_L(qc, q, 0)

def CS_L(qc: QuantumCircuit, q: list):
    T_L(qc, q, 0)
    T_L(qc, q, 1)
    CNOT_L(qc, q, 0)
    adj_T_L(qc, q, 1)
    CNOT_L(qc, q, 0)

def sortout(c_register: list, tracker):
    cbits = len(c_register[0])
    z_ref = ["00000","11100","00100","10100","01100","01010","00010","11010","10010","10001","00001","01001","11001"]
    x_ref = ["00000","11100","10100","00100","01100","01010","11010","00010","10010","10001","01001","00001","11001"]
    
    ref = []
    for i in z_ref:
        for j in x_ref:
            ref.append(i+j)

    check = [i[12:cbits-7] for i in c_register]
    
    done = 0
    brain = []
    for i in tracker[0]:
        if i == "z":
            if done == 0:
                hmm = [j[-5:] for j in check]
            else:
                hmm = [j[-done-5:-done] for j in check]
            done += 5
            for j in range(len(hmm)):
                for k in z_ref:
                    if hmm[j] == k:
                        hmm[j] = 1
            for j in range(len(hmm)):
                if hmm[j] != 1:
                    brain.append(j)
        if i == "q":
            if done == 0:
                hmm = [j[-10:] for j in check]                                      #HIER STIMMT WAS NET, FIXEN!!!
            else:
                hmm = [j[-done-10:-done] for j in check]                            
            done += 10
            for j in range(len(hmm)):
                for k in ref:
                    if hmm[j] == k:
                        hmm[j] = 1
            for j in range(len(hmm)):
                if hmm[j] != 1:
                    brain.append(j)
    return brain

def readout(qc: QuantumCircuit, shots: int, q: list, noise = 0):
    read = ClassicalRegister(12)
    qc.add_register(read)

    for i in range(12):
        qc.id(q[i])
        qc.measure(q[i],read[11-i])

    cbits = qc.num_clbits

    p = noise
    p_error = pauli_error([["X",p/2],["I",1-p],["Z",p/2]])
    p_error_2 = pauli_error([["XI",p/4],["IX",p/4],["II",1-p],["ZI",p/4],["IZ",p/4]])

    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(p_error, ['x', "z", 'h', "id"])  # Apply to single-qubit gates
    noise_model.add_all_qubit_quantum_error(p_error_2, ['cx'])  # Apply to 2-qubit gates

    sim = AerSimulator()
    job = sim.run(qc, shots=shots, noise_model = noise_model)
    result = job.result()
    counts = result.get_counts()

    return counts, cbits

def code_ft():                                 
    qr = QuantumRegister(15,"q")
    cbits = ClassicalRegister(7,"c")             #7(Preselection) + 1 als Zwischenspeicher für magic states = 8 zu Beginn
    qc = QuantumCircuit(qr, cbits)

    q = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]

    for i in range(15):
        qc.id(i)

    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.h(7)
    qc.h(11)
    qc.h(12)

    qc.cx(12,3)
    qc.cx(7,13)
    qc.cx(11,14)


    qc.cx(0,3)
    qc.cx(1,3)
    qc.cx(2,3)

    qc.cx(7,4)
    qc.cx(7,5)
    qc.cx(7,6)

    qc.cx(11,8)
    qc.cx(11,9)
    qc.cx(11,10)

    qc.cx(12,3)
    qc.cx(7,13)
    qc.cx(11,14)

    qc.h(12)
    qc.id(12), qc.measure(12,0)
    qc.id(13), qc.measure(13,1)
    qc.id(14), qc.measure(14,2)

    qc.reset(12), qc.id(12)
    qc.reset(13), qc.id(13)
    qc.reset(14)
    ####################################################
    for i in range(8):
        qc.cx(i,i+4)
    ####################################################
    qc.h(12)

    qc.cx(12,4)
    qc.cx(7,13)
    qc.cx(12,7)
    qc.cx(4,13)
    qc.cx(12,5)
    qc.cx(6,13)
    qc.cx(12,6)
    qc.cx(5,13)

    qc.h(12)
    qc.id(12), qc.measure(12,3)
    qc.id(13), qc.measure(13,4)

    qc.reset(12), qc.id(12)
    qc.reset(13), qc.id(13)
    
    ####################################################
    qc.h(12)

    qc.cx(12,13)
    qc.cx(8,13)
    qc.cx(10,12)
    qc.cx(9,12)
    qc.cx(11,13)
    qc.cx(12,13)

    qc.h(12)

    qc.id(12), qc.measure(12,5)
    qc.id(13), qc.measure(13,6)

    qc.reset(12)
    qc.reset(13)

    q[5],q[7] = q[7],q[5]
    q[6],q[7] = q[7],q[6]

    q[9],q[10] = q[10],q[9]
    q[10],q[11] = q[11],q[10]

    tracker = [""]

    ram = ClassicalRegister(1)
    qc.add_register(ram)
    
    return qc, q, tracker

def qec_ft(qc: QuantumCircuit, q:list, tracker):        #128 gates
    anc = qc.num_qubits - 1
    ancc = anc - 1
    qc.reset(anc)

    ec = ClassicalRegister(10)
    qc.add_register(ec)
    tracker[0] += "q"
    flag = ClassicalRegister(10)
    qc.add_register(flag)
    tracker[0] += "f"

    for k in range(1):
        #S2 Stabilizers
        qc.reset(anc), qc.reset(ancc)
        qc.id(anc), qc.id(ancc)
        qc.h(ancc), qc.cx(ancc, anc)
        qc.cx(q[0], anc)
        qc.cx(q[1], anc)
        qc.cx(q[2], anc)
        qc.cx(ancc, anc)
        qc.cx(q[3], anc)
        qc.h(ancc), qc.id(anc), qc.id(ancc)
        qc.measure(anc, ec[0]), qc.measure(ancc, flag[0])

        #S4 Stabilizer
        qc.reset(anc), qc.reset(ancc)
        qc.id(anc), qc.id(ancc)
        qc.h(ancc), qc.cx(ancc, anc)
        qc.cx(q[4], anc)
        qc.cx(q[5], anc)
        qc.cx(q[6], anc)
        qc.cx(ancc, anc)
        qc.cx(q[7], anc)
        qc.h(ancc), qc.id(anc), qc.id(ancc)
        qc.measure(anc, ec[1]), qc.measure(ancc, flag[0])

        #S6 Stabilizer
        qc.reset(anc), qc.reset(ancc)
        qc.id(anc), qc.id(ancc)
        qc.h(ancc), qc.cx(ancc, anc)
        qc.cx(q[8], anc)
        qc.cx(q[9], anc)
        qc.cx(q[10], anc)
        qc.cx(ancc, anc)
        qc.cx(q[11], anc)
        qc.h(ancc), qc.id(anc), qc.id(ancc)
        qc.measure(anc, ec[2]), qc.measure(ancc, flag[0])

        #S9 Stabilizer
        qc.reset(anc), qc.reset(ancc)
        qc.id(anc), qc.id(ancc)
        qc.h(ancc), qc.cx(ancc, anc)
        qc.cx(q[0],anc)
        qc.cx(q[2],anc)
        qc.cx(q[6],anc)
        qc.cx(q[7],anc)
        qc.cx(q[8],anc)
        qc.cx(ancc, anc)
        qc.cx(q[11],anc)
        qc.h(ancc), qc.id(anc), qc.id(ancc)
        qc.measure(anc, ec[3]), qc.measure(ancc, flag[0])

        #S10 Stabilizer
        qc.reset(anc), qc.reset(ancc)
        qc.id(anc), qc.id(ancc)
        qc.h(ancc), qc.cx(ancc, anc)
        qc.cx(q[0],anc)
        qc.cx(q[3],anc)
        qc.cx(q[4],anc)
        qc.cx(q[6],anc)
        qc.cx(q[10],anc)
        qc.cx(ancc, anc)
        qc.cx(q[11],anc)
        qc.h(ancc), qc.id(anc), qc.id(ancc)
        qc.measure(anc, ec[4]), qc.measure(ancc, flag[0])

        with qc.if_test((ec[0],1)):            #X0
            with qc.if_test((ec[3],1)):
                with qc.if_test((ec[4],1)):
                    qc.x(q[0])

        with qc.if_test((ec[0],1)):            #X1
            with qc.if_test((ec[3],0)):
                with qc.if_test((ec[4],0)):
                    qc.x(q[1])

        with qc.if_test((ec[0],1)):            #X2
            with qc.if_test((ec[3],1)):
                with qc.if_test((ec[4],0)):
                    qc.x(q[2])

        with qc.if_test((ec[0],1)):            #X3
            with qc.if_test((ec[3],0)):
                with qc.if_test((ec[4],1)):
                    qc.x(q[3])

        with qc.if_test((ec[1],1)):            #X4
            with qc.if_test((ec[3],0)):
                with qc.if_test((ec[4],1)):
                    qc.x(q[4])

        with qc.if_test((ec[1],1)):            #X5
            with qc.if_test((ec[3],0)):
                with qc.if_test((ec[4],0)):
                    qc.x(q[5])

        with qc.if_test((ec[1],1)):            #X6
            with qc.if_test((ec[3],1)):
                with qc.if_test((ec[4],1)):
                    qc.x(q[6])

        with qc.if_test((ec[1],1)):            #X7
            with qc.if_test((ec[3],1)):
                with qc.if_test((ec[4],0)):
                    qc.x(q[7])

        with qc.if_test((ec[2],1)):            #X8
            with qc.if_test((ec[3],1)):
                with qc.if_test((ec[4],0)):
                    qc.x(q[8])
        
        with qc.if_test((ec[2],1)):            #X9
            with qc.if_test((ec[3],0)):
                with qc.if_test((ec[4],0)):
                    qc.x(q[9])
        
        with qc.if_test((ec[2],1)):            #X10
            with qc.if_test((ec[3],0)):
                with qc.if_test((ec[4],1)):
                    qc.x(q[10])

        with qc.if_test((ec[2],1)):            #X11
            with qc.if_test((ec[3],1)):
                with qc.if_test((ec[4],1)):
                    qc.x(q[11])

    ###################Phaseflip Error Stabilizers############################
    for k in range(1):
        #S1 Stabilizers
        qc.reset(anc), qc.reset(ancc)
        qc.id(anc), qc.id(ancc)
        qc.h(anc), qc.cx(anc, ancc)
        qc.cx(anc, q[0])
        qc.cx(anc, q[1])
        qc.cx(anc, q[2])
        qc.cx(anc, ancc)
        qc.cx(anc, q[3])
        qc.h(anc)
        qc.id(anc), qc.id(ancc)
        qc.measure(anc, ec[5]), qc.measure(ancc, flag[5])

        #S3 Stabilizer
        qc.reset(anc), qc.reset(ancc)
        qc.id(anc), qc.id(ancc)
        qc.h(anc), qc.cx(anc, ancc)
        qc.cx(anc, q[4])
        qc.cx(anc, q[5])
        qc.cx(anc, q[6])
        qc.cx(anc, ancc)
        qc.cx(anc, q[7])
        qc.h(anc)
        qc.id(anc), qc.id(ancc)
        qc.measure(anc, ec[6]), qc.measure(ancc, flag[6])

        #S5 Stabilizer
        qc.reset(anc), qc.reset(ancc)
        qc.id(anc), qc.id(ancc)
        qc.h(anc), qc.cx(anc, ancc)
        qc.cx(anc, q[8])
        qc.cx(anc, q[9])
        qc.cx(anc, q[10])
        qc.cx(anc, ancc)
        qc.cx(anc, q[11])
        qc.h(anc)
        qc.id(anc), qc.id(ancc)
        qc.measure(anc, ec[7]), qc.measure(ancc, flag[7])

        #S7 Stabilizer
        qc.reset(anc), qc.reset(ancc)
        qc.id(anc), qc.id(ancc)
        qc.h(anc), qc.cx(anc, ancc)
        qc.cx(anc, q[0])
        qc.cx(anc, q[1])
        qc.cx(anc, q[5])
        qc.cx(anc, q[7])
        qc.cx(anc, q[8])
        qc.cx(anc, ancc)
        qc.cx(anc, q[11])
        qc.h(anc)
        qc.id(anc), qc.id(ancc)
        qc.measure(anc, ec[8]), qc.measure(ancc, flag[8])

        #S8 Stabilizer
        qc.reset(anc), qc.reset(ancc)
        qc.id(anc), qc.id(ancc)
        qc.h(anc), qc.cx(anc, ancc)
        qc.cx(anc, q[0])
        qc.cx(anc, q[3])
        qc.cx(anc, q[4])
        qc.cx(anc, q[5])
        qc.cx(anc, q[9])
        qc.cx(anc, ancc)
        qc.cx(anc, q[11])
        qc.h(anc)
        qc.id(anc), qc.id(ancc)
        qc.measure(anc, ec[9]), qc.measure(ancc, flag[9])

        with qc.if_test((ec[5],1)):            #Z0
            with qc.if_test((ec[8],1)):
                with qc.if_test((ec[9],1)):
                    qc.z(q[0])

        with qc.if_test((ec[5],1)):            #Z1
            with qc.if_test((ec[8],1)):
                with qc.if_test((ec[9],0)):
                    qc.z(q[1])

        with qc.if_test((ec[5],1)):            #Z2
            with qc.if_test((ec[8],0)):
                with qc.if_test((ec[9],0)):
                    qc.z(q[2])

        with qc.if_test((ec[5],1)):            #Z3
            with qc.if_test((ec[8],0)):
                with qc.if_test((ec[9],1)):
                    qc.z(q[3])

        with qc.if_test((ec[6],1)):            #Z4
            with qc.if_test((ec[8],0)):
                with qc.if_test((ec[9],1)):
                    qc.z(q[4])

        with qc.if_test((ec[6],1)):            #Z5
            with qc.if_test((ec[8],1)):
                with qc.if_test((ec[9],1)):
                    qc.z(q[5])

        with qc.if_test((ec[6],1)):            #Z6
            with qc.if_test((ec[8],0)):
                with qc.if_test((ec[9],0)):
                    qc.z(q[6])

        with qc.if_test((ec[6],1)):            #Z7
            with qc.if_test((ec[8],1)):
                with qc.if_test((ec[9],0)):
                    qc.z(q[7])

        with qc.if_test((ec[7],1)):            #Z8
            with qc.if_test((ec[8],1)):
                with qc.if_test((ec[9],0)):
                    qc.z(q[8])
        
        with qc.if_test((ec[7],1)):            #Z9
            with qc.if_test((ec[8],0)):
                with qc.if_test((ec[9],1)):
                    qc.z(q[9])
        
        with qc.if_test((ec[7],1)):            #Z10
            with qc.if_test((ec[8],0)):
                with qc.if_test((ec[9],0)):
                    qc.z(q[10])

        with qc.if_test((ec[7],1)):            #Z11
            with qc.if_test((ec[8],1)):
                with qc.if_test((ec[9],1)):
                    qc.z(q[11])

def fullpp_ft(counts: dict, shots: int, cbits: int, track, two = True):
    nn, ne, en, ee = ["0000","1111"], ["0011","1100"], ["0101","1010"], ["0110","1001"]
    zerozero, zeroone, onezero, oneone = [], [], [], []

    for i in range(1):
        idk(zerozero, nn, nn, nn)
        idk(zerozero, ne, en, ee)
        idk(zerozero, en, ee, ne)
        idk(zerozero, ee, ne, en)
        idk(zeroone, en, nn, ee)
        idk(zeroone, ee, en, nn)
        idk(zeroone, nn, ee, en)
        idk(zeroone, ne, ne, ne)
        idk(onezero, ee, nn, ne)
        idk(onezero, en, en, en)
        idk(onezero, ne, ee, nn)
        idk(onezero, nn, ne, ee)
        idk(oneone, ne, nn, en)
        idk(oneone, nn, en, ne)
        idk(oneone, ee, ee, ee)
        idk(oneone, en, ne, nn)

    bitstring = list(counts.keys())
    hmm = list(counts.values())

    bitstring = [i.replace(" ","") for i in bitstring]

    pre, preselected = [i[cbits-7:] for i in bitstring], 0
    bits = [i[:12] for i in bitstring]

    qf = [i[12:cbits-8] for i in bitstring]

    length = int(len(qf[0])/10)
    flags = []

    for i in range(len(qf)):
        flags.append("")
        for j in range(length):
            if j%2 == 0:
                flags[i] += qf[i][j*10:j*10+10]

    for i in range(len(pre)):
        if pre[i].count("1") != 0:
            bits[i] = "pre"
            preselected += hmm[i]

    for i in range(len(flags)):
        if flags[i].count("1") != 0:
            if bits[i] != "pre":
                bits[i] = "post"
    
    for i in range(len(bits)):
        for j in zerozero:
            if j == bits[i]:
                bits[i] = 0
                break
        if bits[i] != 0:
            for j in zeroone:
                if j == bits[i]:
                    bits[i] = 1
                    break
        if bits[i] != 1 and bits[i] != 0:
            for j in onezero:
                if j == bits[i]:
                    bits[i] = 2
                    break
        if bits[i] != 2 and bits[i] != 1 and bits[i] != 0:
            for j in oneone:
                if j == bits[i]:
                    bits[i] = 3
                    break
        if bits[i] != 0 and bits[i] != 1 and bits[i] != 2 and bits[i] != 3 and bits[i] != "pre":
            bits[i] = "post"

    if two:
        twoqubiterrors = sortout(bitstring, tracker=track)
        for i in twoqubiterrors:
            if bits[i] != "post" and bits[i] != "pre":
                bits[i] = "twoqubiterr"

    nullnull = 0
    nulleins = 0
    einsnull = 0
    einseins = 0
    post = 0
    twoqubiterr = 0

    for i in range(len(bits)):
        if bits[i] == 0:
            nullnull += hmm[i]
        if bits[i] == 1:
            nulleins += hmm[i]
        if bits[i] == 2:
            einsnull += hmm[i]
        if bits[i] == 3:
            einseins += hmm[i]
        if bits[i] == "post":
            post += hmm[i]
        if bits[i] == "twoqubiterr":
            twoqubiterr += hmm[i]


    nullnull = (nullnull/shots)
    nulleins = (nulleins/shots)
    einsnull = (einsnull/shots)
    einseins = (einseins/shots)
    preselected = (preselected/shots)
    post = (post/shots)
    twoqubiterr = (twoqubiterr/shots)

    return [preselected, twoqubiterr, post, nullnull, nulleins, einsnull, einseins]

################################################################################################################################################################
def gen_data(name):
    x = np.linspace(0,0.03,10)
    shots = 200
    pre, post, nn, ne, en, ee, pre2, two, post2, nn2, ne2, ee2, en2 = [],[],[],[],[],[],[],[],[],[],[],[],[]
    for i in x:
        qc, q, tracker = code_ft()      #first iteration iQPE, with 0.3 angle, U2 eqauls 0.15 rotation
        n = [0]
        X_L(qc, q, 1)
        H_L(qc, q, 0)
        #############################
        CT_L(qc, q, n, tracker, err=False)
        ###############################
        adj_T_L(qc, q, 0)
        H_L(qc, q, 0)
        counts, cbits = readout(qc, shots, q, noise=i)
        result = fullpp_ft(counts, shots, cbits, tracker, True)

        pre.append(result[0]), post.append(result[2]), nn.append(result[3]), ne.append(result[4]), en.append(result[5]), ee.append(result[6])
        ###################################################################################################
        qc, q, tracker = code_ft()      #first iteration iQPE, with 0.3 angle, U2 eqauls 0.15 rotation
        n = [0]
        X_L(qc, q, 1)
        H_L(qc, q, 0)
        #############################
        CT_L(qc, q, n, tracker, err=True)
        ###############################
        adj_T_L(qc, q, 0)
        H_L(qc, q, 0)
        counts, cbits = readout(qc, shots, q, noise=i)
        result = fullpp_ft(counts, shots, cbits, tracker, True)
            
        pre2.append(result[0]), two.append(result[1]), post2.append(result[2]), nn2.append(result[3]), ne2.append(result[4]), en2.append(result[5]), ee2.append(result[6])

    data = np.array((x,pre,post,nn,ne,en,ee,pre2,two,post2,nn2,ne2,en2,ee2))
    np.savetxt("FTCarbon_3rd_c+{}.txt".format(name), data, delimiter=",")
