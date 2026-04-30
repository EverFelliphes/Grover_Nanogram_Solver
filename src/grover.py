"""
Grover's algorithm components: diffuser, iteration count, and full circuit runner.
Depends on the oracle but is agnostic to its internal structure.
"""

import math

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

from .utils import get_accumulator_size, compute_max_block_flags, compute_max_window_aux
from .oracle import create_nxm_oracle


def create_diffuser(num_qubits):
    """Standard Grover diffusion operator D = 2|s><s| - I."""
    qc = QuantumCircuit(num_qubits, name="Diffuser")
    qc.h(range(num_qubits))
    qc.x(range(num_qubits))
    qc.h(num_qubits - 1)
    qc.mcx(list(range(num_qubits - 1)), num_qubits - 1)
    qc.h(num_qubits - 1)
    qc.x(range(num_qubits))
    qc.h(range(num_qubits))
    return qc.to_gate()


def compute_grover_iterations(N, M, num_solutions=1):
    """
    Optimal number of Grover iterations for an N×M board.
    For M solutions in a search space of size 2^(NM):
        k = floor( (pi/4) * sqrt(2^(NM) / M) )
    (eq. 31 of the paper, generalized for M > 1 solutions)
    """
    n = N * M
    search_space = 2 ** n
    if num_solutions <= 0:
        return 1
    ratio = search_space / num_solutions
    k = max(1, int(math.floor((math.pi / 4) * math.sqrt(ratio))))
    return k


def run_grover(N, M, row_hints, col_hints, grover_iters, shots=2048):
    """
    Builds and runs the full Grover circuit for the given nonogram.
    Returns a dict with counts, qubit count, and circuit depths.
    """
    num_inputs   = N * M
    acc_size     = get_accumulator_size(N, M)
    num_zeros    = max(1, acc_size - 1)
    all_hints    = row_hints + col_hints
    num_sum_flags = N + M
    num_ord_flags = sum(1 for h in all_hints if h != [0])
    max_block_flags = compute_max_block_flags(row_hints, col_hints)
    max_win_aux     = compute_max_window_aux(N, M, row_hints, col_hints)

    # Define registers
    q_inputs  = QuantumRegister(num_inputs,      'in')
    q_zero    = QuantumRegister(num_zeros,        '0')
    q_acc     = QuantumRegister(acc_size,         'acc')
    q_sum_fl  = QuantumRegister(num_sum_flags,    'fl_sum')
    q_ord_fl  = QuantumRegister(num_ord_flags,    'fl_ord') if num_ord_flags > 0 else None
    q_oracle  = QuantumRegister(1,                'oracle')
    q_cin     = QuantumRegister(1,                'cin')
    q_cout    = QuantumRegister(1,                'cout')
    q_win_aux = QuantumRegister(max_win_aux,      'win_aux')
    q_blk_fl  = QuantumRegister(max_block_flags,  'blk_fl')
    c_out     = ClassicalRegister(num_inputs,     'meas')

    regs = [q_inputs, q_zero, q_acc, q_sum_fl]
    if q_ord_fl is not None:
        regs.append(q_ord_fl)
    regs += [q_oracle, q_cin, q_cout, q_win_aux, q_blk_fl]
    regs.append(c_out)

    qc = QuantumCircuit(*regs)

    oracle_gate   = create_nxm_oracle(N, M, row_hints, col_hints)
    diffuser_gate = create_diffuser(num_inputs)

    # Initial state: superposition on inputs, |-> on oracle qubit
    qc.h(q_inputs)
    qc.x(q_oracle)
    qc.h(q_oracle)

    # Flat qubit list matching oracle gate's internal ordering
    qubits_all = (list(q_inputs) + list(q_zero) + list(q_acc) +
                  list(q_sum_fl) +
                  (list(q_ord_fl) if q_ord_fl is not None else []) +
                  [q_oracle[0], q_cin[0], q_cout[0]] +
                  list(q_win_aux) + list(q_blk_fl))

    for _ in range(grover_iters):
        qc.append(oracle_gate, qubits_all)
        qc.append(diffuser_gate, q_inputs)

    qc.measure(q_inputs, c_out)

    depth_original    = qc.depth()
    n_qubits_original = qc.num_qubits

    simulator    = AerSimulator(method='matrix_product_state')
    qc_transpiled = transpile(qc, simulator, optimization_level=0)
    depth_2q     = qc_transpiled.depth()

    job    = simulator.run(qc_transpiled, shots=shots)
    counts = job.result().get_counts()

    return {
        'counts':         counts,
        'n_qubits':       n_qubits_original,
        'depth_original': depth_original,
        'depth_2q':       depth_2q,
    }
