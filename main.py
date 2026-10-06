"""main.py - menu-driven front end for the CPU scheduling simulator."""
from cpu_scheduler import generate_processes
from sim_extended import ALGOS, prepare, simulate
import re
from gantt_sim import timeline_to_segments, plot_gantt
from paths import csv_path, chart_path, gantt_path

CORE = ["FCFS", "SRTF", "Round Robin (q=4)"]
settings = {"io": False, "switch": 0}       # 'realistic' mode toggles these
workload = []


def ask_int(msg, lo=0, hi=10**6):
    while True:
        try:
            v = int(input(msg))
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        print(f"  Please enter a whole number between {lo} and {hi}.")


def create_random():
    n = ask_int("Number of processes (10-50 recommended): ", 1, 500)
    seed = ask_int("Seed (same seed = same workload): ", 0)
    return generate_processes(n, seed)


def create_manual():
    procs = []
    for i in range(1, ask_int("How many processes? ", 1, 100) + 1):
        print(f"Process {i}")
        procs.append({"pid": i,
                      "arrival_time": ask_int("  arrival time (ms): ", 0),
                      "burst_time": ask_int("  burst time (ms): ", 1),
                      "priority": ask_int("  priority (1 = highest): ", 1),
                      "time_quantum": ask_int("  time quantum (ms): ", 1)})
    return procs


def show_workload():
    print(f"{'PID':>4}{'Arrival':>9}{'Burst':>7}{'Prio':>6}{'Quantum':>9}")
    for p in workload:
        print(f"{p['pid']:>4}{p['arrival_time']:>9}{p['burst_time']:>7}{p['priority']:>6}{p['time_quantum']:>9}")


def run(name):
    procs = prepare(workload, settings["io"], 0)
    return simulate(procs, switch_cost=settings["switch"], **ALGOS[name])


def summary(name, r):
    print(f"{name:20s} wait {r['avg_waiting']:8.2f}  turn {r['avg_turnaround']:8.2f}  "
          f"resp {r['avg_response']:7.2f}  util {r['utilisation']:6.2f}%  thr {r['throughput']:.4f}/ms")

def gantt_file(name, n):
    slug = re.sub(r"\W+", "_", name.lower()).strip("_")
    return gantt_path(f"gantt_{slug}_{n}procs.png")

def run_one():
    names = list(ALGOS)
    for i, nm in enumerate(names, 1):
        print(f"  {i}. {nm}")
    name = names[ask_int("Choose algorithm: ", 1, len(names)) - 1]
    r = run(name)
    print(f"{'PID':>4}{'Waiting':>9}{'Turnaround':>12}{'Response':>10}")
    for x in r["per_process"]:
        print(f"{x['pid']:>4}{x['waiting']:>9}{x['turnaround']:>12}{x['response']:>10}")
    summary(name, r)
    out = gantt_file(name, len(workload))
    plot_gantt(timeline_to_segments(r["timeline"], r["t0"]), f"{name} - {len(workload)} processes", out)
    print("Gantt chart saved to", out)


def compare():
    for name in CORE:
        r = run(name)
        summary(name, r)
        plot_gantt(timeline_to_segments(r["timeline"], r["t0"]),
                    f"{name} - {len(workload)} processes", gantt_file(name, len(workload)))
    print("Gantt charts saved to results/gantt/")


def full_experiment():
    import multi_run_experiment as m
    import plot_extended as pe
    rows = m.run_multi_experiment()
    out = csv_path("scheduling_results_multirun.csv")
    m.save_csv(rows, out)
    data = pe.load_multirun(out)
    for key, label in pe.MULTIRUN_METRICS:
        pe.plot_multirun_metric(data, key, label, chart_path(f"chart_multirun_{key}.png"))
    print("30-run experiment done. CSV saved to results/csv/, charts to results/charts/.")


MENU = """
=== CPU Scheduling Simulator ===
1. Create random workload      4. Compare FCFS / SRTF / RR
2. Enter workload manually     5. Run full 10-50 experiment (30 runs)
3. Run one algorithm + Gantt   6. Toggle realistic mode (I/O + 1 ms switch)
7. Show workload               0. Exit
"""

if __name__ == "__main__":
    while True:
        print(MENU)
        c = input("Choice: ").strip()
        if c == "0":
            break
        elif c == "1":
            workload = create_random(); show_workload()
        elif c == "2":
            workload = create_manual()
        elif c == "5":
            full_experiment()
        elif c == "6":
            realistic = not settings["io"]
            settings.update(io=realistic, switch=1 if realistic else 0)
            print("Realistic mode:", "ON" if realistic else "OFF")
        elif c in {"3", "4", "7"}:
            if not workload:
                print("Create a workload first (option 1 or 2).")
            else:
                {"3": run_one, "4": compare, "7": show_workload}[c]()
        else:
            print("Invalid choice.")