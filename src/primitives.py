"""
Lowest-level quantum gate primitives: MAJ, UMA, Cuccaro ripple-carry adder,
and static comparator. No nonogram logic here.
"""

from qiskit import QuantumCircuit


def maj_gate(qc, c, b, a):
    """MAJ gate: c, b, a → majority."""
    qc.cx(c, b)
    qc.cx(c, a)
    qc.ccx(a, b, c)


def uma_gate(qc, c, b, a):
    """UMA gate: inverse of MAJ (uncompute carry)."""
    qc.ccx(a, b, c)
    qc.cx(c, a)
    qc.cx(a, b)


def generic_ripple_adder(qc, cin, reg_source, reg_target, cout):
    """
    Cuccaro ripple-carry adder.
    Adds reg_source into reg_target (in-place), with carry-in cin and carry-out cout.
    """
    n = len(reg_source)
    for i in range(n):
        maj_gate(qc, cin, reg_target[i], reg_source[i])
    qc.cx(cin, cout)
    for i in reversed(range(n)):
        uma_gate(qc, cin, reg_target[i], reg_source[i])


def compare_static(qc, reg_input, target_val_int, flag_qubit):
    """
    Flips flag_qubit iff reg_input encodes target_val_int.
    Uses X gates on zero-bits so that an MCX (all-ones check) fires correctly.
    """
    n = len(reg_input)
    for i in range(n):
        if not ((target_val_int >> i) & 1):
            qc.x(reg_input[i])
    qc.mcx(list(reg_input), flag_qubit)
    for i in range(n):
        if not ((target_val_int >> i) & 1):
            qc.x(reg_input[i])
