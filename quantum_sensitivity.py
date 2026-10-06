"""
Round Robin time-quantum sensitivity analysis.

The brief doesn't ask for this, but it's a natural and well-known
extension: RR's performance depends heavily on the quantum size.
Too small -> excessive context-switch overhead (in a real OS; our
simulator models it via waiting/response time degrading toward pure
time-slicing overhead). Too large -> RR degrades toward FCFS.

We run RR at several quantum values, for multiple process counts,
each averaged over several random workloads, and report waiting
time and response time so the trade-off can be shown and discussed.
"""

import csv
import statistics

from cpu_scheduler import generate_processes, round_robin, compute_metrics

QUANTUM_VALUES = [1, 2, 4, 8, 16, 32]
PROCESS_COUNTS_FOR_SENSITIVITY = [10, 30, 50]   # small / medium / large workload
NUM_RUNS = 20
BASE_SEED = 5000


def run_quantum_sensitivity():
    rows = []
    for n in PROCESS_COUNTS_FOR_SENSITIVITY:
        for q in QUANTUM_VALUES:
            waiting_runs, turnaround_runs, response_runs = [], [], []
            for r in range(NUM_RUNS):
                processes = generate_processes(n, seed=BASE_SEED + r)
                results, total_time = round_robin(processes, quantum=q)
                metrics = compute_metrics(results, total_time, idle_time=0)
                waiting_runs.append(metrics["avg_waiting_time"])
                turnaround_runs.append(metrics["avg_turnaround_time"])
                response_runs.append(metrics["avg_response_time"])

            rows.append({
                "num_processes": n,
                "quantum": q,
                "num_runs": NUM_RUNS,
                "avg_waiting_time_mean": round(statistics.mean(waiting_runs), 4),
                "avg_turnaround_time_mean": round(statistics.mean(turnaround_runs), 4),
                "avg_response_time_mean": round(statistics.mean(response_runs), 4),
            })
    return rows


def save_csv(rows, path):
    fieldnames = ["num_processes", "quantum", "num_runs", "avg_waiting_time_mean",
                  "avg_turnaround_time_mean", "avg_response_time_mean"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    from paths import csv_path
    rows = run_quantum_sensitivity()
    out = csv_path("quantum_sensitivity.csv")
    save_csv(rows, out)
    print("Saved to", out)
    for row in rows:
        print(row)
