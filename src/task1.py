import os
import sys


def my_system(cmd=""):
    """
    Simplified analogue of the standard system() function.
    Runs a shell command using fork(), execve(), and waitpid().
    Returns the raw wait status (same as os.system()).
    Returns 0 for an empty command, -1 if fork() fails.
    """
    if not cmd:
        return 0

    try:
        pid = os.fork()
    except OSError as e:
        print(f"ERROR: fork() failed: {e}")
        return -1

    if pid == 0:
        # Child process: replace itself with /bin/sh -c <cmd>
        try:
            os.execve("/bin/sh", ["/bin/sh", "-c", cmd], os.environ.copy())
        except OSError as e:
            print(f"ERROR: execve() failed: {e}")
            os._exit(127)
    else:
        # Parent process: wait for the child to finish
        _, status = os.waitpid(pid, 0)
        return status


def _main():
    commands = ["date", "cp", "ls -la", "nonexistentcommand123"]

    if len(sys.argv) == 2:
        cmd = sys.argv[1]
        print(f"[user:]> my_system('{cmd}')")
        status = my_system(cmd)
        print(f"\tExit status (raw):  {status}")
        print(f"\tExit code:          {os.waitstatus_to_exitcode(status)}")
    else:
        # Demo mode: run all built-in test commands
        for cmd in commands:
            print(f"\n[user:]> my_system('{cmd}')")
            status = my_system(cmd)
            print(f"\tExit status (raw):  {status}")
            print(f"\tExit code:          {os.waitstatus_to_exitcode(status)}")


if __name__ == "__main__":
    _main()
