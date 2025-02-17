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
def code_test(n: int):                                     #intialize |00> state   ,   n = 2*#qec + #z_qec
    qr = QuantumRegister(15,"q")
    cbits = ClassicalRegister(19+n*5,"c")             #12(Auslesen am Ende) + 7(Preselection) + 5(Stabilizers) = 24 insgesamt
    qc = QuantumCircuit(qr, cbits)

    q = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]

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
    qc.measure(12,0)
    qc.measure(13,1)
    qc.measure(14,2)

    qc.reset(12)
    qc.reset(13)
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
    qc.measure(12,3)
    qc.measure(13,4)

    qc.reset(12)
    qc.reset(13)
    
    ####################################################
    qc.h(12)

    qc.cx(12,13)
    qc.cx(8,13)
    qc.cx(10,12)
    qc.cx(9,12)
    qc.cx(11,13)
    qc.cx(12,13)

    qc.h(12)

    qc.measure(12,5)
    qc.measure(13,6)

    qc.reset(12)
    qc.reset(13)

    q[5],q[7] = q[7],q[5]
    q[6],q[7] = q[7],q[6]

    q[9],q[10] = q[10],q[9]
    q[10],q[11] = q[11],q[10]
    
    return qc, q, ""

def sortout(c_register: list):
    cbits = len(c_register[0])
    z_ref = ["00000","11100","00100","10100","01100","01010","00010","11010","10010","10001","00001","01001","11001"]
    x_ref = ["00000","11100","10100","00100","01100","01010","11010","00010","10010","10001","01001","00001","11001"]
    
    ref = []
    for i in z_ref:
        for j in x_ref:
            ref.append(i+j)

    check = [i[12:cbits-7] for i in c_register]

    brain = []
    bruh = int((cbits-19)/10)
    for i in range(bruh):
        hmm = [j[int(10*i): int(10*(i+1))] for j in check]
        for j in range(len(hmm)):
            for k in ref:
                if hmm[j] == k:
                    hmm[j] = 1
        for j in range(len(hmm)):
            if hmm[j] != 1:
                brain.append(j)
    return brain

def sortout_updated(c_register: list, tracker):
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
    for i in tracker:
        if tracker[i] == "z":
            hmm = [j[-done-5:-done] for j in check]
            done += 5
            for j in range(len(hmm)):
                for k in z_ref:
                    if hmm[j] == k:
                        hmm[j] = 1
            for j in range(len(hmm)):
                if hmm[j] != 1:
                    brain.append(j)
        if tracker[i] == "q":
            hmm = [j[-done-10:-done] for j in check]
            done += 10
            for j in range(len(hmm)):
                for k in z_ref:
                    if hmm[j] == k:
                        hmm[j] = 1
            for j in range(len(hmm)):
                if hmm[j] != 1:
                    brain.append(j)
    return brain

def qec_ideal(qc: QuantumCircuit, q:list, n: int, tracker):              #n --> +2
    anc = qc.num_qubits - 1
    qc.reset(anc)
    tracker += "q"
    n += 2
    #####################Bitflip Error Stabilizer messen########################################
    for k in range(1):

        #S2 Stabilizers
        for i in range(4):
            qc.append(cx_ideal, [anc, q[i]])
        qc.measure(anc, 7+n*5)
        qc.reset(anc)

        #S4 Stabilizer
        for i in range(4):
            qc.append(cx_ideal, [anc, q[i+4]])
        qc.measure(anc, 8+n*5)
        qc.reset(anc)

        #S6 Stabilizer
        for i in range(4):
            qc.append(cx_ideal, [anc, q[i+8]])
        qc.measure(anc, 9+n*5)
        qc.reset(anc)

        #S9 Stabilizer
        qc.append(cx_ideal, [anc, q[0]])
        qc.append(cx_ideal, [anc, q[2]])
        qc.append(cx_ideal, [anc, q[6]])
        qc.append(cx_ideal, [anc, q[7]])
        qc.append(cx_ideal, [anc, q[8]])
        qc.append(cx_ideal, [anc, q[11]])
        qc.measure(anc, 10+n*5)
        qc.reset(anc)

        #S10 Stabilizer
        qc.append(cx_ideal, [anc, q[0]])
        qc.append(cx_ideal, [anc, q[3]])
        qc.append(cx_ideal, [anc, q[4]])
        qc.append(cx_ideal, [anc, q[6]])
        qc.append(cx_ideal, [anc, q[10]])
        qc.append(cx_ideal, [anc, q[11]])
        qc.measure(anc, 11+n*5)
        qc.reset(anc)

        with qc.if_test((7+n*5,1)):            #X0
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[0]])

        with qc.if_test((7+n*5,1)):            #X1
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[1]])

        with qc.if_test((7+n*5,1)):            #X2
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[2]])

        with qc.if_test((7+n*5,1)):            #X3
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[3]])

        with qc.if_test((8+n*5,1)):            #X4
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[4]])

        with qc.if_test((8+n*5,1)):            #X5
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[5]])

        with qc.if_test((8+n*5,1)):            #X6
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[6]])

        with qc.if_test((8+n*5,1)):            #X7
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[7]])

        with qc.if_test((9+n*5,1)):            #X8
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[8]])
        
        with qc.if_test((9+n*5,1)):            #X9
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[9]])
        
        with qc.if_test((9+n*5,1)):            #X10
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[10]])

        with qc.if_test((9+n*5,1)):            #X11
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[11]])

    ###################Phaseflip Error Stabilizers############################
    for k in range(1):
        #S1 Stabilizers
        qc.append(h_ideal, [anc])
        for i in range(4):
            qc.append(cx_ideal, [q[i], anc])
        qc.append(h_ideal, [anc])
        qc.measure(anc, 12+n*5)
        qc.reset(anc)

        #S3 Stabilizer
        qc.append(h_ideal, [anc])
        for i in range(4):
            qc.append(cx_ideal, [q[i+4], anc])
        qc.append(h_ideal, [anc])
        qc.measure(anc, 13+n*5)
        qc.reset(anc)

        #S5 Stabilizer
        qc.append(h_ideal, [anc])
        for i in range(4):
            qc.append(cx_ideal, [q[i+8], anc])
        qc.append(h_ideal, [anc])
        qc.measure(anc, 14+n*5)
        qc.reset(anc)

        #S7 Stabilizer
        qc.append(h_ideal, [anc])
        qc.append(cx_ideal, [q[0], anc])
        qc.append(cx_ideal, [q[1], anc])
        qc.append(cx_ideal, [q[5], anc])
        qc.append(cx_ideal, [q[7], anc])
        qc.append(cx_ideal, [q[8], anc])
        qc.append(cx_ideal, [q[11], anc])
        qc.append(h_ideal, [anc])
        qc.measure(anc, 15+n*5)
        qc.reset(anc)

        #S8 Stabilizer
        qc.append(h_ideal, [anc])
        qc.append(cx_ideal, [q[0], anc])
        qc.append(cx_ideal, [q[3], anc])
        qc.append(cx_ideal, [q[4], anc])
        qc.append(cx_ideal, [q[5], anc])
        qc.append(cx_ideal, [q[9], anc])
        qc.append(cx_ideal, [q[11], anc])
        qc.append(h_ideal, [anc])
        qc.measure(anc, 16+n*5)
        qc.reset(anc)

        with qc.if_test((12+n*5,1)):            #Z0
            with qc.if_test((15+n*5,1)):
                with qc.if_test((16+n*5,1)):
                    qc.append(z_ideal,[q[0]])

        with qc.if_test((12+n*5,1)):            #Z1
            with qc.if_test((15+n*5,1)):
                with qc.if_test((16+n*5,0)):
                    qc.append(z_ideal,[q[1]])

        with qc.if_test((12+n*5,1)):            #Z2
            with qc.if_test((15+n*5,0)):
                with qc.if_test((16+n*5,0)):
                    qc.append(z_ideal,[q[2]])

        with qc.if_test((12+n*5,1)):            #Z3
            with qc.if_test((15+n*5,0)):
                with qc.if_test((16+n*5,1)):
                    qc.append(z_ideal,[q[3]])

        with qc.if_test((13+n*5,1)):            #Z4
            with qc.if_test((15+n*5,0)):
                with qc.if_test((16+n*5,1)):
                    qc.append(z_ideal,[q[4]])

        with qc.if_test((13+n*5,1)):            #Z5
            with qc.if_test((15+n*5,1)):
                with qc.if_test((16+n*5,1)):
                    qc.append(z_ideal,[q[5]])

        with qc.if_test((13+n*5,1)):            #Z6
            with qc.if_test((15+n*5,0)):
                with qc.if_test((16+n*5,0)):
                    qc.append(z_ideal,[q[6]])

        with qc.if_test((13+n*5,1)):            #Z7
            with qc.if_test((15+n*5,1)):
                with qc.if_test((16+n*5,0)):
                    qc.append(z_ideal,[q[7]])

        with qc.if_test((14+n*5,1)):            #Z8
            with qc.if_test((15+n*5,1)):
                with qc.if_test((16+n*5,0)):
                    qc.append(z_ideal,[q[8]])
        
        with qc.if_test((14+n*5,1)):            #Z9
            with qc.if_test((15+n*5,0)):
                with qc.if_test((16+n*5,1)):
                    qc.append(z_ideal,[q[9]])
        
        with qc.if_test((14+n*5,1)):            #Z10
            with qc.if_test((15+n*5,0)):
                with qc.if_test((16+n*5,0)):
                    qc.append(z_ideal,[q[10]])

        with qc.if_test((14+n*5,1)):            #Z11
            with qc.if_test((15+n*5,1)):
                with qc.if_test((16+n*5,1)):
                    qc.append(z_ideal,[q[11]])  

def z_qec_ideal(qc: QuantumCircuit, q:list, n: int, tracker):            #n --> +1
    anc = qc.num_qubits - 1
    qc.reset(anc)
    tracker += "z"
    n += 1
    #####################Bitflip Error Stabilizer messen########################################
    for k in range(1):

        #S2 Stabilizers
        for i in range(4):
            qc.append(cx_ideal, [anc, q[i]])
        qc.measure(anc, 7+n*5)
        qc.reset(anc)

        #S4 Stabilizer
        for i in range(4):
            qc.append(cx_ideal, [anc, q[i+4]])
        qc.measure(anc, 8+n*5)
        qc.reset(anc)

        #S6 Stabilizer
        for i in range(4):
            qc.append(cx_ideal, [anc, q[i+8]])
        qc.measure(anc, 9+n*5)
        qc.reset(anc)

        #S9 Stabilizer
        qc.append(cx_ideal, [anc, q[0]])
        qc.append(cx_ideal, [anc, q[2]])
        qc.append(cx_ideal, [anc, q[6]])
        qc.append(cx_ideal, [anc, q[7]])
        qc.append(cx_ideal, [anc, q[8]])
        qc.append(cx_ideal, [anc, q[11]])
        qc.measure(anc, 10+n*5)
        qc.reset(anc)

        #S10 Stabilizer
        qc.append(cx_ideal, [anc, q[0]])
        qc.append(cx_ideal, [anc, q[3]])
        qc.append(cx_ideal, [anc, q[4]])
        qc.append(cx_ideal, [anc, q[6]])
        qc.append(cx_ideal, [anc, q[10]])
        qc.append(cx_ideal, [anc, q[11]])
        qc.measure(anc, 11+n*5)
        qc.reset(anc)

        with qc.if_test((7+n*5,1)):            #X0
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[0]])

        with qc.if_test((7+n*5,1)):            #X1
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[1]])

        with qc.if_test((7+n*5,1)):            #X2
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[2]])

        with qc.if_test((7+n*5,1)):            #X3
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[3]])

        with qc.if_test((8+n*5,1)):            #X4
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[4]])

        with qc.if_test((8+n*5,1)):            #X5
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[5]])

        with qc.if_test((8+n*5,1)):            #X6
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[6]])

        with qc.if_test((8+n*5,1)):            #X7
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[7]])

        with qc.if_test((9+n*5,1)):            #X8
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[8]])
        
        with qc.if_test((9+n*5,1)):            #X9
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,0)):
                    qc.append(x_ideal, [q[9]])
        
        with qc.if_test((9+n*5,1)):            #X10
            with qc.if_test((10+n*5,0)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[10]])

        with qc.if_test((9+n*5,1)):            #X11
            with qc.if_test((10+n*5,1)):
                with qc.if_test((11+n*5,1)):
                    qc.append(x_ideal, [q[11]])

def readout_2(qc: QuantumCircuit, shots: int, q: list, noise = 0):
    cbits = qc.num_clbits

    for i in range(12):
        qc.id(q[i])
        qc.measure(q[i],cbits-i-1)

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

def fullpp(counts: dict, shots: int, cbits: int, two = True):
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

    pre, preselected = [i[cbits-7:] for i in bitstring], 0
    bits = [i[:12] for i in bitstring]

    for i in range(len(pre)):
        if pre[i].count("1") != 0:
            bits[i] = "pre"
            preselected += hmm[i]
    
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
        twoqubiterrors = sortout(bitstring)
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

def H_L(qc: QuantumCircuit, q: list, pos: int):
    anc = qc.num_qubits - 1
    cbits = qc.num_clbits - 1
    if pos != 2:
        qc.reset(anc)
        
        Z_L(qc, q, pos=pos)

        if pos == 0:                  #hier zu Z_L
            qc.cx(q[0], anc)
            qc.cx(q[3], anc)
            qc.cx(q[9], anc)
            qc.cx(q[11], anc)
        elif pos == 1:
            qc.cx(q[0], anc)
            qc.cx(q[1], anc)
            qc.cx(q[9], anc)
            qc.cx(q[10], anc)
        qc.h(anc)
        if pos == 0:
            qc.cx(anc, q[0])
            qc.cx(anc, q[3])
            qc.cx(anc, q[10])
            qc.cx(anc, q[11])
        elif pos == 1:
            qc.cx(anc, q[1])
            qc.cx(anc, q[3])
            qc.cx(anc, q[9])
            qc.cx(anc, q[10])
        qc.h(anc)
        qc.measure(anc, cbits)
        if pos == 0:                        #hier zu X_L
            with qc.if_test((cbits,1)):
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
            with qc.if_test((cbits,1)):
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
    cbits = qc.num_clbits - 1
    qc.reset(anc)
    qc.append(h_ideal,[anc])
    qc.s(anc)

    if pos == 0:                        #zu Z_L
        qc.cx(q[0], anc)
        qc.cx(q[3], anc)
        qc.cx(q[9], anc)
        qc.cx(q[11], anc)
    elif pos == 1:
        qc.cx(q[0], anc)
        qc.cx(q[1], anc)
        qc.cx(q[9], anc)
        qc.cx(q[10], anc)

    qc.measure(anc,cbits)
    if pos == 0:
        with qc.if_test((cbits,1)):
            qc.z(q[0])
            qc.z(q[9])
            qc.z(q[3])
            qc.z(q[11])
    elif pos == 1:
        with qc.if_test((cbits,1)):
            qc.z(q[0])
            qc.z(q[9])
            qc.z(q[1])
            qc.z(q[10])

def adj_S_L(qc: QuantumCircuit, q: list, pos: int):
    anc = qc.num_qubits - 1
    cbits = qc.num_clbits - 1
    qc.reset(anc)
    qc.append(h_ideal,[anc])
    qc.sdg(anc)

    if pos == 0:                        #zu Z_L
        qc.cx(q[0], anc)
        qc.cx(q[3], anc)
        qc.cx(q[9], anc)
        qc.cx(q[11], anc)
    elif pos == 1:
        qc.cx(q[0], anc)
        qc.cx(q[1], anc)
        qc.cx(q[9], anc)
        qc.cx(q[10], anc)

    qc.measure(anc,cbits)
    if pos == 0:
        with qc.if_test((cbits,1)):
            qc.z(q[0])
            qc.z(q[9])
            qc.z(q[3])
            qc.z(q[11])
    elif pos == 1:
        with qc.if_test((cbits,1)):
            qc.z(q[0])
            qc.z(q[9])
            qc.z(q[1])
            qc.z(q[10])

def T_L(qc: QuantumCircuit, q: list, pos: int):
    anc = qc.num_qubits - 1
    cbits = qc.num_clbits - 1
    qc.reset(anc)
    qc.append(h_ideal,[anc])
    qc.t(anc)

    if pos == 0:                        #zu Z_L
        qc.cx(q[0], anc)
        qc.cx(q[3], anc)
        qc.cx(q[9], anc)
        qc.cx(q[11], anc)
    elif pos == 1:
        qc.cx(q[0], anc)
        qc.cx(q[1], anc)
        qc.cx(q[9], anc)
        qc.cx(q[10], anc)

    qc.measure(anc,cbits)
    if pos == 0:
        with qc.if_test((cbits,1)):
            qc.reset(anc)
            qc.append(h_ideal,[anc])
            qc.s(anc)
            qc.cx(q[0], anc)
            qc.cx(q[3], anc)
            qc.cx(q[9], anc)
            qc.cx(q[11], anc)
            qc.measure(anc,cbits)
            with qc.if_test((cbits,1)):
                qc.z(q[0])
                qc.z(q[3])
                qc.z(q[9])
                qc.z(q[11])
    elif pos == 1:
        with qc.if_test((cbits,1)):
            qc.reset(anc)
            qc.append(h_ideal,[anc])
            qc.s(anc)
            qc.cx(q[0], anc)
            qc.cx(q[1], anc)
            qc.cx(q[9], anc)
            qc.cx(q[10], anc)
            qc.measure(anc,cbits)
            with qc.if_test((cbits,1)):
                qc.z(q[0])
                qc.z(q[1])
                qc.z(q[9])
                qc.z(q[10])

def adj_T_L(qc: QuantumCircuit, q: list, pos: int):
    anc = qc.num_qubits - 1
    cbits = qc.num_clbits - 1
    qc.reset(anc)
    qc.append(h_ideal,[anc])
    qc.tdg(anc)

    if pos == 0:                        #zu Z_L
        qc.cx(q[0], anc)
        qc.cx(q[3], anc)
        qc.cx(q[9], anc)
        qc.cx(q[11], anc)
    elif pos == 1:
        qc.cx(q[0], anc)
        qc.cx(q[1], anc)
        qc.cx(q[9], anc)
        qc.cx(q[10], anc)

    qc.measure(anc,cbits )
    if pos == 0:
        with qc.if_test((cbits ,1)):
            qc.reset(anc)
            qc.append(h_ideal,[anc])
            qc.sdg(anc)
            qc.cx(q[0], anc)
            qc.cx(q[3], anc)
            qc.cx(q[9], anc)
            qc.cx(q[11], anc)
            qc.measure(anc,cbits )
            with qc.if_test((cbits ,1)):
                qc.z(q[0])
                qc.z(q[3])
                qc.z(q[9])
                qc.z(q[11])
    elif pos == 1:
        with qc.if_test((cbits ,1)):
            qc.reset(anc)
            qc.append(h_ideal,[anc])
            qc.sdg(anc)
            qc.cx(q[0], anc)
            qc.cx(q[1], anc)
            qc.cx(q[9], anc)
            qc.cx(q[10], anc)
            qc.measure(anc,cbits )
            with qc.if_test((cbits ,1)):
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

def root_T_L(qc: QuantumCircuit, q: list, pos: int, n: int, err = False):
    instruction = rootT.data

    if err:
        for i in instruction:
            if i.name == "t":
                T_L(qc, q, pos=pos)
                z_qec_ideal(qc, q, n, tracker)
                n += 1
            if i.name == "tdg":
                adj_T_L(qc, q, pos=pos)
                z_qec_ideal(qc, q, n, tracker)
                n += 1
            if i.name == "h":
                H_L(qc, q, pos=pos)
    else:
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

def adj_root_T_L(qc: QuantumCircuit, q: list, pos: int, n:int, err=False):
    instruction = rootadjT.data

    if err:
        for i in instruction:
            if i.name == "t":
                T_L(qc, q, pos=pos)
                z_qec_ideal(qc, q, n, tracker)
                n += 1
            if i.name == "tdg":
                adj_T_L(qc, q, pos=pos)
                z_qec_ideal(qc, q, n, tracker)
                n += 1
            if i.name == "h":
                H_L(qc, q, pos=pos)
    else:
        for i in instruction:
            if i.name == "t":
                T_L(qc, q, pos=pos)
            if i.name == "tdg":
                adj_T_L(qc, q, pos=pos)
            if i.name == "h":
                H_L(qc, q, pos=pos)

def CT_L(qc: QuantumCircuit, q: list, n: int, err = False):
    if err:
        root_T_L(qc, q, 0, n, True)
        root_T_L(qc, q, 1, n, True)
        CNOT_L(qc, q, 0)
        adj_root_T_L(qc, q, 1, n, True)
        CNOT_L(qc, q, 0)
    else:
        root_T_L(qc, q, 0, n)
        root_T_L(qc, q, 1, n)
        CNOT_L(qc, q, 0)
        adj_root_T_L(qc, q, 1, n)
        CNOT_L(qc, q, 0)

def CS_L(qc: QuantumCircuit, q: list):
    T_L(qc, q, 0)
    T_L(qc, q, 1)
    CNOT_L(qc, q, 0)
    adj_T_L(qc, q, 1)
    CNOT_L(qc, q, 0)


################################################################################################################################################################
def gen_data(name):
    x = np.linspace(0,0.05,10)
    pre, post, nn, ne, en, ee, pre2, two, post2, nn2, ne2, ee2, en2 = [],[],[],[],[],[],[],[],[],[],[],[],[]
    shots = 100
    for i in x:
        # depolarizing_prob = i
        # dep_error = depolarizing_error(depolarizing_prob, 1)
        # dep_error_2q = depolarizing_error(depolarizing_prob, 2)
        # noise_model = NoiseModel()
        # noise_model.add_all_qubit_quantum_error(dep_error, ['x', "z",'h'])  # Apply to single-qubit gates
        # noise_model.add_all_qubit_quantum_error(dep_error_2q, ["cx"])  # Apply to 2-qubit gates
        
        qc, q, tracker = code_test(31)

        n = 0

        X_L(qc, q, 1)
        H_L(qc, q, 0)
        CT_L(qc, q, 6, False)
        adj_T_L(qc, q, 0)
        H_L(qc, q, 0)

        counts, cbits = readout_2(qc, shots, q, i)

        result = fullpp(counts, shots, cbits)

        nice, total = result[3] + result[4], result[3] + result[6] + result[4] + result[5]
        if total == 0:
            y_no_QEC.append(0.5)
        else:
            y_no_QEC.append(nice/total)

        pre.append(result[0]), post.append(result[2]), nn.append(result[3]), ne.append(result[4]), en.append(result[5]), ee.append(result[6])

        ###############################################################################################################

        qc, q, tracker = code_test(31)

        n = 0

        X_L(qc, q, 1)
        qec_ideal(qc, q, n, tracker)
        H_L(qc, q, 0)
        qec_ideal(qc, q, n, tracker)
        CT_L(qc, q, n, True)
        qec_ideal(qc, q, n, tracker)
        adj_T_L(qc, q, 0)
        qec_ideal(qc, q, n, tracker)
        H_L(qc, q, 0)

        counts, cbits = readout_2(qc, shots, q, i)

        result_1 = fullpp(counts, shots, cbits, True)

        nice, total = result_1[3] + result_1[4], result_1[6] + result_1[3] + result_1[4] + result_1[5]

        if total == 0:
            y.append(0.5)
        else:
            y.append(nice/total)

        pre2.append(result_1[0]), two.append(result_1[1]), post2.append(result_1[2]), nn2.append(result_1[3]), ne2.append(result_1[4]), en2.append(result_1[5]), ee2.append(result_1[6])

        data = np.array((pre,post,nn,ne,en,ee,pre2,two,post2,nn2,ne2,en2,ee2))
        np.savetxt("Carbon_3rd_1{}.txt".format(name), data, delimiter=",")
