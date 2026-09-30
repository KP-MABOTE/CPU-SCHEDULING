"""
Multi-run statistical experiment.

Runs each process count multiple times with different random seeds
(different workloads each time), then reports the MEAN and STANDARD
DEVIATION for every metric instead of a single-run number. This is
what makes a claim like "SRTF has lower waiting time than FCFS"
statistically defensible rather than an artefact of one random draw.
"""

import csv
import statistics

from cpu_scheduler import (
    generate_processes, fcfs, srtf, round_robin, compute_metrics,
    PROCESS_COUNTS,
)

NUM_RUNS = 30            # independent runs per (algorithm, process count) combination
BASE_SEED = 1000         # each run uses BASE_SEED + run_index as its seed

ALGORITHMS = {
    "FCFS": lambda procs: fcfs(procs),
    "SRTF": lambda procs: srtf(procs),
    "Round Robin": lambda procs: round_robin(procs),
}

METRIC_KEYS = [
    "avg_waiting_time", "avg_turnaround_time", "avg_response_time",
    "cpu_utilization_pct", "throughput",
]


def run_single(alg_name, n, seed):
    processes = generate_processes(n, seed=seed)
    if alg_name == "SRTF":
        results, total_time, idle_time = srtf(processes)
    else:
        fn = fcfs if alg_name == "FCFS" else round_robin
        results, total_time = fn(processes)
        idle_time = 0
    return compute_metrics(results, total_time, idle_time)


def run_multi_experiment():
    rows = []
    for n in PROCESS_COUNTS:
        for alg_name in ALGORITHMS:
            runs = [run_single(alg_name, n, BASE_SEED + r) for r in range(NUM_RUNS)]

            row = {"algorithm": alg_name, "num_processes": n, "num_runs": NUM_RUNS}
            for key in METRIC_KEYS:
                values = [r[key] for r in runs]
                row[f"{key}_mean"] = round(statistics.mean(values), 4)
                row[f"{key}_std"] = round(statistics.stdev(values), 4) if len(values) > 1 else 0.0
            rows.append(row)
    return rows


def save_csv(rows, path):
    fieldnames = ["algorithm", "num_processes", "num_runs"]
    for key in METRIC_KEYS:
        fieldnames += [f"{key}_mean", f"{key}_std"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    rows = run_multi_experiment()
    save_csv(rows, "scheduling_results_multirun.csv")
    print(f"Done. {NUM_RUNS} runs per (algorithm, process count) combination.")
    print("Saved to scheduling_results_multirun.csv")
    for row in rows:
        print(row["algorithm"], row["num_processes"],
              "waiting_mean=", row["avg_waiting_time_mean"],
              "waiting_std=", row["avg_waiting_time_std"])
