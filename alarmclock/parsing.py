"""Pure time-parsing logic — no I/O, no real clock.

Every function takes the current time (`now`) as an argument instead of
calling ``datetime.now()`` internally. That keeps this module deterministic
and trivially unit-testable: a test can pin "now" to any instant and assert
the exact target the alarm should fire at.

Two input shapes are supported, covering the two real use cases for an
alarm clock:

* Absolute wall-clock time  -> ``"07:30"``  (24-hour ``HH:MM``)
* Relative duration         -> ``"10m"``, ``"1h30m"``, ``"90s"``
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

# Matches one-or-more "<number><unit>" chunks, units h/m/s, e.g. "1h30m", "90s".
_DURATION_RE = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$", re.IGNORECASE)
# Matches a 24-hour clock time, e.g. "7:30" or "07:30".
_CLOCK_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


class SpecError(ValueError):
    """Raised when an alarm spec can't be understood. Carries a human message."""


def parse_duration(spec: str) -> timedelta:
    """Parse a relative duration like ``"1h30m"`` into a ``timedelta``.

    Raises :class:`SpecError` if the string isn't a valid duration or sums
    to zero (a zero-length alarm is almost certainly a typo).
    """
    match = _DURATION_RE.match(spec.strip())
    if not match or spec.strip() == "":
        raise SpecError(
            f"{spec!r} is not a valid duration. "
            "Use forms like '10m', '1h30m', or '90s'."
        )
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    total = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    if total <= timedelta(0):
        raise SpecError(f"Duration {spec!r} must be greater than zero.")
    return total


def parse_clock_time(spec: str, now: datetime) -> datetime:
    """Parse an absolute ``"HH:MM"`` into the next datetime it occurs.

    If the time is still ahead of ``now`` today, the alarm is today;
    otherwise it rolls over to the same time tomorrow.
    """
    match = _CLOCK_RE.match(spec.strip())
    if not match:
        raise SpecError(f"{spec!r} is not a valid time. Use 24-hour 'HH:MM', e.g. '07:30'.")
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        raise SpecError(f"{spec!r} is out of range. Hours 0-23, minutes 0-59.")
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)  # already passed today -> tomorrow
    return target


def parse_spec(spec: str, now: datetime) -> datetime:
    """Parse either an absolute time or a relative duration into a target datetime.

    A ``":"`` disambiguates the two forms: clock times contain one, durations
    never do. ``now`` is injected for testability.
    """
    spec = spec.strip()
    if ":" in spec:
        return parse_clock_time(spec, now)
    return now + parse_duration(spec)


def seconds_until(target: datetime, now: datetime) -> float:
    """Return seconds from ``now`` until ``target`` (never negative)."""
    return max(0.0, (target - now).total_seconds())


def format_delta(seconds: float) -> str:
    """Render a number of seconds as a compact human string, e.g. ``"2h 14m"``.

    Used only for friendly confirmation output.
    """
    seconds = int(round(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs and not hours:  # only show seconds for short alarms
        parts.append(f"{secs}s")
    return " ".join(parts) or "0s"
