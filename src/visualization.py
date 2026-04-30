"""
Visualization utilities: measurement histograms and summary metric charts.
"""

import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def plot_and_save(config_label, counts, solutions_gt, output_dir):
    """
    Plot a histogram of measurement counts, highlighting correct solutions in green.

    Parameters
    ----------
    config_label  : str — label for this puzzle configuration
    counts        : dict — {bitstring: count} from Qiskit
    solutions_gt  : set of str — ground-truth solution bitstrings
    output_dir    : str — directory to save the PNG
    """
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_n  = min(16, len(sorted_counts))
    labels = [x[0] for x in sorted_counts[:top_n]]
    values = [x[1] for x in sorted_counts[:top_n]]
    colors = ['#2ecc71' if lbl in solutions_gt else '#3498db' for lbl in labels]

    fig, ax = plt.subplots(figsize=(max(8, top_n * 0.7), 5))
    ax.bar(range(top_n), values, color=colors, edgecolor='black', linewidth=0.5)
    ax.set_xticks(range(top_n))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.set_xlabel('Measured State (bitstring)')
    ax.set_ylabel('Count')
    ax.set_title(f'Measurement Distribution — {config_label}\n'
                 f'(Green = Correct Solution, Blue = Incorrect)')
    legend_elements = [Patch(facecolor='#2ecc71', label='Correct Solution'),
                       Patch(facecolor='#3498db', label='Incorrect State')]
    ax.legend(handles=legend_elements, loc='upper right')
    plt.tight_layout()
    filename = os.path.join(output_dir, f'{config_label}.png')
    plt.savefig(filename, dpi=150)
    plt.close()
    return filename


def plot_summary_metrics(all_metrics, output_dir):
    """
    Plot qubit counts and circuit depths across all valid configurations.

    Parameters
    ----------
    all_metrics : list of dict — one entry per puzzle run
    output_dir  : str — directory to save the summary PNG
    """
    valid = [m for m in all_metrics if 'error' not in m and 'n_qubits' in m]
    if not valid:
        return None

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    x = range(len(valid))
    labels_plot  = [m['label'] for m in valid]
    qubits_plot  = [m['n_qubits'] for m in valid]
    depth_orig_p = [m['depth_original'] for m in valid]
    depth_2q_p   = [m['depth_2q'] for m in valid]

    axes[0].bar(x, qubits_plot, color='#9b59b6', edgecolor='black', linewidth=0.5)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels_plot, rotation=45, ha='right', fontsize=7)
    axes[0].set_ylabel('Number of Qubits')
    axes[0].set_title('Qubits Used per Configuration')

    axes[1].bar([xi - 0.2 for xi in x], depth_orig_p, width=0.4,
                label='Original Depth', color='#e67e22', edgecolor='black', linewidth=0.5)
    axes[1].bar([xi + 0.2 for xi in x], depth_2q_p,   width=0.4,
                label='2Q Depth (transpiled)', color='#c0392b', edgecolor='black', linewidth=0.5)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels_plot, rotation=45, ha='right', fontsize=7)
    axes[1].set_ylabel('Circuit Depth')
    axes[1].set_title('Depth per Configuration')
    axes[1].legend()

    plt.tight_layout()
    summary_path = os.path.join(output_dir, 'summary_metrics.png')
    plt.savefig(summary_path, dpi=150)
    plt.close()
    return summary_path
