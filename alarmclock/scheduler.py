"""Waiting + ringing orchestration.

The wait is a short polling loop rather than one long ``sleep`` so that:

* ``Ctrl+C`` is honoured promptly, and
* a once-per-second countdown can be printed.

When the target is reached the :class:`~alarmclock.sound.Ringer` starts and
the user is prompted to dismiss or snooze. Snooze simply re-arms the loop for
``snooze`` seconds later.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta

from .parsing import format_delta, seconds_until
from .sound import Ringer

# Indirections so tests can run without touching the real clock / sleeping.
_now = datetime.now
_sleep = time.sleep

# How often the wait loop wakes to update the countdown / check for Ctrl+C.
_TICK = 0.5


def _wait_until(target: datetime, *, show_countdown: bool) -> None:
    """Block until ``target``, optionally printing a live countdown."""
    while True:
        remaining = seconds_until(target, _now())
        if remaining <= 0:
            break
        if show_countdown and sys.stdout.isatty():
            # \r keeps the countdown on a single rewritten line.
            sys.stdout.write(f"\r   Ringing in {format_delta(remaining)} …   ")
            sys.stdout.flush()
        _sleep(min(_TICK, remaining))
    if show_countdown and sys.stdout.isatty():
        sys.stdout.write("\r" + " " * 40 + "\r")  # clear the countdown line
        sys.stdout.flush()


def _prompt_snooze(label: str | None) -> bool:
    """Ring + prompt. Return ``True`` to snooze, ``False`` to dismiss."""
    banner = f'⏰  RING!  "{label}"' if label else "⏰  RING!"
    print(banner)
    print("  [Enter] = dismiss    s = snooze")
    try:
        answer = input("  > ").strip().lower()
    except EOFError:
        answer = ""  # piped/no TTY -> treat as dismiss
    return answer == "s"


def run_alarm(
    target: datetime,
    *,
    label: str | None = None,
    snooze: timedelta | None = None,
    show_countdown: bool = True,
) -> None:
    """Wait until ``target`` then ring, handling the snooze loop.

    Raises nothing on normal completion. ``KeyboardInterrupt`` propagates to
    the caller, which prints a friendly cancellation message.
    """
    ringer = Ringer()
    while True:
        _wait_until(target, show_countdown=show_countdown)
        ringer.start()
        try:
            wants_snooze = _prompt_snooze(label)
        finally:
            ringer.stop()
        if not (wants_snooze and snooze):
            break
        target = _now() + snooze
        print(f"  Snoozed — back in {format_delta(snooze.total_seconds())}.\n")
