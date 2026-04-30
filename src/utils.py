"""
Pure utility functions for computing auxiliary resource sizes.
No Qiskit dependency — easy to test in isolation.
"""


def get_accumulator_size(N, M):
    """Bits needed to represent max(N, M) in binary."""
    max_val = max(N, M)
    return max(1, max_val.bit_length())


def _block_window_size(line_len, block_len, b_idx, clue_list):
    """
    Number of valid sliding-window positions for block b_idx in a line.
    s_min and s_max are computed from eq. (17)-(18) of the paper.
    Returns (s_min, s_max, window_size).
    """
    # s_min for block b (0-indexed)
    s_min = 0
    for i in range(b_idx):
        s_min += clue_list[i] + 1  # block length + mandatory gap

    # s_max for block b (0-indexed)
    # s_max = L - sum(clue[b..end]) - (k - b - 1)  [0-indexed variant]
    remaining_blocks = clue_list[b_idx:]
    k = len(clue_list)
    s_max = line_len - sum(remaining_blocks) - (k - b_idx - 1)

    window_size = max(0, s_max - s_min + 1)
    return s_min, s_max, window_size


def compute_max_block_flags(row_hints, col_hints):
    """
    Maximum number of block-flags needed simultaneously (= max blocks in any line).
    """
    max_blocks = 0
    for hints in row_hints + col_hints:
        if hints == [0]:
            continue
        max_blocks = max(max_blocks, len(hints))
    return max(1, max_blocks)


def compute_max_window_aux(N, M, row_hints, col_hints):
    """
    Maximum number of window-auxiliary qubits needed for any single block
    across all lines/blocks.  These are reused block-by-block (uncomputed
    locally within each block per eq. (23)).
    """
    max_win = 1
    for r, hints in enumerate(row_hints):
        if hints == [0]:
            continue
        for b_idx, blk_len in enumerate(hints):
            _, _, win_size = _block_window_size(M, blk_len, b_idx, hints)
            max_win = max(max_win, win_size)
    for c, hints in enumerate(col_hints):
        if hints == [0]:
            continue
        for b_idx, blk_len in enumerate(hints):
            _, _, win_size = _block_window_size(N, blk_len, b_idx, hints)
            max_win = max(max_win, win_size)
    return max(1, max_win)
