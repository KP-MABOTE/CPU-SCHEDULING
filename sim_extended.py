"""
Extended CPU scheduling simulator (CMPG324).

Adds, on top of cpu_scheduler.py:
  * Process states: Ready, Running, Blocked (I/O bursts), plus Done
  * Preemptive Priority scheduling, with optional aging (anti-starvation)
  * Round Robin with a fixed quantum OR each process's own random quantum
  * Context-switch overhead (milliseconds)
  * Worst-case waiting time (starvation indicator)
  * A user-facing command line: create workloads, choose algorithm, draw a Gantt chart

One tick = 1 millisecond. Lower priority number = higher priority.
With no I/O and no switch cost it reproduces the hand-checked results (see validate()).
"""
import argparse, random
from statistics import mean
from cpu_scheduler import generate_processes

ALGOS = {
    "FCFS": dict(policy="FCFS"),
    "SRTF": dict(policy="SRTF"),
    "Round Robin (q=4)": dict(policy="RR", quantum=4),
    "Round Robin (random q)": dict(policy="RR", per_process_q=True),
    "Priority (preemptive)": dict(policy="PRIO"),
    "Priority + aging": dict(policy="PRIO", aging=10),
}

def prepare(processes, io=False, seed=0):
    """Attach a burst list [cpu, io, cpu, ...]. With io=True a process splits its CPU burst
    around one random 2-8 ms I/O wait (the Blocked state)."""
    rng, out = random.Random(seed + 7), []
    for p in processes:
        q, b = dict(p), p["burst_time"]
        q["bursts"] = [b // 2, rng.randint(2, 8), b - b // 2] if (io and b >= 2) else [b]
        out.append(q)
    return out

def simulate(procs, policy, quantum=4, per_process_q=False, aging=None, switch_cost=0):
    P = [dict(pid=p["pid"], arr=p["arrival_time"], prio=p["priority"], q=p["time_quantum"], bursts=p["bursts"],
              i=0, rem=p["bursts"][0], state="new", first=None, done=None, wait=0, waited=0, seq=0, io_end=0, boost=0)
         for p in procs]
    n, seq, cur, last, used, useful, finished = len(P), 0, None, None, 0, 0, 0
    sw_left, sw_to, ready, timeline = 0, None, [], []
    t = t0 = min(p["arr"] for p in P)

    def enq(p):                       # process enters the Ready queue
        nonlocal seq
        seq += 1; p["seq"] = seq; p["state"] = "ready"; ready.append(p)

    while finished < n:
        for p in P:                   # arrivals, and processes whose I/O has finished (Blocked -> Ready)
            if p["state"] == "new" and p["arr"] <= t: enq(p)
            elif p["state"] == "blocked" and p["io_end"] <= t:
                p["i"] += 1; p["rem"] = p["bursts"][p["i"]]; enq(p)
        if cur is not None and cur["state"] == "expired":     # Round Robin slice used up
            enq(cur); cur = None

        if sw_to is None:             # ---- scheduler decision ----
            cands = ready + ([cur] if cur else [])
            if not cands:
                timeline.append(-1); t += 1; last = None; continue      # CPU idle
            if policy in ("FCFS", "RR"):
                pick = cur if cur else min(ready, key=lambda p: p["seq"])
            elif policy == "SRTF":
                pick = min(cands, key=lambda p: (p["rem"], p["arr"], p["pid"]))
            else:
                eff = lambda p: p["prio"] - ((p["boost"] if p is cur else p["waited"] // aging) if aging else 0)   # a dispatched process keeps its aging boost
                pick = min(cands, key=lambda p: (eff(p), p["seq"]))
            if pick is not cur:
                if cur: enq(cur)                                        # Running -> Ready (preempted)
                ready.remove(pick); cur = None
                if switch_cost > 0 and last is not None and last != pick["pid"]:
                    sw_to, sw_left, pick["state"] = pick, switch_cost, "switching"
                else:
                    cur, pick["state"], used = pick, "running", 0; pick["boost"] = pick["waited"] // aging if aging else 0

        if sw_to is not None:         # ---- context-switch overhead tick (no useful work) ----
            for p in ready: p["wait"] += 1; p["waited"] += 1
            sw_to["wait"] += 1
            timeline.append(0); t += 1; sw_left -= 1
            if sw_left == 0:
                cur, sw_to = sw_to, None; cur["state"], used = "running", 0; cur["boost"] = cur["waited"] // aging if aging else 0
            continue

        timeline.append(cur["pid"])   # ---- run the chosen process for 1 ms ----
        if cur["first"] is None: cur["first"] = t
        cur["rem"] -= 1; useful += 1; last = cur["pid"]; cur["waited"] = 0
        for p in ready: p["wait"] += 1; p["waited"] += 1
        t += 1
        if cur["rem"] == 0:
            if cur["i"] == len(cur["bursts"]) - 1:
                cur["state"], cur["done"] = "done", t; finished += 1     # Running -> Done
            else:
                cur["i"] += 1; cur["io_end"] = t + cur["bursts"][cur["i"]]; cur["state"] = "blocked"  # -> Blocked
            cur = None
        elif policy == "RR":
            used += 1
            if used >= (cur["q"] if per_process_q else quantum): cur["state"] = "expired"

    span = t - t0
    per = [dict(pid=p["pid"], waiting=p["wait"], turnaround=p["done"] - p["arr"], response=p["first"] - p["arr"]) for p in P]
    return dict(per_process=per, timeline=timeline, t0=t0, makespan=span,
                avg_waiting=mean(x["waiting"] for x in per), avg_turnaround=mean(x["turnaround"] for x in per),
                avg_response=mean(x["response"] for x in per), max_waiting=max(x["waiting"] for x in per),
                max_response=max(x["response"] for x in per),
                low_prio_wait=mean([w["wait"] for w in P if w["prio"] >= 8] or [x["waiting"] for x in per]),   # starvation indicator: lowest-priority processes
                utilisation=useful / span * 100, throughput=n / span)

def validate():
    """Compare against the hand-calculated worked example (same values as test_scheduler.py)."""
    from test_scheduler import TEST_PROCESSES, EXPECTED_FCFS, EXPECTED_SRTF, EXPECTED_RR_Q4
    procs, ok = prepare(TEST_PROCESSES), True
    for name, exp in [("FCFS", EXPECTED_FCFS), ("SRTF", EXPECTED_SRTF), ("Round Robin (q=4)", EXPECTED_RR_Q4)]:
        r = simulate(procs, **ALGOS[name])
        got = {x["pid"]: (x["waiting"], x["turnaround"], x["response"]) for x in r["per_process"]}
        good = got == exp; ok &= good
        print(f"[{'PASS' if good else 'FAIL'}] extended simulator matches hand calculation: {name}")
    return ok

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CPU scheduling simulator")
    ap.add_argument("--n", type=int, default=10, help="number of processes")
    ap.add_argument("--algo", default="SRTF", choices=list(ALGOS))
    ap.add_argument("--io", action="store_true", help="give processes an I/O wait (Blocked state)")
    ap.add_argument("--switch", type=int, default=0, help="context-switch cost in ms")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    r = simulate(prepare(generate_processes(a.n, a.seed), a.io, a.seed), switch_cost=a.switch, **ALGOS[a.algo])
    for k in ("avg_waiting", "avg_turnaround", "avg_response", "max_waiting", "utilisation", "throughput"):
        print(f"{k:16s}{r[k]:.3f}")
