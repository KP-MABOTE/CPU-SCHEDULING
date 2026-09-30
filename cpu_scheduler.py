"""
CPU Scheduling Simulator
CMPG324 - Operating Systems
Compares FCFS, SRTF, and Round Robin scheduling algorithms
for an audio-and-video system with multiple processes.

Author: (fill in your name/student number)
"""

import random
import copy
import csv
import statistics

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RANDOM_SEED = 42          # fixed seed so results are reproducible for the report
ARRIVAL_MAX_GAP = 4       # max random gap (ms) between one process arriving and the next
BURST_MIN, BURST_MAX = 1, 20       # burst time range (ms)
PRIORITY_MIN, PRIORITY_MAX = 1, 10  # lower number = higher priority
TIME_QUANTUM = 4          # fixed system time quantum used for Round Robin
                           # (RR needs ONE system-wide quantum, not a per-process
                           # value, so per-process "time quantum" from the brief
                           # is generated but not used by the algorithm itself -
                           # see note in generate_processes())

PROCESS_COUNTS = [10, 20, 30, 40, 50]


# ---------------------------------------------------------------------------
# Process generation
# ---------------------------------------------------------------------------
def generate_processes(n, seed=RANDOM_SEED):
    """
    Create n processes with randomised parameters as specified in the brief:
    Process ID, Arrival time (random incremental), Burst time (random),
    Priority (random), Time quantum (random).

    NOTE: a per-process time quantum does not fit how Round Robin works
    (RR uses one shared system quantum so every process gets a fair,
    equal turn). We still generate a random quantum value per process,
    per the brief, but only report/store it - the RR algorithm itself
    uses TIME_QUANTUM. Explain this assumption in your report's
    methodology section.
    """
    rng = random.Random(seed)
    processes = []
    arrival = 0
    for i in range(1, n + 1):
        arrival += rng.randint(0, ARRIVAL_MAX_GAP)
        processes.append({
            "pid": i,
            "arrival_time": arrival,
            "burst_time": rng.randint(BURST_MIN, BURST_MAX),
            "priority": rng.randint(PRIORITY_MIN, PRIORITY_MAX),
            "time_quantum": rng.randint(2, 6),
        })
    return processes


# ---------------------------------------------------------------------------
# FCFS - First Come First Served (non-preemptive)
# ---------------------------------------------------------------------------
def fcfs(processes):
    procs = sorted(copy.deepcopy(processes), key=lambda p: (p["arrival_time"], p["pid"]))
    time = 0
    results = []
    for p in procs:
        start = max(time, p["arrival_time"])
        completion = start + p["burst_time"]
        waiting = start - p["arrival_time"]
        turnaround = completion - p["arrival_time"]
        response = waiting  # first (and only) time it runs
        results.append({**p, "start": start, "completion": completion,
                         "waiting_time": waiting, "turnaround_time": turnaround,
                         "response_time": response})
        time = completion
    return results, time


# ---------------------------------------------------------------------------
# SRTF - Shortest Remaining Time First (preemptive)
# ---------------------------------------------------------------------------
def srtf(processes):
    procs = copy.deepcopy(processes)
    for p in procs:
        p["remaining"] = p["burst_time"]
        p["first_run"] = None
        p["completion"] = None

    n = len(procs)
    completed = 0
    time = min(p["arrival_time"] for p in procs)
    idle_time = 0

    while completed < n:
        available = [p for p in procs if p["arrival_time"] <= time and p["remaining"] > 0]
        if not available:
            idle_time += 1
            time += 1
            continue

        current = min(available, key=lambda p: (p["remaining"], p["arrival_time"], p["pid"]))
        if current["first_run"] is None:
            current["first_run"] = time

        current["remaining"] -= 1
        time += 1

        if current["remaining"] == 0:
            current["completion"] = time
            completed += 1

    results = []
    for p in procs:
        waiting = (p["completion"] - p["arrival_time"]) - p["burst_time"]
        turnaround = p["completion"] - p["arrival_time"]
        response = p["first_run"] - p["arrival_time"]
        results.append({**p, "waiting_time": waiting, "turnaround_time": turnaround,
                         "response_time": response})
    return results, time, idle_time


# ---------------------------------------------------------------------------
# Round Robin (preemptive, fixed system quantum)
# ---------------------------------------------------------------------------
def round_robin(processes, quantum=TIME_QUANTUM):
    procs = copy.deepcopy(processes)
    for p in procs:
        p["remaining"] = p["burst_time"]
        p["first_run"] = None
        p["completion"] = None

    procs_by_arrival = sorted(procs, key=lambda p: (p["arrival_time"], p["pid"]))
    queue = []
    time = procs_by_arrival[0]["arrival_time"]
    not_arrived = list(procs_by_arrival)
    idle_time = 0

    # seed the queue with anything that has already arrived
    while not_arrived and not_arrived[0]["arrival_time"] <= time:
        queue.append(not_arrived.pop(0))

    completed = 0
    n = len(procs)

    while completed < n:
        if not queue:
            if not_arrived:
                time = not_arrived[0]["arrival_time"]
                while not_arrived and not_arrived[0]["arrival_time"] <= time:
                    queue.append(not_arrived.pop(0))
                continue
            else:
                break

        current = queue.pop(0)
        if current["first_run"] is None:
            current["first_run"] = time

        run_for = min(quantum, current["remaining"])
        time += run_for
        current["remaining"] -= run_for

        # any process that arrived during this slice joins the back of the queue
        while not_arrived and not_arrived[0]["arrival_time"] <= time:
            queue.append(not_arrived.pop(0))

        if current["remaining"] > 0:
            queue.append(current)
        else:
            current["completion"] = time
            completed += 1

    results = []
    for p in procs:
        waiting = (p["completion"] - p["arrival_time"]) - p["burst_time"]
        turnaround = p["completion"] - p["arrival_time"]
        response = p["first_run"] - p["arrival_time"]
        results.append({**p, "waiting_time": waiting, "turnaround_time": turnaround,
                         "response_time": response})
    return results, time


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def compute_metrics(results, total_time, idle_time=0):
    """Utilisation and throughput are measured the same way for every algorithm:
    busy time = sum of burst times; span = finish time - first arrival.
    (idle_time is kept as a parameter for backward compatibility but is no longer needed.)"""
    n = len(results)
    start = min(p["arrival_time"] for p in results)
    span = total_time - start
    busy = sum(p["burst_time"] for p in results)
    return {
        "num_processes": n,
        "avg_waiting_time": round(statistics.mean(p["waiting_time"] for p in results), 3),
        "avg_turnaround_time": round(statistics.mean(p["turnaround_time"] for p in results), 3),
        "avg_response_time": round(statistics.mean(p["response_time"] for p in results), 3),
        "cpu_utilization_pct": round(busy / span * 100 if span > 0 else 0, 3),
        "throughput": round(n / span if span > 0 else 0, 5),
    }


# ---------------------------------------------------------------------------
# Experiment runner
# ---------------------------------------------------------------------------
def run_experiments():
    all_rows = []
    for n in PROCESS_COUNTS:
        processes = generate_processes(n)

        fcfs_results, fcfs_time = fcfs(processes)
        fcfs_metrics = compute_metrics(fcfs_results, fcfs_time, idle_time=0)
        fcfs_metrics["algorithm"] = "FCFS"
        all_rows.append(fcfs_metrics)

        srtf_results, srtf_time, srtf_idle = srtf(processes)
        srtf_metrics = compute_metrics(srtf_results, srtf_time, idle_time=srtf_idle)
        srtf_metrics["algorithm"] = "SRTF"
        all_rows.append(srtf_metrics)

        rr_results, rr_time = round_robin(processes)
        rr_metrics = compute_metrics(rr_results, rr_time, idle_time=0)
        rr_metrics["algorithm"] = "Round Robin"
        all_rows.append(rr_metrics)

    return all_rows


def save_csv(rows, path):
    fieldnames = ["algorithm", "num_processes", "avg_waiting_time",
                  "avg_turnaround_time", "avg_response_time",
                  "cpu_utilization_pct", "throughput"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fieldnames})


if __name__ == "__main__":
    results = run_experiments()
    save_csv(results, "scheduling_results.csv")
    print(f"Done. {len(results)} rows written to scheduling_results.csv")
    for r in results:
        print(r)
