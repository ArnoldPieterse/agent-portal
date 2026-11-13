import os
import sys


def safe_relpath(target, start):
    """os.path.relpath that falls back to an absolute path across drives.
    Windows relpath is undefined (ValueError) when target and start sit on
    different mount points; an absolute path is the sane cross-drive answer."""
    try:
        return os.path.relpath(target, start)
    except ValueError:
        return os.path.abspath(target)

def a():
    return safe_relpath("D:\\models\\x.gguf", "Z:\\dcabots")
def b():
    x = safe_relpath("C:\\a", "C:\\b")
def c():
    y = safe_relpath(sys.argv[1], ".")
