"""Runs the extended experiments (30 runs per point) and draws the comparison charts.
Scenario 'ideal'    : no I/O, no context-switch cost (matches the main comparison).
Scenario 'realistic': every process does I/O (Blocked state) and each context switch costs 1 ms."""
import csv, statistics as st
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from cpu_scheduler import generate_processes, PROCESS_COUNTS
from sim_extended import ALGOS, prepare, simulate, validate
from paths import csv_path, chart_path

NUM_RUNS, BASE_SEED = 30, 1000
SCEN = {"ideal": dict(io=False, switch=0), "realistic": dict(io=True, switch=1)}
KEYS = ["avg_waiting", "avg_turnaround", "avg_response", "max_waiting", "max_response", "low_prio_wait", "utilisation", "throughput"]

def run():
    rows = []
    for scen, cfg in SCEN.items():
        for n in PROCESS_COUNTS:
            for name, opts in ALGOS.items():
                runs = [simulate(prepare(generate_processes(n, BASE_SEED + r), cfg["io"], BASE_SEED + r),
                                 switch_cost=cfg["switch"], **opts) for r in range(NUM_RUNS)]
                row = dict(scenario=scen, algorithm=name, num_processes=n, num_runs=NUM_RUNS)
                for k in KEYS:
                    v = [x[k] for x in runs]
                    row[k + "_mean"], row[k + "_std"] = round(st.mean(v), 4), round(st.stdev(v), 4)
                rows.append(row)
    with open(csv_path("extended_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows

BG, FG = "#F6F2EA", "#1E2340"
STYLE = {"FCFS": ("#14A38B", "-"), "SRTF": ("#EF5B3C", "-"), "Round Robin (q=4)": ("#5B4BDB", "-"),
         "Round Robin (random q)": ("#9C8FF0", "--"), "Priority (preemptive)": ("#F2B134", "-"), "Priority + aging": ("#8A5A00", "--")}

def chart(rows, scen, key, label, out, algos=None):
    fig, ax = plt.subplots(figsize=(7.6, 5), facecolor=BG); ax.set_facecolor(BG)
    for name in (algos or ALGOS):
        r = [x for x in rows if x["scenario"] == scen and x["algorithm"] == name]
        col, ls = STYLE[name]
        ax.plot([x["num_processes"] for x in r], [x[key + "_mean"] for x in r], marker="o", lw=3, ls=ls, color=col, label=name)
    ax.set_xlabel("Number of processes", color=FG); ax.set_ylabel(label, color=FG); ax.tick_params(colors=FG)
    [s.set_color(FG) for s in ax.spines.values()]; ax.grid(alpha=.2, color=FG)
    ax.legend(facecolor=BG, labelcolor=FG, edgecolor="none", fontsize=10)
    fig.tight_layout(); fig.savefig(chart_path(out), dpi=150, facecolor=BG); plt.close(fig)

if __name__ == "__main__":
    assert validate(), "validation failed"
    rows = run()
    chart(rows, "ideal", "avg_waiting", "Average waiting time (milliseconds)", "chart_ext_ideal_waiting.png")
    chart(rows, "ideal", "max_response", "Worst-case response time (milliseconds)", "chart_ext_ideal_maxresp.png",
          ["FCFS", "SRTF", "Round Robin (q=4)", "Priority (preemptive)", "Priority + aging"])
    chart(rows, "ideal", "low_prio_wait", "Avg waiting time, lowest-priority processes (milliseconds)", "chart_ext_ideal_lowprio.png",
          ["Priority (preemptive)", "Priority + aging"])
    chart(rows, "realistic", "utilisation", "CPU utilisation (%)", "chart_ext_real_util.png")
    chart(rows, "realistic", "avg_waiting", "Average waiting time (milliseconds)", "chart_ext_real_waiting.png")
    for scen in SCEN:
        print("\n==", scen, "n=50 (means)")
        for r in [x for x in rows if x["scenario"] == scen and x["num_processes"] == 50]:
            print(f"{r['algorithm']:24s} wait {r['avg_waiting_mean']:7.1f}  turn {r['avg_turnaround_mean']:7.1f}  resp {r['avg_response_mean']:6.1f}"
                  f"  maxresp {r['max_response_mean']:6.1f}  lowprio {r['low_prio_wait_mean']:7.1f}  util {r['utilisation_mean']:6.2f}  thr {r['throughput_mean']:.4f}")
