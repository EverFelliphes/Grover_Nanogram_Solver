"""
Full Grover oracle for the N×M nonogram.
Orchestrates arithmetic (sum checks) and geometry (contiguity checks).
"""

from qiskit import QuantumCircuit

from .utils import get_accumulator_size, compute_max_block_flags, compute_max_window_aux
from .arithmetic import create_adder_gate, apply_sum_check_for_line
from .geometry import apply_order_check_for_line


def create_nxm_oracle(N, M, row_hints, col_hints):
    """
    Builds the full Grover oracle for the N×M nonogram.

    row_hints : list of lists, e.g. [[1,2], [0], [3]]
    col_hints : list of lists, e.g. [[2], [1,1], [2]]

    Returns a gate with the following qubit order:
        inputs | zero_pad | acc | sum_flags | ord_flags | oracle | cin | cout | win_aux | block_flags
    """
    num_inputs   = N * M
    acc_size     = get_accumulator_size(N, M)
    num_zeros    = max(1, acc_size - 1)

    all_hints = row_hints + col_hints
    num_sum_flags = N + M
    lines_with_contiguity = [h for h in all_hints if h != [0]]
    num_ord_flags = len(lines_with_contiguity)
    max_block_flags = compute_max_block_flags(row_hints, col_hints)
    max_win_aux = compute_max_window_aux(N, M, row_hints, col_hints)

    total_qubits = (num_inputs + num_zeros + acc_size +
                    num_sum_flags + num_ord_flags +
                    1 + 1 + 1 + max_win_aux + max_block_flags)

    qc = QuantumCircuit(total_qubits, name="Oracle_Full")

    idx = 0
    g_inputs      = qc.qubits[idx: idx + num_inputs];      idx += num_inputs
    g_zero        = qc.qubits[idx: idx + num_zeros];        idx += num_zeros
    g_acc         = qc.qubits[idx: idx + acc_size];         idx += acc_size
    g_sum_flags   = qc.qubits[idx: idx + num_sum_flags];    idx += num_sum_flags
    g_ord_flags   = qc.qubits[idx: idx + num_ord_flags];    idx += num_ord_flags
    g_oracle      = qc.qubits[idx];                         idx += 1
    g_cin         = qc.qubits[idx];                         idx += 1
    g_cout        = qc.qubits[idx];                         idx += 1
    g_win_aux     = qc.qubits[idx: idx + max_win_aux];      idx += max_win_aux
    g_block_flags = qc.qubits[idx: idx + max_block_flags];  idx += max_block_flags

    adder_gate = create_adder_gate(acc_size)

    line_descriptors = []
    sum_flag_idx = 0
    ord_flag_idx = 0

    for r in range(N):
        line_qubits = [g_inputs[r * M + c] for c in range(M)]
        hints       = row_hints[r]
        target_sum  = sum(hints)
        has_cont    = (hints != [0])
        ofi = ord_flag_idx if has_cont else None
        if has_cont:
            ord_flag_idx += 1
        line_descriptors.append((line_qubits, M, hints, target_sum, sum_flag_idx, ofi))
        sum_flag_idx += 1

    for c in range(M):
        line_qubits = [g_inputs[r * M + c] for r in range(N)]
        hints       = col_hints[c]
        target_sum  = sum(hints)
        has_cont    = (hints != [0])
        ofi = ord_flag_idx if has_cont else None
        if has_cont:
            ord_flag_idx += 1
        line_descriptors.append((line_qubits, N, hints, target_sum, sum_flag_idx, ofi))
        sum_flag_idx += 1

    # COMPUTE: sum checks (Vsum)
    for (lq, ll, h, ts, sfi, ofi) in line_descriptors:
        apply_sum_check_for_line(qc, lq, ts, g_zero, g_acc, g_cin, g_cout, g_sum_flags[sfi], adder_gate)

    # COMPUTE: order checks (Vorder)
    for (lq, ll, h, ts, sfi, ofi) in line_descriptors:
        if ofi is None:
            continue
        apply_order_check_for_line(qc, lq, ll, h, list(g_win_aux), list(g_block_flags), g_ord_flags[ofi])

    # KICKBACK: MCX over all flags → oracle qubit
    all_flags = list(g_sum_flags) + list(g_ord_flags)
    qc.mcx(all_flags, g_oracle)

    # UNCOMPUTE: order checks (Vorder†)
    for (lq, ll, h, ts, sfi, ofi) in reversed(line_descriptors):
        if ofi is None:
            continue
        apply_order_check_for_line(qc, lq, ll, h, list(g_win_aux), list(g_block_flags), g_ord_flags[ofi])

    # UNCOMPUTE: sum checks (Vsum†)
    for (lq, ll, h, ts, sfi, ofi) in reversed(line_descriptors):
        apply_sum_check_for_line(qc, lq, ts, g_zero, g_acc, g_cin, g_cout, g_sum_flags[sfi], adder_gate)

    return qc.to_gate()
