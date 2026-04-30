"""
Classical brute-force solver for nonograms.
Completely independent of Qiskit — easy to test in isolation.
"""


def _check_contiguity_classical(segment, clue_list):
    """
    Checks that 'segment' (list of 0/1) satisfies 'clue_list'
    (list of block lengths) in order with at least one gap between blocks.
    Returns True iff the constraint is satisfied.
    """
    if clue_list == [0]:
        return sum(segment) == 0  # entire line must be empty
    # Try to match blocks in order using the sliding-window logic
    pos = 0
    for b_idx, blk_len in enumerate(clue_list):
        # Find the first valid position for this block starting from pos
        found = False
        s_min_b = pos
        # s_max: leave room for remaining blocks
        remaining = clue_list[b_idx + 1:]
        s_max_b = len(segment) - blk_len - sum(remaining) - len(remaining)
        for w in range(s_min_b, s_max_b + 1):
            if all(segment[w + j] == 1 for j in range(blk_len)):
                # Check right neighbor emptiness (if not last block)
                right_ok = (b_idx == len(clue_list) - 1) or \
                           (w + blk_len < len(segment) and segment[w + blk_len] == 0)
                # Check left neighbor emptiness (if not first block)
                left_ok = (b_idx == 0) or (w > 0 and segment[w - 1] == 0)
                if left_ok and right_ok:
                    pos = w + blk_len + 1  # next block must start after the gap
                    found = True
                    break
        if not found:
            return False
    # Ensure no extra filled cells exist (sum already verified by oracle)
    return True


def brute_force_solutions(N, M, row_hints, col_hints):
    """Finds all valid nonogram solutions by brute force."""
    num_cells = N * M
    solutions = []

    for bits in range(2 ** num_cells):
        grid = [(bits >> i) & 1 for i in range(num_cells)]
        valid = True

        for r in range(N):
            row    = grid[r * M:(r + 1) * M]
            hints  = row_hints[r]
            target = sum(hints)
            if sum(row) != target:
                valid = False
                break
            if hints != [0] and not _check_contiguity_classical(row, hints):
                valid = False
                break
        if not valid:
            continue

        for c in range(M):
            col   = [grid[r * M + c] for r in range(N)]
            hints = col_hints[c]
            target = sum(hints)
            if sum(col) != target:
                valid = False
                break
            if hints != [0] and not _check_contiguity_classical(col, hints):
                valid = False
                break

        if valid:
            # Qiskit measures MSB-first; grid[0] is qubit 0 (LSB) → reverse
            bit_str = ''.join(str(grid[i]) for i in reversed(range(num_cells)))
            solutions.append(bit_str)

    return solutions
