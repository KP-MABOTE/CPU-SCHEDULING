# CPU Scheduling Simulator

A CPU scheduling simulator built for comparing how different scheduling algorithms perform for an audio-and-video
processing system, where a bad scheduling decision means an audible or visible glitch, not just a slow response.

## What this project does

We implemented and compared five CPU scheduling algorithms in Python:

| Algorithm | Type | What it does |
|---|---|---|
| **FCFS** | Non-preemptive | Runs processes strictly in arrival order |
| **SRTF** | Preemptive | Always runs whichever process has the least time left |
| **Round Robin** | Preemptive | Gives every process a short, equal turn, then cycles |
| **Priority** | Preemptive | Always runs the highest-priority process |
| **Priority + Aging** | Preemptive | Priority scheduling, but a process's priority rises the longer it waits |

Each algorithm was tested on randomly generated workloads of 10–50
processes, repeated 30 times per test for statistical reliability, and
measured against five standard metrics: waiting time, turnaround time,
response time, CPU utilisation, and throughput.

We then went further than a purely theoretical comparison and modelled
realistic conditions; input/output waits (the "Blocked" process state) and
the cost of switching between processes — to see whether the theoretical
best algorithm still wins once those real-world costs are included.

## Key findings

- **SRTF** gives the lowest average waiting and turnaround time, but can
  starve long-running processes if short ones keep arriving.
- **Round Robin** gives the fastest, most predictable response time, making
  it the strongest fit for a live audio/video system at the cost of a
  higher average wait.
- **Priority scheduling risks severe starvation** without aging; adding
  aging fixes the worst case but costs some average performance.
- **Once input/output waits and switching costs are modelled**, CPU
  utilisation stops being a tie between algorithms Round Robin loses the
  most efficiency to its frequent switching.




