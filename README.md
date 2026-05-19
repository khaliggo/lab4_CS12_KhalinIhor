# Operating Systems Lab 4 - Working With Processes

## About Project

This project was created for Operating Systems Laboratory Work #4, "Working
with Processes". The laboratory work focuses on practical process management in
Linux using Python and low-level operating-system interfaces.

The main educational goal of the lab is to understand how processes are created,
how one program can be started inside another process, how a parent process can
wait for child processes, and how process termination information is delivered
back to the parent.

The laboratory assignment covers these process-related topics:

- creating a new process with `fork()`;
- replacing the current process image with another program using functions from
  the `exec()` family;
- waiting for child processes with `wait()` and `waitpid()`;
- reading and interpreting process termination status;
- distinguishing normal exit, error exit, and signal termination;
- passing data from a parent process to a child process through command-line
  arguments;
- passing data from a parent process to a child process through environment
  variables;
- returning a small result from a child process to the parent through the exit
  code;
- understanding zombie processes and why finished children must be reaped;
- observing process state with shell commands such as `ps`;
- terminating still-running processes with `kill`.

The lab contains three tasks.

Task 1 asks to implement a custom function named `my_system()`. This function is
a simplified analog of the standard C/Python `system()` behavior. It should run
external shell commands by manually using process-control operations:

1. create a child process with `fork()`;
2. in the child process, run `/bin/sh -c <command>` with `execve()`;
3. in the parent process, wait for the child with `waitpid()`;
4. return the raw wait status.

The task specifically asks for a simplified implementation without full signal
handling. This project follows that idea: `my_system()` is small and focused on
demonstrating the process lifecycle.

Task 2 asks to create a program that starts a chosen number of child processes.
The number of children is an optional command-line argument. If it is not
provided, the default number is `10`.

Each child process generates a pseudo-random floating-point number in the range
`[0, 1)`. If the number is greater than or equal to `0.5`, the child exits
normally with exit code `0`. If the number is less than `0.5`, the child enters
an infinite loop. The parent process then:

1. creates all child processes;
2. sleeps for 3 seconds;
3. reaps children that already finished;
4. prints which children are still running;
5. sleeps for 5 more seconds;
6. terminates the remaining children with `kill`;
7. waits for the killed children;
8. prints the reason why every child finished.

This task demonstrates a very important process-management rule: a parent must
collect finished child processes. If it does not, finished children may stay in
the process table as zombies until the parent exits or reaps them.

Task 3 explores a simple form of communication between a parent process and
child processes. The lab describes a pair of programs:

- Program 0 divides the interval `[0, 1]` into equal parts, creates child
  processes, gives each child one interval through command-line arguments, and
  gives all children a trial count through the `NUM` environment variable.
- Program 1 receives interval bounds `a` and `b` through command-line arguments,
  receives `NUM` from the environment, generates random values, counts how many
  values fall into `[a, b]`, and returns that count through its process exit
  code.

In this repository, `src/task3.py` implements the Program 1 side of that task.
It reads interval bounds from `sys.argv`, reads `NUM` from `os.environ`,
generates pseudo-random numbers, counts hits, and exits with the hit count. The
implementation also protects against the 8-bit exit-code limitation by clamping
the returned hit count to `255`.

The project uses only Python standard library modules in the runtime code. It
is intended to be run on Linux or a Unix-like system because it depends on
process APIs such as `os.fork()`, `os.execve()`, `os.waitpid()`, and POSIX
signals.

The laboratory requirements also mention project organization, Git history, a
README file, and `flake8` quality checking. This README explains the purpose of
the project, the source files, and the behavior of each utility.

## About Code

The project contains three source files:

```text
lab4_CS12_KhalinIhor/
|-- README.md
`-- src/
    |-- task1.py
    |-- task2.py
    `-- task3.py
```

There are no external runtime dependencies. The code uses these Python standard
library modules:

- `os`: process creation, program execution, waiting, environment access,
  process IDs, exit status helpers, file paths, and shell command execution
  support;
- `sys`: command-line arguments, stderr output, and exiting with a status code;
- `time`: sleeping in parent and child processes;
- `random`: generating pseudo-random floating-point values.

### Source File: `src/task1.py`

`src/task1.py` implements Task 1: a custom simplified `system()` analog.

Main function:

```python
my_system(cmd="")
```

Demo entry point:

```python
_main()
```

The `my_system()` function accepts a shell command as a string. If the command
is empty, it returns `0`. Otherwise, it creates a child process with
`os.fork()`.

After `fork()`, the program has two execution paths:

- child process path, where `pid == 0`;
- parent process path, where `pid` is the process ID of the child.

In the child process, the function calls:

```python
os.execve("/bin/sh", ["/bin/sh", "-c", cmd], os.environ.copy())
```

This replaces the child process image with `/bin/sh`. The shell receives `-c`
and the command string, so it executes the command exactly as a shell command.
The child also receives a copy of the current environment.

In the parent process, the function calls:

```python
_, status = os.waitpid(pid, 0)
return status
```

`waitpid(pid, 0)` blocks until the specific child process finishes. The returned
`status` is the raw wait status, like the value returned by `os.system()`.

The raw wait status is not always the same as the exit code. The code converts
it for display in demo mode with:

```python
os.waitstatus_to_exitcode(status)
```

The `_main()` function provides two ways to demonstrate `my_system()`:

- if one command-line argument is provided, it runs that command;
- if no command is provided, it runs a built-in list of demo commands.

Built-in demo commands:

```text
date
cp
ls -la
nonexistentcommand123
```

Examples:

```bash
python3 src/task1.py
python3 src/task1.py "date"
python3 src/task1.py "ls -la"
python3 src/task1.py "echo hello"
python3 src/task1.py "nonexistentcommand123"
```

### Source File: `src/task2.py`

`src/task2.py` implements Task 2: child process creation, observation,
termination, and cleanup.

Main constants and functions:

```python
DEFAULT_NUM_CHILDREN = 10

get_num_children()
report_exit(idx, wpid, status)
create_children(num_children)
reap_finished(child_pids)
kill_and_reap(still_running)
_main()
```

The file imports `my_system()` from Task 1:

```python
from task1 import my_system
```

This connects Task 2 to Task 1. The parent process uses the custom shell-command
runner to execute `ps` and `kill` commands.

`get_num_children()` reads the optional command-line argument. If no argument is
provided, it returns `DEFAULT_NUM_CHILDREN`, which is `10`. If one argument is
provided, the function tries to convert it to an integer and requires it to be a
positive number. Invalid input prints an error and exits with code `1`.

`create_children(num_children)` creates child processes in a loop. For each
child, it calls `os.fork()`.

In each child process:

1. a random number is generated with `random.random()`;
2. the child prints its index, process ID, and generated number;
3. if the number is at least `0.5`, the child prints a success message and exits
   with `os._exit(0)`;
4. if the number is below `0.5`, the child enters an infinite loop and sleeps
   repeatedly.

The infinite loop is intentional. It creates child processes that remain alive
so the parent can later detect and terminate them.

In the parent process, each child PID is stored as a tuple:

```python
(child_index, pid)
```

The returned list lets the parent know which child index belongs to which real
process ID.

`reap_finished(child_pids)` performs a non-blocking wait for every child:

```python
wpid, status = os.waitpid(cpid, os.WNOHANG)
```

`os.WNOHANG` means the parent does not block if the child is still running. If
`waitpid()` returns `0`, the child has not finished yet. If it returns a child
PID, that child has finished and can be reported.

The function returns only the children that are still running.

`report_exit(idx, wpid, status)` interprets the termination status:

- `os.WIFEXITED(status)` checks whether the child exited normally;
- `os.WEXITSTATUS(status)` extracts the normal exit code;
- `os.WIFSIGNALED(status)` checks whether the child was terminated by a signal;
- `os.WTERMSIG(status)` extracts the signal number.

The printed message distinguishes:

- normal exit with code `0`;
- error exit with a nonzero code;
- termination by signal;
- unknown termination status.

`kill_and_reap(still_running)` handles children that did not finish naturally.
For each still-running child, it builds a shell command:

```python
kill <pid>
```

Then it runs that command through `my_system()`. After sending termination
signals, it calls `os.waitpid(cpid, 0)` for every remaining child. This final
wait is blocking because the parent must collect each terminated child.

The `_main()` function coordinates the whole demonstration:

1. parse child count;
2. print the parent PID;
3. run `ps` to show current child process state;
4. create children;
5. sleep 3 seconds;
6. reap children that finished naturally;
7. print still-running children and show them with `ps`;
8. sleep 5 seconds;
9. kill and reap survivors;
10. run `ps` again to show that no children remain.

Examples:

```bash
python3 src/task2.py
python3 src/task2.py 3
python3 src/task2.py 10
python3 src/task2.py 20
```

### Source File: `src/task3.py`

`src/task3.py` implements the Program 1 side of Task 3: counting random values
that fall into a specified interval and returning the count through the process
exit code.

Main constants and functions:

```python
DEFAULT_NUM = 500
MAX_EXIT_CODE = 255

get_num()
get_interval()
count_hits(a, b, num)
_main()
```

`DEFAULT_NUM` is the default number of random trials when the `NUM` environment
variable is not set.

`MAX_EXIT_CODE` is `255` because only 8 bits are available for the meaningful
exit-code value returned from a child process.

`get_num()` reads the environment variable:

```python
os.environ.get("NUM", str(DEFAULT_NUM))
```

If `NUM` is missing, the function uses `"500"`. The value is converted to an
integer and must be positive. If it is invalid, the program prints an error to
stderr and exits with code `1`.

`get_interval()` reads exactly two command-line arguments:

```text
a b
```

Both must be floating-point numbers. The implementation accepts intervals that
satisfy:

```text
0 <= a < b <= 1
```

The lab text describes the stricter mathematical condition `0 < a < b < 1`,
while this implementation also allows the endpoints `0` and `1`. This is useful
when the full `[0, 1]` range is divided into adjacent pieces.

`count_hits(a, b, num)` performs the experiment:

1. generate `num` random values with `random.random()`;
2. count values where `a <= value <= b`;
3. return the count;
4. clamp the count to `255`.

The clamping is important because process exit codes cannot reliably return
large integers. If the hit count is greater than `255`, the returned exit code
would lose information. This implementation avoids wraparound by returning at
most `255`.

The `_main()` function:

1. reads interval bounds from command-line arguments;
2. reads the number of trials from the environment;
3. prints process information;
4. runs the random experiment;
5. prints the hit count;
6. exits with the hit count.

Examples:

```bash
python3 src/task3.py 0.0 0.5
python3 src/task3.py 0.25 0.75
NUM=100 python3 src/task3.py 0.0 0.1
NUM=1000 python3 src/task3.py 0.5 1.0
```

Because the result is returned through the exit code, the shell can inspect it:

```bash
NUM=100 python3 src/task3.py 0.0 0.5
echo $?
```

The printed value from `echo $?` is the child process exit code, clamped to the
range `0..255`.

## How Code Works Detailed

### Task 1 Detailed Flow: Custom `my_system()`

The first task demonstrates how a shell command can be launched manually without
directly calling `os.system()`.

The function signature is:

```python
def my_system(cmd=""):
```

The argument `cmd` is the shell command to run. The default is an empty string.

The first check handles an empty command:

```python
if not cmd:
    return 0
```

This keeps the function simple and predictable. If there is nothing to execute,
the function reports success with `0`.

The next step is process creation:

```python
try:
    pid = os.fork()
except OSError as e:
    print(f"ERROR: fork() failed: {e}")
    return -1
```

`os.fork()` creates a new process. After a successful fork, both parent and
child continue executing the same Python code, but `fork()` returns different
values:

- in the child process, it returns `0`;
- in the parent process, it returns the child's process ID.

If `fork()` fails, the function prints an error and returns `-1`.

The child branch is:

```python
if pid == 0:
    try:
        os.execve("/bin/sh", ["/bin/sh", "-c", cmd], os.environ.copy())
    except OSError as e:
        print(f"ERROR: execve() failed: {e}")
        os._exit(127)
```

The child calls `execve()`. This is a major process concept: `execve()` does not
create a new process. Instead, it replaces the current process image with a new
program. After a successful `execve()`, the Python child process becomes
`/bin/sh`.

The argument list:

```python
["/bin/sh", "-c", cmd]
```

means:

- run `/bin/sh`;
- tell the shell to execute a command string with `-c`;
- use `cmd` as that command string.

The environment is passed as:

```python
os.environ.copy()
```

This gives the child a copy of the current process environment.

If `execve()` fails, the child exits with:

```python
os._exit(127)
```

`os._exit()` is used instead of `sys.exit()` in a child created by `fork()`.
`os._exit()` terminates immediately without running Python cleanup handlers that
belong to the parent process.

The parent branch is:

```python
else:
    _, status = os.waitpid(pid, 0)
    return status
```

The parent waits for the exact child process. The second argument `0` means a
blocking wait. The parent will not continue until the child terminates.

The returned `status` is a packed wait status. It contains information about
whether the child exited normally, what exit code it used, or whether it was
terminated by a signal.

Example:

```bash
python3 src/task1.py "echo hello"
```

Expected behavior:

1. parent forks;
2. child becomes `/bin/sh -c "echo hello"`;
3. shell prints `hello`;
4. shell exits;
5. parent waits;
6. parent prints raw status and converted exit code.

### Task 2 Detailed Flow: Creating And Reaping Children

Task 2 demonstrates a parent process managing several child processes.

The program starts by reading the number of children:

```python
num_children = get_num_children()
```

`get_num_children()` supports these cases:

| Command | Result |
| --- | --- |
| `python3 src/task2.py` | use default `10` |
| `python3 src/task2.py 5` | create `5` children |
| `python3 src/task2.py 0` | error, not positive |
| `python3 src/task2.py abc` | error, not an integer |
| `python3 src/task2.py 1 2` | error, too many arguments |

Then the parent prints its own PID:

```python
print(f"Parent PID={os.getpid()}")
```

The PID is useful because later `ps --ppid <parent_pid>` can show child
processes that belong to this parent.

The program runs:

```python
my_system(f"ps --ppid {os.getpid()} --no-headers 2>/dev/null "
          f"|| echo '  (no children yet)'")
```

This command shows child processes of the current parent before new children
are created.

Child creation happens in:

```python
child_pids = create_children(num_children)
```

Inside `create_children()`, the parent loops from `0` to `num_children - 1`.
Each iteration calls `os.fork()`.

In the child branch, a random number is generated:

```python
num = random.random()
```

`random.random()` returns a float in `[0, 1)`.

If the number is at least `0.5`, the child exits normally:

```python
if num >= 0.5:
    os._exit(0)
```

This creates a finished child that the parent must later reap.

If the number is below `0.5`, the child enters an infinite loop:

```python
while True:
    time.sleep(1)
```

The child sleeps inside the loop to avoid consuming CPU aggressively. It remains
alive until the parent sends it a termination signal.

The parent branch stores each child:

```python
child_pids.append((i + 1, pid))
```

The index is human-friendly, starting from `1`. The PID is the real operating
system process ID.

After all children are created, the parent sleeps:

```python
time.sleep(3)
```

This gives children time either to finish normally or stay alive in their loops.

Then the parent reaps finished children:

```python
still_running = reap_finished(child_pids)
```

`reap_finished()` uses:

```python
wpid, status = os.waitpid(cpid, os.WNOHANG)
```

The `os.WNOHANG` flag is important. It means:

- if the child already finished, return its PID and status;
- if the child is still running, return `0` immediately;
- do not block the parent.

If a child finished, the program calls:

```python
report_exit(idx, wpid, status)
```

`report_exit()` decodes the status.

Normal successful exit:

```python
os.WIFEXITED(status)
os.WEXITSTATUS(status) == 0
```

Error exit:

```python
os.WIFEXITED(status)
os.WEXITSTATUS(status) != 0
```

Signal termination:

```python
os.WIFSIGNALED(status)
os.WTERMSIG(status)
```

If children are still running, the parent prints their PIDs and runs `ps` again:

```python
my_system(f"ps --ppid {os.getpid()} --no-headers 2>/dev/null")
```

Then the parent sleeps five more seconds:

```python
time.sleep(5)
```

After that, remaining children are terminated:

```python
kill_and_reap(still_running)
```

For each still-running child, `kill_and_reap()` builds:

```python
cmd = f"kill {cpid}"
```

and runs it through:

```python
ret = my_system(cmd)
```

The normal `kill` command sends `SIGTERM` by default. If `kill` fails, the code
prints a warning with the converted exit code.

After sending termination signals, the parent waits for every survivor:

```python
wpid, status = os.waitpid(cpid, 0)
report_exit(idx, wpid, status)
```

This time the wait is blocking. The parent must fully collect every child before
the program ends.

The final `ps` command checks whether child processes remain:

```python
my_system(f"ps --ppid {os.getpid()} --no-headers 2>/dev/null "
          f"|| echo '  (no children remaining)'")
```

This completes the process lifecycle demonstration:

```text
fork -> child runs -> parent waits -> parent reports -> parent kills survivors
-> parent waits again -> all children are reaped
```

### Task 3 Detailed Flow: Returning Data Through Exit Codes

Task 3 demonstrates a very simple communication path:

```text
parent -> child: command-line arguments and environment variables
child -> parent: process exit code
```

In this repository, `task3.py` is the child-side program.

The program expects two command-line arguments:

```bash
python3 src/task3.py a b
```

For example:

```bash
python3 src/task3.py 0.2 0.4
```

The interval is read by:

```python
a = float(sys.argv[1])
b = float(sys.argv[2])
```

The argument count is checked first:

```python
if len(sys.argv) != 3:
    print(
        f"ERROR: expected 2 arguments (a b), "
        f"got {len(sys.argv) - 1}",
        file=sys.stderr,
    )
    sys.exit(1)
```

If the user passes too few or too many arguments, the program exits with code
`1`.

If arguments cannot be converted to floats, the program also exits with code
`1`.

After conversion, the interval is validated:

```python
if not (0 <= a < b <= 1):
    print(
        f"ERROR: arguments must satisfy 0 <= a < b <= 1, "
        f"got a={a}, b={b}",
        file=sys.stderr,
    )
    sys.exit(1)
```

The number of random trials comes from the environment:

```python
num_str = os.environ.get("NUM", str(DEFAULT_NUM))
```

Examples:

```bash
python3 src/task3.py 0.0 0.5
NUM=100 python3 src/task3.py 0.0 0.5
```

If `NUM` is missing, the program uses `500`. If `NUM` is present, it must be a
positive integer.

The experiment is performed by:

```python
hits = sum(1 for _ in range(num) if a <= random.random() <= b)
```

This line generates `num` pseudo-random values. For each value, it checks
whether it belongs to the closed interval `[a, b]`. Every successful check adds
one hit.

Then the return value is clamped:

```python
return min(hits, MAX_EXIT_CODE)
```

This matters because exit codes are limited. Even though Python integers can be
large, only the low 8 bits are normally available as a process exit status. The
largest safe direct value is `255`.

Finally, `_main()` exits with:

```python
sys.exit(hits)
```

A parent process can read this exit code using `waitpid()` and
`os.WEXITSTATUS(status)`.

Manual shell example:

```bash
NUM=50 python3 src/task3.py 0.0 0.5
echo $?
```

The second command prints the exit code of `task3.py`. Because random values are
used, the result changes from run to run.

### Process Status And Exit Code Notes

Process termination status in Unix-like systems is packed. A child does not only
return a simple integer to the parent. The parent receives a status value that
can describe several situations.

Normal exit:

```python
os.WIFEXITED(status)
```

If this is true, the child called `exit()`, returned from main, or used
`sys.exit()` / `os._exit()` normally. The actual exit code is available through:

```python
os.WEXITSTATUS(status)
```

Signal termination:

```python
os.WIFSIGNALED(status)
```

If this is true, the child was terminated by a signal. The signal number is
available through:

```python
os.WTERMSIG(status)
```

Task 2 uses these helpers to print why every child was removed from memory.
Task 1 returns the raw status from `waitpid()` and then demonstrates conversion
with `os.waitstatus_to_exitcode()`.

### Expected Usage Workflow

1. Run the custom `system()` demonstration:

```bash
python3 src/task1.py
python3 src/task1.py "date"
python3 src/task1.py "ls -la"
```

2. Run the child-process management demonstration:

```bash
python3 src/task2.py
python3 src/task2.py 5
```

3. Run the random interval worker:

```bash
python3 src/task3.py 0.0 0.5
NUM=100 python3 src/task3.py 0.25 0.75
echo $?
```

4. Run linting:

```bash
flake8 src
```

### Summary Of Program Logic

Task 1 shows how a parent process can create a child, replace the child with a
shell, run a command, and wait for the command to finish.

Task 2 shows how a parent can create many children, allow some to exit
naturally, detect which children are still running, terminate those children,
and correctly reap every child process.

Task 3 shows how a child process can receive input through command-line
arguments and environment variables, perform computation, and return a compact
numeric result through its exit code.

Together, these programs demonstrate the central idea of Laboratory Work #4:
processes in Linux have a lifecycle that can be controlled programmatically, and
parent-child communication can be built from simple operating-system mechanisms
such as arguments, environment variables, signals, and exit statuses.
