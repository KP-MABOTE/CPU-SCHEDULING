"""
Gantt chart generator.

Produces a visual execution timeline (who runs when) for each of the
three algorithms, using the same small worked example as
test_scheduler.py. This makes the preemption behaviour of SRTF and
Round Robin visible and concrete, rather than only summarised as
averages.
"""

import matplotlib.pyplot as plt
import matplotlib.cm as cm

from test_scheduler import TEST_PROCESSES

PROC_COLORS = {
    1: "#4C72B0", 2: "#DD8452", 3: "#55A868", 4: "#C44E52", 5: "#8172B2",
}


# ---------------------------------------------------------------------------
# Instrumented copies of the scheduling logic that additionally record
# every (pid, start, end) execution segment, for plotting.
# ---------------------------------------------------------------------------
def fcfs_segments(processes):
    procs = sorted(processes, key=lambda p: (p["arrival_time"], p["pid"]))
    time = 0
    segments = []
    for p in procs:
        start = max(time, p["arrival_time"])
        end = start + p["burst_time"]
        segments.append((p["pid"], start, end))
        time = end
    return segments


def srtf_segments(processes):
    import copy
    procs = copy.deepcopy(processes)
    for p in procs:
        p["remaining"] = p["burst_time"]

    n = len(procs)
    completed = 0
    time = min(p["arrival_time"] for p in procs)
    segments = []
    current_pid = None
    seg_start = None

    while completed < n:
        available = [p for p in procs if p["arrival_time"] <= time and p["remaining"] > 0]
        if not available:
            time += 1
            continue
        chosen = min(available, key=lambda p: (p["remaining"], p["arrival_time"], p["pid"]))

        if chosen["pid"] != current_pid:
            if current_pid is not None:
                segments.append((current_pid, seg_start, time))
            current_pid = chosen["pid"]
            seg_start = time

        chosen["remaining"] -= 1
        time += 1
        if chosen["remaining"] == 0:
            completed += 1

    segments.append((current_pid, seg_start, time))
    return segments


def rr_segments(processes, quantum=4):
    import copy
    procs = copy.deepcopy(processes)
    for p in procs:
        p["remaining"] = p["burst_time"]

    procs_by_arrival = sorted(procs, key=lambda p: (p["arrival_time"], p["pid"]))
    queue = []
    time = procs_by_arrival[0]["arrival_time"]
    not_arrived = list(procs_by_arrival)
    segments = []

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
        run_for = min(quantum, current["remaining"])
        seg_start = time
        time += run_for
        current["remaining"] -= run_for
        segments.append((current["pid"], seg_start, time))

        while not_arrived and not_arrived[0]["arrival_time"] <= time:
            queue.append(not_arrived.pop(0))

        if current["remaining"] > 0:
            queue.append(current)
        else:
            completed += 1

    return segments


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
BG, INK = "#F6F2EA", "#1E2340"


def plot_gantt(segments, title, out_path):
    fig, ax = plt.subplots(figsize=(10, 2.2), facecolor=BG)
    ax.set_facecolor(BG)

    for pid, start, end in segments:
        ax.broken_barh([(start, end - start)], (0, 1),
                        facecolors=PROC_COLORS.get(pid, "#999999"), edgecolor="black")
        ax.text((start + end) / 2, 0.5, f"P{pid}", ha="center", va="center",
                color="white", fontweight="bold", fontsize=9)

    max_time = max(end for _, _, end in segments)
    ax.set_xlim(0, max_time)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Time (ms)", color=INK)
    ax.set_xticks(range(0, max_time + 1, max(1, max_time // 20)))
    ax.tick_params(colors=INK)
    for spine in ax.spines.values(): spine.set_color("#C9C2AE")
    ax.set_title(title, color=INK)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fcfs_segs = fcfs_segments(TEST_PROCESSES)
    srtf_segs = srtf_segments(TEST_PROCESSES)
    rr_segs = rr_segments(TEST_PROCESSES, quantum=4)

    plot_gantt(fcfs_segs, "FCFS Execution Timeline (5-process worked example)", "gantt_fcfs.png")
    plot_gantt(srtf_segs, "SRTF Execution Timeline (5-process worked example)", "gantt_srtf.png")
    plot_gantt(rr_segs, "Round Robin (quantum=4) Execution Timeline (5-process worked example)", "gantt_rr.png")
    print("Saved gantt_fcfs.png, gantt_srtf.png, gantt_rr.png")
