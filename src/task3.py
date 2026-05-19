import os
import sys

# prog1.py must reside in the same directory as this file
PROG1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prog1.py")


def parse_args():
    """
    Parse required CLI arguments: n (number of intervals) and num (trials).
    Usage: python3 task3.py <n> <num>
    """
    if len(sys.argv) != 3:
        print(
            f"Usage: python3 {sys.argv[0]} <n> <num>\n"
            f"  n   - number of equal sub-intervals of [0, 1]\n"
            f"  num - number of random trials per sub-interval (NUM env var)"
        )
        sys.exit(1)
    try:
        n = int(sys.argv[1])
        num = int(sys.argv[2])
        if n < 1:
            raise ValueError("n must be a positive integer")
        if num < 1:
            raise ValueError("num must be a positive integer")
        return n, num
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def build_intervals(n):
    """
    Split [0, 1] into n equal sub-intervals.
    Returns a list of (a, b) tuples with full float precision.
    """
    return [(i / n, (i + 1) / n) for i in range(n)]


def launch_children(intervals, env):
    """
    Fork one child per interval. Each child replaces itself with
    prog1.py via execve(), passing its [a, b] as argv and the
    prepared environment (which contains NUM).

    Returns a list of (interval_index, a, b, child_pid).
    """
    child_pids = []

    for i, (a, b) in enumerate(intervals):
        try:
            pid = os.fork()
        except OSError as e:
            print(f"ERROR: fork() failed for child {i + 1}: {e}")
            continue

        if pid == 0:
            # --- CHILD PROCESS ---
            # Replace this process image with prog1.py
            try:
                args = [sys.executable, PROG1, str(a), str(b)]
                os.execve(sys.executable, args, env)
            except OSError as e:
                print(
                    f"ERROR: execve() failed for child {i + 1}: {e}",
                    file=sys.stderr,
                )
                os._exit(127)
        else:
            # --- PARENT PROCESS ---
            child_pids.append((i + 1, a, b, pid))

    return child_pids


def wait_and_collect(child_pids, num):
    """
    Wait for every child to finish (blocking).
    Decode exit status and print results per child.
    """
    print("\n--- Results ---")
    for idx, a, b, cpid in child_pids:
        try:
            wpid, status = os.waitpid(cpid, 0)
        except ChildProcessError:
            print(
                f"  Interval {idx} [{a:.6f}, {b:.6f}]: "
                f"ERROR - child already gone"
            )
            continue

        if os.WIFEXITED(status):
            hits = os.WEXITSTATUS(status)
            expected = (b - a) * num
            print(
                f"  Interval {idx} [{a:.4f}, {b:.4f}]: "
                f"{hits:>3} hit(s) out of {num} "
                f"(expected ~{expected:.1f})"
            )
        elif os.WIFSIGNALED(status):
            print(
                f"  Interval {idx} [{a:.4f}, {b:.4f}]: "
                f"child (PID={wpid}) killed by signal "
                f"{os.WTERMSIG(status)}"
            )
        else:
            print(
                f"  Interval {idx} [{a:.4f}, {b:.4f}]: "
                f"unknown termination status {status}"
            )


def _main():
    n, num = parse_args()

    print("=== Task 3: Uniformity check of the PRNG ===")
    print(f"Parent PID={os.getpid()}")
    print(f"Splitting [0, 1] into {n} equal interval(s), {num} trial(s) each")

    intervals = build_intervals(n)

    # Pass NUM to children via environment
    env = os.environ.copy()
    env["NUM"] = str(num)

    print(f"\nLaunching {n} child process(es)...")
    child_pids = launch_children(intervals, env)

    if not child_pids:
        print("ERROR: no children were created. Exiting.")
        sys.exit(1)

    print(f"Waiting for {len(child_pids)} child(ren) to finish...")
    wait_and_collect(child_pids, num)

    print("\n=== Done ===")


if __name__ == "__main__":
    _main()
