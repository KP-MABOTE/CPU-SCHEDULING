"""Paired significance tests across the 30 runs (same seeds for every algorithm)."""
import csv
import statistics as st
from scipy import stats
from cpu_scheduler import PROCESS_COUNTS
from multi_run_experiment import run_single, NUM_RUNS, BASE_SEED

METRICS = ["avg_waiting_time", "avg_turnaround_time", "avg_response_time",
           "cpu_utilization_pct", "throughput"]
PAIRS = [("FCFS", "SRTF"), ("FCFS", "Round Robin"), ("SRTF", "Round Robin")]


def compare(x, y):
    d = [a - b for a, b in zip(x, y)]
    if all(v == 0 for v in d):
        return 0.0, 0.0, 0.0, 1.0, 1.0
    mean_d = st.mean(d)
    lo, hi = stats.t.interval(0.95, len(d) - 1, loc=mean_d, scale=stats.sem(d))
    p_t = stats.ttest_rel(x, y).pvalue
    p_w = stats.wilcoxon(x, y).pvalue
    return mean_d, lo, hi, p_t, p_w


if __name__ == "__main__":
    rows = []
    for n in PROCESS_COUNTS:
        runs = {a: [run_single(a, n, BASE_SEED + r) for r in range(NUM_RUNS)]
                for a in ("FCFS", "SRTF", "Round Robin")}
        for m in METRICS:
            for a, b in PAIRS:
                md, lo, hi, pt, pw = compare([r[m] for r in runs[a]], [r[m] for r in runs[b]])
                rows.append(dict(n=n, metric=m, A=a, B=b, mean_diff_A_minus_B=round(md, 4),
                                 ci95_low=round(lo, 4), ci95_high=round(hi, 4),
                                 p_ttest=round(pt, 6), p_wilcoxon=round(pw, 6),
                                 significant=pt < 0.05))
    from paths import csv_path
    with open(csv_path("analysis_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("Saved", csv_path("analysis_results.csv"))