# Operating Systems Lab 4 - Working With Processes

## About Project

This project was created for Operating Systems Laboratory Work #4, "Working
with Processes". The laboratory work focuses on practical work with Linux
processes using Python and low-level operating-system calls.

The purpose of the lab is to understand how processes are created, how a new
program is started inside an existing process, how a parent waits for child
processes, how child termination is analyzed, and how simple information can be
passed between parent and child processes.

The assignment covers these process-management topics:

- creating a new process with `fork()`;
- replacing a process image with another program through the `exec()` family;
- waiting for process completion with `wait()` and `waitpid()`;
- collecting child processes so they do not remain as zombies;
- checking whether a process exited normally or was killed by a signal;
- passing data from parent to child through command-line arguments;
- passing data from parent to child through environment variables;
- returning a small numeric result from child to parent through the exit code;
- observing child processes with commands such as `ps`;
- terminating still-running processes with `kill`.

The laboratory assignment contains three tasks.

Task 1 asks to implement a custom `my_system()` function. It is a simplified
analog of the standard `system()` function. The function must run shell commands
by explicitly creating a child process, executing a shell in that child, and
waiting for the child from the parent:

1. parent calls `fork()`;
2. child calls an `exec()`-family function;
3. child becomes `/bin/sh -c <command>`;
4. parent calls `waitpid()`;
5. parent receives the raw termination status.

Task 2 asks to create a process-management demonstration. The program creates a
chosen number of child processes. The number is an optional command-line
argument, and the default is `10`. Every child generates a random number in the
range `[0, 1)`. If the number is greater than or equal to `0.5`, the child exits
successfully with code `0`. If the number is less than `0.5`, the child enters
an infinite loop. The parent waits, reaps children that finished naturally,
shows which children are still alive, then terminates and reaps the remaining
children.

Task 3 asks to research simple parent-child communication. The assignment
describes two programs:

- Program 0 divides the interval `[0, 1]` into `n` equal sub-intervals, sets the
  environment variable `NUM`, creates `n` children, starts Program 1 in each
  child, waits for all children, and prints the result returned by every child.
- Program 1 receives two interval bounds `a` and `b` through command-line
  arguments, receives the number of trials through the `NUM` environment
  variable, generates random values, counts how many fall into `[a, b]`, and
  returns that count through its process exit code.

The current repository implements Task 3 with two files:

- `src/task3.py` is Program 0, the parent/controller;
- `src/prog1.py` is Program 1, the child worker.

This structure follows the lab idea directly. `task3.py` creates child
processes with `fork()`, each child replaces itself with `prog1.py` through
`execve()`, and the parent collects the result from each child with
`waitpid()` and `WEXITSTATUS`.

The project uses only Python standard library modules. It is intended for Linux
or a Unix-like system because it depends on POSIX process APIs such as
`os.fork()`, `os.execve()`, `os.waitpid()`, and signal-based process
termination.

## About Code

The project currently contains four source files:

```text
lab4_CS12_KhalinIhor/
|-- README.md
`-- src/
    |-- task1.py
    |-- task2.py
    |-- task3.py
    `-- prog1.py
```

Runtime code uses only standard Python modules:

- `os`: process creation, program execution, waiting, environment handling,
  process IDs, process-status helpers, and filesystem path construction;
- `sys`: command-line arguments, stderr output, Python executable path, and
  exiting with status codes;
- `time`: sleeping in child loops and parent waiting phases;
- `random`: generating pseudo-random floating-point values.

There are no pytest files in the current project. The lab PDF says that pytest
testing is not mandatory for this work and that manual testing is acceptable.
The project can be checked with `flake8`.

### Source File: `src/task1.py`

`src/task1.py` implements Task 1: a simplified custom replacement for
`system()`.

Main function:

```python
my_system(cmd="")
```

Demo entry point:

```python
_main()
```

`my_system()` receives a command string. If the string is empty, it returns `0`.
Otherwise, it forks the current process.

After `fork()`, there are two execution paths:

- child process path: `pid == 0`;
- parent process path: `pid` contains the child process ID.

In the child process, the code runs:

```python
os.execve("/bin/sh", ["/bin/sh", "-c", cmd], os.environ.copy())
```

This replaces the child Python process with `/bin/sh`. The shell receives the
`-c` option and the command string. The child also receives a copy of the
current environment.

In the parent process, the code runs:

```python
_, status = os.waitpid(pid, 0)
return status
```

The parent blocks until the specific child finishes. The returned value is the
raw wait status, the same kind of status that `os.system()` returns.

The demo mode converts this raw status to a more familiar exit code:

```python
os.waitstatus_to_exitcode(status)
```

Built-in demo commands:

```text
date
cp
ls -la
nonexistentcommand123
```

Usage examples:

```bash
python3 src/task1.py
python3 src/task1.py "date"
python3 src/task1.py "ls -la"
python3 src/task1.py "echo hello"
python3 src/task1.py "nonexistentcommand123"
```

### Source File: `src/task2.py`

`src/task2.py` implements Task 2: creating, observing, terminating, and reaping
child processes.

Main constant:

```python
DEFAULT_NUM_CHILDREN = 10
```

Main functions:

```python
get_num_children()
report_exit(idx, wpid, status)
create_children(num_children)
reap_finished(child_pids)
kill_and_reap(still_running)
_main()
```

The file imports the custom command runner from Task 1:

```python
from task1 import my_system
```

`get_num_children()` parses the optional command-line argument. It supports:

- no argument: use `10`;
- one positive integer argument: use that value;
- invalid value: print an error and exit with code `1`;
- too many arguments: print usage and exit with code `1`.

`create_children(num_children)` creates children in a loop. For every child:

1. the parent calls `os.fork()`;
2. the child generates a random number with `random.random()`;
3. if the number is at least `0.5`, the child exits with `os._exit(0)`;
4. if the number is below `0.5`, the child enters an infinite loop with
   `time.sleep(1)`;
5. the parent stores `(child_index, pid)` in a list.

The infinite loop is intentional. It creates children that remain alive until
the parent kills them. This makes it possible to demonstrate process monitoring
and signal termination.

`reap_finished(child_pids)` checks all known children with non-blocking
`waitpid()`:

```python
wpid, status = os.waitpid(cpid, os.WNOHANG)
```

If `wpid == 0`, the child is still running. If `wpid` is a real PID, the child
has finished and the parent can decode its status. The function returns a list
of children that are still running.

`report_exit(idx, wpid, status)` explains why a child finished:

- normal exit with code `0`;
- error exit with nonzero code;
- termination by signal;
- unknown termination status.

It uses POSIX status helpers:

```python
os.WIFEXITED(status)
os.WEXITSTATUS(status)
os.WIFSIGNALED(status)
os.WTERMSIG(status)
```

`kill_and_reap(still_running)` sends `SIGTERM` to every still-running child by
calling the external `kill` command through `my_system()`:

```python
cmd = f"kill {cpid}"
ret = my_system(cmd)
```

After sending termination signals, it waits for every child with blocking
`waitpid()` and reports the termination reason.

`_main()` coordinates the whole demonstration:

1. parse child count;
2. print parent PID;
3. run `ps --ppid <parent_pid>` before child creation;
4. create children;
5. sleep for 3 seconds;
6. reap children that already finished;
7. print and show still-running children;
8. sleep for 5 more seconds;
9. terminate remaining children;
10. reap all remaining children;
11. run `ps` again to show that no children remain.

Usage examples:

```bash
python3 src/task2.py
python3 src/task2.py 3
python3 src/task2.py 10
```

### Source File: `src/prog1.py`

`src/prog1.py` implements Program 1 from Task 3. It is the child-side worker
that performs one random interval experiment.

Main constants:

```python
DEFAULT_NUM = 500
MAX_EXIT_CODE = 255
```

Main functions:

```python
get_num()
get_interval()
count_hits(a, b, num)
_main()
```

`get_num()` reads the `NUM` environment variable:

```python
num_str = os.environ.get("NUM", str(DEFAULT_NUM))
```

If `NUM` is missing, the default value is `500`. If it is present, it must be a
positive integer. Invalid values produce an error on stderr and exit with code
`1`.

`get_interval()` reads exactly two command-line arguments:

```text
a b
```

Both values must be floats. The implementation accepts:

```text
0 <= a < b <= 1
```

The lab text describes `0 < a < b < 1`, but this implementation also allows
`0` and `1` so Program 0 can divide the full `[0, 1]` interval into equal
sub-intervals including the endpoints.

`count_hits(a, b, num)` generates `num` random values with `random.random()`.
It counts values that satisfy:

```python
a <= random_value <= b
```

The result is clamped:

```python
return min(hits, MAX_EXIT_CODE)
```

This is necessary because process exit codes carry only an 8-bit result value.
The maximum safe value is `255`.

`_main()` reads input, prints process information, runs the experiment, prints
the hit count, and exits with that count:

```python
sys.exit(hits)
```

Usage examples:

```bash
python3 src/prog1.py 0.0 0.5
NUM=100 python3 src/prog1.py 0.25 0.75
NUM=1000 python3 src/prog1.py 0.5 1.0
echo $?
```

The shell command `echo $?` prints the exit code of the previous command.

### Source File: `src/task3.py`

`src/task3.py` implements Program 0 from Task 3. It is the parent/controller
that starts one `prog1.py` child per interval and collects all child results.

Main constant:

```python
PROG1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prog1.py")
```

This builds an absolute path to `prog1.py` in the same directory as `task3.py`.
That makes execution independent from the current working directory.

Main functions:

```python
parse_args()
build_intervals(n)
launch_children(intervals, env)
wait_and_collect(child_pids, num)
_main()
```

`parse_args()` expects exactly two command-line arguments:

```text
n num
```

`n` is the number of equal sub-intervals of `[0, 1]`. `num` is the number of
random trials per interval. Both must be positive integers.

Usage:

```bash
python3 src/task3.py 5 100
```

`build_intervals(n)` splits `[0, 1]` into `n` equal sub-intervals:

```python
return [(i / n, (i + 1) / n) for i in range(n)]
```

Example for `n = 4`:

```text
[0.0, 0.25]
[0.25, 0.5]
[0.5, 0.75]
[0.75, 1.0]
```

`_main()` prepares the child environment:

```python
env = os.environ.copy()
env["NUM"] = str(num)
```

This is how Program 0 passes the number of trials to every Program 1 child.

`launch_children(intervals, env)` creates one child per interval. In every
iteration:

1. parent calls `os.fork()`;
2. child builds an argument vector for `prog1.py`;
3. child calls `os.execve()`;
4. parent stores `(interval_index, a, b, pid)`.

The child-side exec call is:

```python
args = [sys.executable, PROG1, str(a), str(b)]
os.execve(sys.executable, args, env)
```

This means the child process image is replaced by the current Python
interpreter running `prog1.py` with interval bounds as command-line arguments.
The prepared environment contains `NUM`.

`wait_and_collect(child_pids, num)` waits for every child:

```python
wpid, status = os.waitpid(cpid, 0)
```

This is a blocking wait. The parent must collect every child.

If the child exited normally, the parent extracts the hit count:

```python
hits = os.WEXITSTATUS(status)
```

It also calculates the expected number of hits for a uniform generator:

```python
expected = (b - a) * num
```

Then it prints a result line for the interval:

```text
Interval 1 [0.0000, 0.2500]:  24 hit(s) out of 100 (expected ~25.0)
```

If a child was killed by a signal, the parent reports the signal number with
`os.WTERMSIG(status)`. If the termination status is unusual, it prints the raw
status.

Usage examples:

```bash
python3 src/task3.py 2 50
python3 src/task3.py 5 100
python3 src/task3.py 10 200
```

## How Code Works Detailed

### Task 1 Detailed Flow: `my_system()`

The function starts with:

```python
def my_system(cmd=""):
```

The argument is a shell command string. If it is empty, the function returns
success immediately:

```python
if not cmd:
    return 0
```

Then the function creates a child:

```python
pid = os.fork()
```

After this call, two processes continue from the same line of code. The child
gets `pid == 0`; the parent gets the real PID of the child.

The child branch replaces itself with a shell:

```python
os.execve("/bin/sh", ["/bin/sh", "-c", cmd], os.environ.copy())
```

This is the key idea of `execve()`: it does not create another process. It
loads a new program into the current process. If the call succeeds, the child is
no longer running Python code; it is running `/bin/sh`.

The parent branch waits:

```python
_, status = os.waitpid(pid, 0)
```

The `0` flag means a blocking wait. The parent continues only after the child
finishes. The raw status is returned so the caller can inspect it.

If `execve()` fails inside the child, the child exits with `127`, a common shell
convention for command execution failure:

```python
os._exit(127)
```

`os._exit()` is used because the child was created by `fork()`. It exits
immediately without running parent-side Python cleanup code.

### Task 2 Detailed Flow: Child Lifecycle Demonstration

The Task 2 program begins by deciding how many children to create.

```python
num_children = get_num_children()
```

Valid command forms:

| Command | Behavior |
| --- | --- |
| `python3 src/task2.py` | create 10 children |
| `python3 src/task2.py 4` | create 4 children |
| `python3 src/task2.py 0` | print error and exit |
| `python3 src/task2.py abc` | print error and exit |

The parent prints its PID and runs `ps` through `my_system()`:

```python
my_system(f"ps --ppid {os.getpid()} --no-headers 2>/dev/null "
          f"|| echo '  (no children yet)'")
```

This shows whether the parent currently has child processes.

Children are created by:

```python
child_pids = create_children(num_children)
```

Each child executes this random decision:

```python
num = random.random()
if num >= 0.5:
    os._exit(0)
else:
    while True:
        time.sleep(1)
```

Successful children become finished processes. Looping children stay alive.

The parent sleeps for 3 seconds:

```python
time.sleep(3)
```

Then it performs a non-blocking reap:

```python
wpid, status = os.waitpid(cpid, os.WNOHANG)
```

`os.WNOHANG` prevents the parent from getting stuck waiting for children that
are still in infinite loops.

Finished children are reported with `report_exit()`. Still-running children are
stored in a new list.

For each still-running child, the parent later sends:

```bash
kill <pid>
```

through:

```python
my_system(cmd)
```

After sending signals, the parent performs blocking waits for those children.
This removes them from the process table and allows the program to report that
they were terminated by a signal.

This task demonstrates the complete lifecycle:

```text
fork -> child work -> normal exit or infinite loop -> parent non-blocking wait
-> parent kills survivors -> parent blocking wait -> all children reaped
```

### Task 3 Detailed Flow: Program 0 And Program 1 Communication

Task 3 is split into two files because the lab describes two separate programs.

Program 0 is `task3.py`. It receives:

```text
n num
```

Example:

```bash
python3 src/task3.py 4 100
```

Here:

- `n = 4`, so `[0, 1]` is split into four intervals;
- `num = 100`, so every child performs 100 random trials.

First, `task3.py` parses and validates the arguments:

```python
n = int(sys.argv[1])
num = int(sys.argv[2])
```

Both values must be positive integers.

Then it builds intervals:

```python
intervals = build_intervals(n)
```

For `n = 4`, the intervals are:

```text
[0.0, 0.25]
[0.25, 0.5]
[0.5, 0.75]
[0.75, 1.0]
```

Then it prepares the environment:

```python
env = os.environ.copy()
env["NUM"] = str(num)
```

This is the parent-to-child environment transfer. Every child receives the same
`NUM` value.

The parent launches children:

```python
child_pids = launch_children(intervals, env)
```

Inside each child:

```python
args = [sys.executable, PROG1, str(a), str(b)]
os.execve(sys.executable, args, env)
```

This replaces the child with:

```bash
python3 prog1.py a b
```

with `NUM` present in the child environment.

Program 1 is `prog1.py`. It reads:

```python
a = float(sys.argv[1])
b = float(sys.argv[2])
num = int(os.environ.get("NUM", "500"))
```

Then it generates random values and counts hits:

```python
hits = sum(1 for _ in range(num) if a <= random.random() <= b)
```

The count is clamped to `255`:

```python
return min(hits, MAX_EXIT_CODE)
```

Then Program 1 exits:

```python
sys.exit(hits)
```

The parent receives this value through `waitpid()`:

```python
wpid, status = os.waitpid(cpid, 0)
hits = os.WEXITSTATUS(status)
```

Then the parent prints both the actual count and the expected count:

```python
expected = (b - a) * num
```

For a uniform pseudo-random generator, each interval should receive roughly a
proportional number of hits. For example, if `[0, 1]` is split into 4 equal
parts and every child performs 100 trials, the expected value for each interval
is about 25 hits.

Important limitation: child-to-parent communication through exit code is very
small. Exit codes can represent only values from `0` to `255`. Because of that,
`prog1.py` clamps hit counts to `255`. If `num` is large, the printed result may
show `255` even if the real number of hits was greater.

### Process Status Helpers

The project uses Unix wait-status helpers to understand child termination.

Normal exit check:

```python
os.WIFEXITED(status)
```

Exit code extraction:

```python
os.WEXITSTATUS(status)
```

Signal termination check:

```python
os.WIFSIGNALED(status)
```

Signal number extraction:

```python
os.WTERMSIG(status)
```

Task 2 uses these helpers to explain whether a child finished normally, returned
an error code, or was killed by a signal. Task 3 uses them to collect numeric
results from Program 1 children.

### Expected Usage Workflow

1. Run the custom `system()` demonstration:

```bash
python3 src/task1.py
python3 src/task1.py "date"
python3 src/task1.py "ls -la"
```

2. Run the process lifecycle demonstration:

```bash
python3 src/task2.py
python3 src/task2.py 5
```

3. Run Program 1 directly:

```bash
NUM=50 python3 src/prog1.py 0.0 0.5
echo $?
```

4. Run Program 0, which creates Program 1 children:

```bash
python3 src/task3.py 4 100
python3 src/task3.py 10 200
```

5. Run style checking:

```bash
flake8 src
```

### Summary Of Program Logic

Task 1 demonstrates how `fork()`, `execve()`, and `waitpid()` can be combined to
run shell commands manually.

Task 2 demonstrates the lifecycle of multiple child processes: creation,
natural completion, non-blocking reaping, detection of still-running children,
signal termination, and final cleanup.

Task 3 demonstrates parent-child communication. `task3.py` sends interval bounds
through command-line arguments and sends `NUM` through the environment.
`prog1.py` performs work and returns a compact numeric result through its exit
code. The parent decodes those exit codes and prints the observed distribution
of generated pseudo-random numbers across the interval `[0, 1]`.

Together, these programs show the core idea of Laboratory Work #4: Linux
processes can be created, transformed, controlled, waited for, and used for
simple communication when the programmer understands process IDs, environments,
signals, and wait statuses.
