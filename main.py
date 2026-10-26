"""
Empty Room - Legacy Entrypoint (main.py).
Maintained for backwards compatibility; delegates to empty_room.cli.
"""

import sys
from empty_room.cli import main

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Default behavior: run foreground detector
        sys.argv.append("run")
    main()