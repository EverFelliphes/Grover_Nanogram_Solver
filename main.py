"""
CLI entry-point for the Grover Nonogram Solver.
Supports running a single puzzle from a JSON config file,
all configs in a directory, or the default configs/ folder.
"""

import argparse
import json
import os
import glob
import traceback

from src.classical import brute_force_solutions
from src.grover import compute_grover_iterations, run_grover
from src.visualization import plot_and_save, plot_summary_metrics


def load_config(path):
    """Load a puzzle configuration from a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['N'], data['M'], data['row_hints'], data['col_hints']


def load_all_configs(config_dir):
    """Load all JSON puzzle configs from a directory."""
    configs = []
    for path in sorted(glob.glob(os.path.join(config_dir, '*.json'))):
        try:
            configs.append(load_config(path))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [WARN] Skipping {path}: {e}")
    return configs


def run_pipeline(configs, output_dir, shots, iterations='auto'):
    """Run the full Grover pipeline for a list of (N, M, row_hints, col_hints) configs."""
    os.makedirs(output_dir, exist_ok=True)
    all_metrics = []

    print("=" * 100)
    print(f"{'Config':<35} {'Qubits':>7} {'Depth':>8} {'Depth2Q':>9} "
          f"{'Iters':>6} {'GT':>5} {'TopState':<18} {'Correct?':>9}")
    print("=" * 100)

    for (N, M, row_hints, col_hints) in configs:
        rh_str  = ''.join(str(h) for h in row_hints)
        ch_str  = ''.join(str(h) for h in col_hints)
        label   = f"{N}x{M}_r{rh_str}_c{ch_str}"

        gt_solutions = brute_force_solutions(N, M, row_hints, col_hints)
        num_solutions = max(1, len(gt_solutions))
        if iterations == 'auto':
            grover_iters = compute_grover_iterations(N, M, num_solutions)
        else:
            grover_iters = int(iterations)

        try:
            result = run_grover(N, M, row_hints, col_hints, grover_iters, shots=shots)
            counts       = result['counts']
            n_qubits     = result['n_qubits']
            depth_orig   = result['depth_original']
            depth_2q     = result['depth_2q']

            top_state  = max(counts, key=counts.get)
            is_correct = (top_state in gt_solutions) if gt_solutions else None

            plot_and_save(label, counts, set(gt_solutions), output_dir)

            status   = '✓' if is_correct else ('✗' if is_correct is False else 'N/A')
            gt_count = len(gt_solutions)

            print(f"{label:<35} {n_qubits:>7} {depth_orig:>8} {depth_2q:>9} "
                  f"{grover_iters:>6} {gt_count:>5} {top_state:<18} {status:>9}")

            all_metrics.append({
                'label':          label,
                'N': N, 'M': M,
                'row_hints':      row_hints,
                'col_hints':      col_hints,
                'grover_iters':   grover_iters,
                'n_qubits':       n_qubits,
                'depth_original': depth_orig,
                'depth_2q':       depth_2q,
                'gt_solutions':   gt_solutions,
                'top_state':      top_state,
                'top_count':      counts[top_state],
                'total_shots':    sum(counts.values()),
                'is_correct':     is_correct,
            })

        except Exception as e:
            print(f"{label:<35}  ERROR: {e}")
            traceback.print_exc()
            all_metrics.append({'label': label, 'error': str(e)})

    print("=" * 100)

    # Summary
    correct   = sum(1 for m in all_metrics if m.get('is_correct') is True)
    incorrect = sum(1 for m in all_metrics if m.get('is_correct') is False)
    no_gt     = sum(1 for m in all_metrics if m.get('is_correct') is None and 'error' not in m)
    errors    = sum(1 for m in all_metrics if 'error' in m)
    print(f"\n=== SUMMARY ===")
    print(f"Correct               : {correct}")
    print(f"Incorrect             : {incorrect}")
    print(f"No GT (0 solutions)   : {no_gt}")
    print(f"Execution errors      : {errors}")
    print(f"\nPlots saved to: {output_dir}/")

    # Summary metrics chart
    summary_path = plot_summary_metrics(all_metrics, output_dir)
    if summary_path:
        print(f"Summary metrics chart saved to: {summary_path}")

    return all_metrics


def main():
    parser = argparse.ArgumentParser(
        description='Grover Nonogram Solver — solve nonogram puzzles using Grover\'s algorithm.'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        default=None,
        help='Path to a single puzzle JSON config file.'
    )
    parser.add_argument(
        '--config-dir', '-d',
        type=str,
        default=None,
        help='Path to a directory of puzzle JSON config files (runs all).'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='results',
        help='Output directory for plots and metrics (default: results/).'
    )
    parser.add_argument(
        '--shots', '-s',
        type=int,
        default=2048,
        help='Number of measurement shots (default: 2048).'
    )
    parser.add_argument(
        '--iterations', '-i',
        type=str,
        default='auto',
        help='Number of Grover iterations: "auto" to compute optimally, or an integer (default: auto).'
    )

    args = parser.parse_args()

    # Determine configs to run
    if args.config:
        configs = [load_config(args.config)]
    elif args.config_dir:
        configs = load_all_configs(args.config_dir)
        if not configs:
            print(f"No valid configs found in {args.config_dir}/")
            return
    else:
        # Default: load all configs from the configs/ directory
        default_dir = os.path.join(os.path.dirname(__file__), 'configs')
        if os.path.isdir(default_dir):
            configs = load_all_configs(default_dir)
        else:
            print("No config specified and configs/ directory not found.")
            print("Usage: python main.py --config puzzle.json")
            return

    run_pipeline(configs, args.output, args.shots, args.iterations)


if __name__ == '__main__':
    main()
