"""Gantt chart for ANY workload, built from sim_extended.simulate()['timeline'].
Grey = CPU idle, black = context switch."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def timeline_to_segments(timeline, t0=0):
    segs, start = [], 0
    for i in range(1, len(timeline) + 1):
        if i == len(timeline) or timeline[i] != timeline[start]:
            segs.append((timeline[start], t0 + start, t0 + i))
            start = i
    return segs


def plot_gantt(segs, title, out_path):
    pids = sorted({p for p, _, _ in segs if p > 0})
    cmap = plt.get_cmap("tab20")
    colour = {pid: cmap(i % 20) for i, pid in enumerate(pids)}
    fig, ax = plt.subplots(figsize=(14, 2.8))
    for pid, s, e in segs:
        face = "#DDDDDD" if pid == -1 else "black" if pid == 0 else colour[pid]
        ax.broken_barh([(s, e - s)], (0, 1), facecolors=face, edgecolor="white", linewidth=0.5)
        if pid > 0 and e - s >= 2:
            ax.text((s + e) / 2, 0.5, f"P{pid}", ha="center", va="center", fontsize=7, color="white")
    ax.set_xlim(segs[0][1], segs[-1][2])
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Time (ms)")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)