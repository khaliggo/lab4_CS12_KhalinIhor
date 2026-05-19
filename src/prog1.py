import os
import sys
import random

DEFAULT_NUM = 500
MAX_EXIT_CODE = 255


def get_num():
    """
    Read NUM from the environment (default 500).
    NUM defines how many random numbers to generate.
    """
    num_str = os.environ.get("NUM", str(DEFAULT_NUM))
    try:
        num = int(num_str)
        if num < 1:
            raise ValueError("NUM must be a positive integer")
        return num
    except ValueError as e:
        print(f"ERROR: invalid NUM env variable: {e}", file=sys.stderr)
        sys.exit(1)


def get_interval():
    """
    Read interval bounds a and b from command-line arguments.
    Expects exactly: prog1.py a b  (0 < a < b < 1)
    """
    if len(sys.argv) != 3:
        print(
            f"ERROR: expected 2 arguments (a b), "
            f"got {len(sys.argv) - 1}",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        a = float(sys.argv[1])
        b = float(sys.argv[2])
    except ValueError as e:
        print(f"ERROR: arguments must be floats: {e}", file=sys.stderr)
        sys.exit(1)
    if not (0 <= a < b <= 1):
        print(
            f"ERROR: arguments must satisfy 0 <= a < b <= 1, "
            f"got a={a}, b={b}",
            file=sys.stderr,
        )
        sys.exit(1)
    return a, b


def count_hits(a, b, num):
    """
    Generate `num` random floats in [0, 1) and count how many
    fall in the closed interval [a, b].
    Return value is clamped to MAX_EXIT_CODE (255) because only
    8 bits are available in a process exit code.
    """
    hits = sum(1 for _ in range(num) if a <= random.random() <= b)
    return min(hits, MAX_EXIT_CODE)


def _main():
    a, b = get_interval()
    num = get_num()

    print(
        f"prog1 (PID={os.getpid()}): interval=[{a}, {b}], "
        f"NUM={num}",
        flush=True,
    )

    hits = count_hits(a, b, num)

    print(
        f"prog1 (PID={os.getpid()}): {hits} hit(s) "
        f"in [{a}, {b}] out of {num} trials",
        flush=True,
    )

    sys.exit(hits)


if __name__ == "__main__":
    _main()
