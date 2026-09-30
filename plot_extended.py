"""
Charts for:
1. Multi-run comparison (mean + std-dev error bars) - scheduling_results_multirun.csv
2. Round Robin quantum sensitivity - quantum_sensitivity.csv
"""

import csv
import matplotlib.pyplot as plt

ALGORITHMS = ["FCFS", "SRTF", "Round Robin"]
COLORS = {"FCFS": "#4C72B0", "SRTF": "#DD8452", "Round Robin": "#55A868"}

MULTIRUN_METRICS = [
    ("avg_waiting_time", "Average Waiting Time (ms)"),
    ("avg_turnaround_time", "Average Turnaround Time (ms)"),
    ("avg_response_time", "Average Response Time (ms)"),
]


def load_multirun(path):
    data = {alg: {} for alg in ALGORITHMS}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row["algorithm"]][int(row["num_processes"])] = row
    return data


def plot_multirun_metric(data, metric_key, metric_label, out_path):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    process_counts = sorted({n for alg in data for n in data[alg]})

    for alg in ALGORITHMS:
        means = [float(data[alg][n][f"{metric_key}_mean"]) for n in process_counts]
        stds = [float(data[alg][n][f"{metric_key}_std"]) for n in process_counts]
        ax.errorbar(process_counts, means, yerr=stds, marker="o", capsize=4,
                     label=alg, color=COLORS[alg])

    ax.set_xlabel("Number of Processes")
    ax.set_ylabel(metric_label)
    ax.set_title(f"{metric_label} vs Number of Processes\n(mean \u00b1 1 std dev, 30 runs per point)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def load_quantum_data(path):
    rows = list(csv.DictReader(open(path)))
    process_counts = sorted({int(r["num_processes"]) for r in rows})
    by_n = {n: sorted([r for r in rows if int(r["num_processes"]) == n],
                       key=lambda r: int(r["quantum"])) for n in process_counts}
    return by_n


def plot_quantum_sensitivity(by_n, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    colors = plt.cm.viridis([0.15, 0.5, 0.85])

    for (n, rows), color in zip(by_n.items(), colors):
        quanta = [int(r["quantum"]) for r in rows]
        waiting = [float(r["avg_waiting_time_mean"]) for r in rows]
        response = [float(r["avg_response_time_mean"]) for r in rows]
        axes[0].plot(quanta, waiting, marker="o", label=f"n={n}", color=color)
        axes[1].plot(quanta, response, marker="o", label=f"n={n}", color=color)

    axes[0].set_title("Avg Waiting Time vs Quantum")
    axes[0].set_xlabel("Time Quantum (ms)")
    axes[0].set_ylabel("Average Waiting Time (ms)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].set_title("Avg Response Time vs Quantum")
    axes[1].set_xlabel("Time Quantum (ms)")
    axes[1].set_ylabel("Average Response Time (ms)")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.suptitle("Round Robin: Time Quantum Trade-off (20 runs per point)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    data = load_multirun("scheduling_results_multirun.csv")
    for key, label in MULTIRUN_METRICS:
        out_file = f"chart_multirun_{key}.png"
        plot_multirun_metric(data, key, label, out_file)
        print(f"Saved {out_file}")

    by_n = load_quantum_data("quantum_sensitivity.csv")
    plot_quantum_sensitivity(by_n, "chart_quantum_sensitivity.png")
    print("Saved chart_quantum_sensitivity.png")
