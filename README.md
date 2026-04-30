# Grover Nonogram Solver

A quantum computing approach to solving [Nonogram](https://en.wikipedia.org/wiki/Nonogram) puzzles using **Grover's search algorithm**. The oracle encodes both arithmetic (row/column sum) and geometric (block contiguity) constraints, enabling the quantum circuit to amplify valid puzzle solutions from an exponential search space.

---

## Repository Structure

```
Grover_Nanogram_Solver/
├── main.py                # CLI entry-point (argparse)
├── configs/               # Puzzle definitions in JSON
│   └── 3x3_cross.json
├── src/
│   ├── __init__.py
│   ├── primitives.py      # Low-level quantum gates
│   ├── utils.py           # Pure math helpers (no Qiskit)
│   ├── arithmetic.py      # Sum-check subroutine
│   ├── geometry.py        # Contiguity-check subroutine
│   ├── oracle.py          # Full Grover oracle (orchestrator)
│   ├── grover.py          # Diffuser, iteration calc, circuit runner
│   ├── classical.py       # Brute-force solver (no Qiskit)
│   └── visualization.py   # Plotting and metrics charts
└── reference_code.py      # Original monolithic implementation
```

## Module Overview

### `src/primitives.py`
Lowest-level quantum gate building blocks with **zero nonogram knowledge**:
- `maj_gate` / `uma_gate` — MAJ and UMA gates for the Cuccaro ripple-carry adder.
- `generic_ripple_adder` — In-place addition of two quantum registers.
- `compare_static` — Flips a flag qubit iff a register encodes a specific integer.

### `src/utils.py`
Pure utility functions — **no Qiskit dependency**, easy to unit-test:
- `get_accumulator_size(N, M)` — Bits needed to represent `max(N, M)`.
- `_block_window_size(...)` — Valid sliding-window positions for a block (eqs. 17–18).
- `compute_max_block_flags(...)` — Max per-block flags needed across all lines.
- `compute_max_window_aux(...)` — Max window-auxiliary qubits needed.

### `src/arithmetic.py`
Arithmetic subroutine — depends on `primitives`, knows nothing about geometry:
- `create_adder_gate(acc_size)` — Reusable Cuccaro adder gate factory.
- `apply_sum_check_for_line(...)` — Compute–check–uncompute: flips a flag iff the sum of line qubits equals the target value.

### `src/geometry.py`
Geometric subroutine — sliding-window and contiguity verification:
- `apply_window_check_for_block(...)` — Per-block sliding-window operator (eq. 23) with De Morgan OR and uncomputation.
- `apply_order_check_for_line(...)` — Full contiguity check for one line (eq. 25): runs all block checks, ANDs the results, then uncomputes.

### `src/oracle.py`
Oracle orchestrator — composes arithmetic + geometry into the full Grover oracle:
- `create_nxm_oracle(N, M, row_hints, col_hints)` — Builds a `QuantumCircuit` gate encoding all row/column sum and contiguity constraints with proper compute–kickback–uncompute structure.

### `src/grover.py`
Grover's algorithm layer — depends on the oracle but is agnostic to its internals:
- `create_diffuser(num_qubits)` — Standard diffusion operator `D = 2|s⟩⟨s| − I`.
- `compute_grover_iterations(N, M, num_solutions)` — Optimal iteration count: `⌊(π/4)√(2^(NM)/M)⌋`.
- `run_grover(N, M, row_hints, col_hints, grover_iters, shots)` — Builds the full circuit, transpiles, runs on `AerSimulator` (MPS method), and returns counts + depth metrics.

### `src/classical.py`
Classical brute-force solver — **completely independent of Qiskit**:
- `brute_force_solutions(N, M, row_hints, col_hints)` — Enumerates all `2^(N×M)` configurations and returns valid solution bitstrings.
- `_check_contiguity_classical(segment, clue_list)` — Greedy block-matching for classical validation.

### `src/visualization.py`
Plotting utilities:
- `plot_and_save(...)` — Measurement histogram with correct solutions highlighted in green.
- `plot_summary_metrics(...)` — Side-by-side bar charts for qubit counts and circuit depths across configurations.

### `configs/`
Puzzle definitions as JSON files. Example (`3x3_cross.json`):
```json
{
    "name": "3x3_cross",
    "N": 3,
    "M": 3,
    "row_hints": [[2], [1], [2]],
    "col_hints": [[1], [3], [1]]
}
```

---

## Dependency Graph

```
primitives ← arithmetic ← oracle ← grover ← main
    utils  ← geometry   ←────┘                 ↑
 classical ─────────────────────────────────────┘
visualization ──────────────────────────────────┘
```

> `utils` and `classical` have **no Qiskit dependency** and can be tested without any quantum libraries installed.

---

## Installation

### Requirements
- Python 3.9+
- [Qiskit](https://qiskit.org/)
- [Qiskit Aer](https://github.com/Qiskit/qiskit-aer)
- Matplotlib

### Setup

Create and activate a virtual environment, then install dependencies:

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# Linux / macOS:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

All dependencies are listed in [`requirements.txt`](requirements.txt).

## Usage

### Run the default puzzle suite

Loads all JSON configs from the `configs/` directory:

```bash
python main.py
```

### Run a specific puzzle

```bash
python main.py --config configs/3x3_cross.json
```

### Run all puzzles in a directory

```bash
python main.py --config-dir configs/
```

### Full options

```bash
python main.py --help
```

```
usage: main.py [-h] [--config CONFIG] [--config-dir CONFIG_DIR]
               [--output OUTPUT] [--shots SHOTS] [--iterations ITERATIONS]

Grover Nonogram Solver — solve nonogram puzzles using Grover's algorithm.

options:
  -h, --help                show this help message and exit
  --config, -c CONFIG       Path to a single puzzle JSON config file.
  --config-dir, -d DIR      Path to a directory of puzzle JSON config files.
  --output, -o OUTPUT       Output directory for plots and metrics (default: results/).
  --shots, -s SHOTS         Number of measurement shots (default: 2048).
  --iterations, -i ITERS    Number of Grover iterations: "auto" to compute
                            optimally, or an integer (default: auto).
```

### Overriding Grover iterations

By default, the optimal iteration count is computed automatically from the number of brute-force solutions. You can override it with a fixed number:

```bash
# Auto (default) — computes ⌊(π/4)√(2^(NM)/M)⌋
python main.py --config configs/3x3_cross.json --iterations auto

# Fixed — use exactly 3 iterations
python main.py --config configs/3x3_cross.json --iterations 3
```

### Adding new puzzles

Create a JSON file in `configs/` following this schema:

```json
{
    "name": "descriptive_name",
    "N": <number_of_rows>,
    "M": <number_of_columns>,
    "row_hints": [[...], [...], ...],
    "col_hints": [[...], [...], ...]
}
```

- Use `[0]` for empty lines (no filled cells).
- Each hint sublist contains the block lengths for that row/column, in order.

### Example output

```
====================================================================================================
Config                              Qubits    Depth   Depth2Q  Iters    GT TopState            Correct?
====================================================================================================
3x3_r[2][1][2]_c[1][3][1]              21      583      1764      4     2 011010110                  ✓
====================================================================================================

=== SUMMARY ===
Correct               : 1
Incorrect             : 0
No GT (0 solutions)   : 0
Execution errors      : 0

Plots saved to: results/
```

---

## How It Works

1. **Superposition** — All `N×M` input qubits are placed in equal superposition via Hadamard gates.
2. **Oracle** — For each Grover iteration, the oracle marks valid solutions by:
   - **Sum check (Vsum):** Verifying that each row and column has the correct number of filled cells using Cuccaro ripple-carry adders.
   - **Order check (Vorder):** Verifying that filled cells form contiguous blocks in the correct order using sliding-window operators with De Morgan OR logic.
3. **Diffuser** — The standard Grover diffusion operator amplifies the amplitude of marked states.
4. **Measurement** — After the optimal number of iterations, the input qubits are measured, yielding the solution with high probability.

---

## License

See [LICENSE](LICENSE) for details.