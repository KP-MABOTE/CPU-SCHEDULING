"""
Generates comparison charts from scheduling_results.csv
for the Results and Analysis section of the report.
"""

import csv
import matplotlib.pyplot as plt

METRICS = [
    ("avg_waiting_time", "Average Waiting Time (ms)"),
    ("avg_turnaround_time", "Average Turnaround Time (ms)"),
    ("avg_response_time", "Average Response Time (ms)"),
    ("cpu_utilization_pct", "CPU Utilisation (%)"),
    ("throughput", "Throughput (processes/ms)"),
]

ALGORITHMS = ["FCFS", "SRTF", "Round Robin"]
COLORS = {"FCFS": "#4C72B0", "SRTF": "#DD8452", "Round Robin": "#55A868"}


def load_data(path):
    data = {alg: {} for alg in ALGORITHMS}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            alg = row["algorithm"]
            n = int(row["num_processes"])
            data[alg][n] = row
    return data


def plot_metric(data, metric_key, metric_label, out_path):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    process_counts = sorted({n for alg in data for n in data[alg]})

    for alg in ALGORITHMS:
        y = [float(data[alg][n][metric_key]) for n in process_counts]
        ax.plot(process_counts, y, marker="o", label=alg, color=COLORS[alg])

    ax.set_xlabel("Number of Processes")
    ax.set_ylabel(metric_label)
    ax.set_title(f"{metric_label} vs Number of Processes")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    data = load_data("scheduling_results.csv")
    for key, label in METRICS:
        out_file = f"chart_{key}.png"
        plot_metric(data, key, label, out_file)
        print(f"Saved {out_file}")
