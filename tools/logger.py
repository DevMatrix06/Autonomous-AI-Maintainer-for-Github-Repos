import sys

VERBOSE = False  # set True if you ever want debug logs

def info(msg):
    print(msg)

def debug(msg):
    if VERBOSE:
        print(f"[debug] {msg}", file=sys.stderr)

def divider():
    pass  # intentionally empty (keeps output clean)
