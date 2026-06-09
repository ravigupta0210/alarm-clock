#!/usr/bin/env python3
"""Command-line alarm clock.

Usage examples::

    python alarm.py 07:30                 # ring at the next 07:30
    python alarm.py 10m                   # ring in 10 minutes
    python alarm.py 1h30m --label Tea     # labelled timer
    python alarm.py 5s --snooze 2m        # custom snooze length

Run ``python alarm.py --help`` for the full reference.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from alarmclock.parsing import (
    SpecError,
    format_delta,
    parse_duration,
    parse_spec,
    seconds_until,
)
from alarmclock.scheduler import run_alarm


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarm",
        description="A simple, dependency-free CLI alarm clock.",
        epilog="Examples: 'alarm 07:30', 'alarm 10m', 'alarm 1h30m --label Standup'.",
    )
    parser.add_argument(
        "spec",
        help="When to ring: a 24h time 'HH:MM' (e.g. 07:30) or a duration (e.g. 10m, 1h30m, 90s).",
    )
    parser.add_argument(
        "--label", "-l", default=None,
        help="Optional message shown when the alarm rings.",
    )
    parser.add_argument(
        "--snooze", "-s", default="5m", metavar="DURATION",
        help="Snooze length offered when ringing (default: 5m). E.g. 3m, 30s.",
    )
    parser.add_argument(
        "--no-countdown", action="store_true",
        help="Suppress the live countdown line.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    now = datetime.now()
    try:
        target = parse_spec(args.spec, now)
        snooze = parse_duration(args.snooze)
    except SpecError as exc:
        parser.error(str(exc))  # prints usage + message, exits non-zero
        return 2  # unreachable; keeps type-checkers happy

    when = target.strftime("%H:%M:%S")
    ring_in = format_delta(seconds_until(target, now))
    label = f' "{args.label}"' if args.label else ""
    print(f"⏰  Alarm set for {when}{label} — ringing in {ring_in}.")
    print("   Press Ctrl+C to cancel.\n")

    try:
        run_alarm(
            target,
            label=args.label,
            snooze=snooze,
            show_countdown=not args.no_countdown,
        )
    except KeyboardInterrupt:
        print("\n   Alarm cancelled. Bye!")
        return 130  # conventional exit code for SIGINT

    print("   Alarm dismissed. Have a good one!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
