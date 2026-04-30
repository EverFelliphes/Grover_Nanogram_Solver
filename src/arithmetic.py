"""
Arithmetic subroutine: sum-check verification for nonogram lines.
Depends on primitives, but has no knowledge of geometry or puzzle rules.
"""

from qiskit import QuantumCircuit

from .primitives import generic_ripple_adder, compare_static


def create_adder_gate(acc_size):
    """Creates a reusable Cuccaro adder gate for acc_size-bit accumulation."""
    total = 1 + acc_size + acc_size + 1  # cin | source | target(acc) | cout
    qc = QuantumCircuit(total, name=f"Adder{acc_size}")
    cin    = qc.qubits[0]
    source = qc.qubits[1 : 1 + acc_size]
    target = qc.qubits[1 + acc_size : 1 + 2 * acc_size]
    cout   = qc.qubits[-1]
    generic_ripple_adder(qc, cin, source, target, cout)
    return qc.to_gate()


def apply_sum_check_for_line(qc, line_qubits, target_val,
                              g_zero, g_acc, g_cin, g_cout,
                              flag_qubit, adder_gate):
    """
    Compute–check–uncompute for the sum constraint of one line.
    Flips flag_qubit iff sum(line_qubits) == target_val.
    """
    acc_size = len(g_acc)

    # Build q_map for each qubit in the line:
    # [cin | input_bit | zero_padding | acc | cout]
    q_maps = []
    for q in line_qubits:
        padding = list(g_zero[: acc_size - 1])
        q_map = [g_cin] + [q] + padding + list(g_acc) + [g_cout]
        q_maps.append(q_map)

    # Compute: accumulate each bit into acc
    for q_map in q_maps:
        qc.append(adder_gate, q_map)

    # Check: compare accumulator to target
    compare_static(qc, g_acc, target_val, flag_qubit)

    # Uncompute: reverse the accumulation
    for q_map in reversed(q_maps):
        qc.append(adder_gate.inverse(), q_map)
