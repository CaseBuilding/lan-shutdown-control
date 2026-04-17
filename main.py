from __future__ import annotations

import argparse

from ui import run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimized", action="store_true", help="Start minimized to the system tray.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(start_minimized=args.minimized)
