"""
Unit tests: verify FCFS, SRTF, and Round Robin against a hand-calculated
worked example. This proves the simulator's core logic is correct,
independent of the random process generator.

Worked example (5 processes):
    PID  Arrival  Burst
    P1   0        5
    P2   1        3
    P3   2        8
    P4   3        6
    P5   4        4

Expected results below were derived by manually tracing each algorithm
step-by-step (see accompanying report appendix for the full working).
Round Robin uses quantum = 4 (the simulator's default TIME_QUANTUM).
"""

from cpu_scheduler import fcfs, srtf, round_robin

TEST_PROCESSES = [
    {"pid": 1, "arrival_time": 0, "burst_time": 5, "priority": 1, "time_quantum": 4},
    {"pid": 2, "arrival_time": 1, "burst_time": 3, "priority": 1, "time_quantum": 4},
    {"pid": 3, "arrival_time": 2, "burst_time": 8, "priority": 1, "time_quantum": 4},
    {"pid": 4, "arrival_time": 3, "burst_time": 6, "priority": 1, "time_quantum": 4},
    {"pid": 5, "arrival_time": 4, "burst_time": 4, "priority": 1, "time_quantum": 4},
]

# Hand-calculated expected values: {pid: (waiting, turnaround, response)}
EXPECTED_FCFS = {
    1: (0, 5, 0),
    2: (4, 7, 4),
    3: (6, 14, 6),
    4: (13, 19, 13),
    5: (18, 22, 18),
}

EXPECTED_SRTF = {
    1: (3, 8, 0),
    2: (0, 3, 0),
    3: (16, 24, 16),
    4: (9, 15, 9),
    5: (4, 8, 4),
}

EXPECTED_RR_Q4 = {
    1: (15, 20, 0),
    2: (3, 6, 3),
    3: (14, 22, 5),
    4: (17, 23, 8),
    5: (11, 15, 11),
}


def check(results, expected, label):
    by_pid = {p["pid"]: p for p in results}
    failures = []
    for pid, (exp_wait, exp_turn, exp_resp) in expected.items():
        p = by_pid[pid]
        if (p["waiting_time"], p["turnaround_time"], p["response_time"]) != (exp_wait, exp_turn, exp_resp):
            failures.append(
                f"  PID {pid}: expected (wait={exp_wait}, turn={exp_turn}, resp={exp_resp}), "
                f"got (wait={p['waiting_time']}, turn={p['turnaround_time']}, resp={p['response_time']})"
            )
    if failures:
        print(f"[FAIL] {label}")
        for f in failures:
            print(f)
        return False
    else:
        print(f"[PASS] {label} — matches hand-calculated values for all {len(expected)} processes")
        return True


def run_all_tests():
    results_fcfs, _ = fcfs(TEST_PROCESSES)
    results_srtf, _, _ = srtf(TEST_PROCESSES)
    results_rr, _ = round_robin(TEST_PROCESSES, quantum=4)

    all_passed = True
    all_passed &= check(results_fcfs, EXPECTED_FCFS, "FCFS")
    all_passed &= check(results_srtf, EXPECTED_SRTF, "SRTF")
    all_passed &= check(results_rr, EXPECTED_RR_Q4, "Round Robin (quantum=4)")

    print()
    print("ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")
    return all_passed


def test_fcfs():
    results, _ = fcfs(TEST_PROCESSES)
    assert check(results, EXPECTED_FCFS, "FCFS")

def test_srtf():
    results, _, _ = srtf(TEST_PROCESSES)
    assert check(results, EXPECTED_SRTF, "SRTF")

def test_round_robin():
    results, _ = round_robin(TEST_PROCESSES, quantum=4)
    assert check(results, EXPECTED_RR_Q4, "Round Robin (q=4)")

def test_extended_simulator_matches():
    from sim_extended import validate
    assert validate()
    
if __name__ == "__main__":
    run_all_tests()
