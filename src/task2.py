import os
import sys
import time
import random

# Import my_system() from task1 (must be in the same directory)
from task1 import my_system

DEFAULT_NUM_CHILDREN = 10


def get_num_children():
    """Parse optional CLI argument for number of children (default 10)."""
    if len(sys.argv) == 1:
        return DEFAULT_NUM_CHILDREN
    if len(sys.argv) == 2:
        try:
            n = int(sys.argv[1])
            if n < 1:
                raise ValueError("must be a positive integer")
            return n
        except ValueError as e:
            print(f"ERROR: invalid argument: {e}")
            sys.exit(1)
    print(
        f"ERROR: too many arguments. "
        f"Usage: python3 {sys.argv[0]} [num_children]"
    )
    sys.exit(1)


def report_exit(idx, wpid, status):
    """Print the reason a child process was removed from memory."""
    if os.WIFEXITED(status):
        code = os.WEXITSTATUS(status)
        if code == 0:
            print(f"  Child {idx} (PID={wpid}): normal exit with code 0")
        else:
            print(f"  Child {idx} (PID={wpid}): error exit with code {code}")
    elif os.WIFSIGNALED(status):
        print(
            f"  Child {idx} (PID={wpid}): "
            f"terminated by signal {os.WTERMSIG(status)}"
        )
    else:
        print(
            f"  Child {idx} (PID={wpid}): "
            f"unknown termination status {status}"
        )


def create_children(num_children):
    """
    Fork num_children child processes.
    Each child generates a random float in [0, 1):
      >= 0.5 -> exits normally (code 0)
      <  0.5 -> enters an infinite loop
    Returns a list of (child_index, pid) for the parent.
    """
    child_pids = []

    for i in range(num_children):
        try:
            pid = os.fork()
        except OSError as e:
            print(f"ERROR: fork() failed for child {i + 1}: {e}")
            continue

        if pid == 0:
            # --- CHILD PROCESS ---
            num = random.random()
            print(
                f"  Child {i + 1} (PID={os.getpid()}): "
                f"generated {num:.4f}",
                flush=True,
            )
            if num >= 0.5:
                print(
                    f"  Child {i + 1} (PID={os.getpid()}): "
                    f"finished successfully",
                    flush=True,
                )
                os._exit(0)
            else:
                print(
                    f"  Child {i + 1} (PID={os.getpid()}): "
                    f"entering infinite loop",
                    flush=True,
                )
                while True:
                    time.sleep(1)
        else:
            # --- PARENT PROCESS ---
            child_pids.append((i + 1, pid))

    return child_pids


def reap_finished(child_pids):
    """
    Non-blocking reap of all children that have already finished.
    Returns a list of (index, pid) entries that are still running.
    """
    still_running = []

    for idx, cpid in child_pids:
        try:
            wpid, status = os.waitpid(cpid, os.WNOHANG)
            if wpid == 0:
                # Child has not finished yet
                still_running.append((idx, cpid))
            else:
                report_exit(idx, wpid, status)
        except ChildProcessError:
            # Child already gone (should not happen here, but handle it)
            pass

    return still_running


def kill_and_reap(still_running):
    """
    Send SIGTERM to every still-running child via my_system(),
    then wait for each one and report its termination reason.
    """
    for idx, cpid in still_running:
        cmd = f"kill {cpid}"
        print(f"  Sending SIGTERM to child {idx} (PID={cpid}): '{cmd}'")
        ret = my_system(cmd)
        if ret != 0:
            print(
                f"  WARNING: kill command returned "
                f"{os.waitstatus_to_exitcode(ret)}"
            )

    for idx, cpid in still_running:
        try:
            wpid, status = os.waitpid(cpid, 0)
            report_exit(idx, wpid, status)
        except ChildProcessError:
            print(f"  Child {idx} (PID={cpid}): already gone before waitpid")


def _main():
    num_children = get_num_children()

    print(f"=== Starting: creating {num_children} child process(es) ===")
    print(f"Parent PID={os.getpid()}")
    my_system(f"ps --ppid {os.getpid()} --no-headers 2>/dev/null "
              f"|| echo '  (no children yet)'")

    child_pids = create_children(num_children)

    # --- Phase 1: sleep 3s, then reap finished children ---
    print("\nParent: all children created, sleeping 3 seconds...")
    time.sleep(3)

    print("\nParent: reaping finished children...")
    still_running = reap_finished(child_pids)

    if still_running:
        print(f"\nParent: {len(still_running)} child(ren) still running:")
        for idx, cpid in still_running:
            print(f"  Child {idx} (PID={cpid})")
        my_system(
            f"ps --ppid {os.getpid()} --no-headers 2>/dev/null"
        )
    else:
        print("\nParent: all children have already finished.")

    # --- Phase 2: sleep 5s, then kill remaining ---
    if still_running:
        print("\nParent: sleeping 5 more seconds before killing survivors...")
        time.sleep(5)

        print("\nParent: killing and reaping remaining children...")
        kill_and_reap(still_running)

    print("\n=== Parent: all done ===")
    my_system(f"ps --ppid {os.getpid()} --no-headers 2>/dev/null "
              f"|| echo '  (no children remaining)'")


if __name__ == "__main__":
    _main()
