"""
Geometric subroutine: sliding-window and contiguity checks for nonogram blocks.
Isolates the spatial/structural constraints from arithmetic.
"""

from .utils import _block_window_size


def apply_window_check_for_block(qc, line_qubits, line_len,
                                  clue_list, b_idx,
                                  g_win_aux, block_flag_qubit):
    """
    Per-block sliding-window operator  Word,γ,b  (eq. 23):
      1. For each valid position w, mark aux qubit a_{b,w}.
      2. OR all a_{b,w} into block_flag_qubit via De Morgan.
      3. Uncompute all a_{b,w}.

    Neighbor cells (left/right of the window) are checked for emptiness
    using X-before-MCX-X pattern, per eq. (19) of the paper.

    Parameters
    ----------
    line_qubits   : list of Qubit — the qubits of the current line (in order)
    line_len      : int — length of the line
    clue_list     : list of int — all block lengths for this line
    b_idx         : int — 0-indexed block number within clue_list
    g_win_aux     : list of Qubit — auxiliary qubits for window marks (reused)
    block_flag_qubit : Qubit — output flag for this block
    """
    blk_len = clue_list[b_idx]
    k       = len(clue_list)

    s_min, s_max, win_size = _block_window_size(line_len, blk_len, b_idx, clue_list)

    if win_size <= 0:
        # No valid position exists — block flag stays 0 (constraint unsatisfiable)
        return

    # ---- 1. Compute: mark a_{b,w} for each valid position w ----
    for w_offset, w in enumerate(range(s_min, s_max + 1)):
        aux_q = g_win_aux[w_offset]

        # Determine neighbor indices to check for emptiness (eq. 19)
        # b_idx == 0        → check right neighbor (w + blk_len), if in bounds
        # 0 < b_idx < k-1   → check left (w-1) and right (w + blk_len)
        # b_idx == k-1      → check left neighbor (w-1), if in bounds
        neighbor_left  = (w - 1)          if b_idx > 0      else None
        neighbor_right = (w + blk_len)    if b_idx < k - 1  else None
        # Note: boundary positions are guaranteed in-bounds by s_min/s_max,
        # but we guard anyway for safety.

        # Collect all control qubits: window cells + neighbor (X-flipped) cells
        controls = [line_qubits[w + j] for j in range(blk_len)]

        flip_targets = []
        if neighbor_left is not None and 0 <= neighbor_left < line_len:
            controls.append(line_qubits[neighbor_left])
            flip_targets.append(line_qubits[neighbor_left])
        if neighbor_right is not None and 0 <= neighbor_right < line_len:
            controls.append(line_qubits[neighbor_right])
            flip_targets.append(line_qubits[neighbor_right])

        # X on neighbor cells so MCX fires when they are 0 (empty)
        for fq in flip_targets:
            qc.x(fq)

        qc.mcx(controls, aux_q)

        # Restore neighbor cells
        for fq in flip_targets:
            qc.x(fq)

    # ---- 2. Check: OR all a_{b,w} into block_flag via De Morgan ----
    # OR(a0, a1, ...) = NOT(AND(NOT(a0), NOT(a1), ...))
    # Implement: X on all aux, MCX → flag (inverted), X on aux, X on flag
    aux_used = [g_win_aux[i] for i in range(win_size)]

    qc.x(aux_used)
    qc.x(block_flag_qubit)
    qc.mcx(aux_used, block_flag_qubit)
    qc.x(aux_used)
    # Now block_flag_qubit == OR(a_{b,w})  (flag is 1 if any window matched)

    # ---- 3. Uncompute: restore all a_{b,w} to |0⟩ ----
    for w_offset, w in enumerate(range(s_min, s_max + 1)):
        aux_q = g_win_aux[w_offset]

        neighbor_left  = (w - 1)          if b_idx > 0      else None
        neighbor_right = (w + blk_len)    if b_idx < k - 1  else None

        controls = [line_qubits[w + j] for j in range(blk_len)]
        flip_targets = []
        if neighbor_left is not None and 0 <= neighbor_left < line_len:
            controls.append(line_qubits[neighbor_left])
            flip_targets.append(line_qubits[neighbor_left])
        if neighbor_right is not None and 0 <= neighbor_right < line_len:
            controls.append(line_qubits[neighbor_right])
            flip_targets.append(line_qubits[neighbor_right])

        for fq in flip_targets:
            qc.x(fq)
        qc.mcx(controls, aux_q)
        for fq in flip_targets:
            qc.x(fq)


def apply_order_check_for_line(qc, line_qubits, line_len,
                                clue_list,
                                g_win_aux, g_block_flags,
                                ord_flag_qubit):
    """
    Full geometric subroutine  Vord,γ  (eq. 25) for one line:
      For each block b: Word,γ,b  (compute-OR-uncompute window aux)
      Then MCX over all per-block flags → ord_flag_qubit
      Then uncompute block flags.

    Lines with clue [0] must NOT call this function.

    Parameters
    ----------
    g_block_flags : list of Qubit — per-block flags (reused across lines).
                    Must have at least len(clue_list) qubits.
    ord_flag_qubit : Qubit — global contiguity flag for this line.
    """
    k = len(clue_list)
    block_flags_used = g_block_flags[:k]

    # Per-block compute–OR–uncompute (sets block_flags_used[b])
    for b_idx in range(k):
        apply_window_check_for_block(
            qc, line_qubits, line_len,
            clue_list, b_idx,
            g_win_aux, block_flags_used[b_idx]
        )

    # MCX over all block flags → global contiguity flag (eq. 24)
    qc.mcx(list(block_flags_used), ord_flag_qubit)

    # Uncompute block flags (UCO† — eq. 25 comment)
    for b_idx in reversed(range(k)):
        apply_window_check_for_block(
            qc, line_qubits, line_len,
            clue_list, b_idx,
            g_win_aux, block_flags_used[b_idx]
        )
