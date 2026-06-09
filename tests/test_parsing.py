"""Tests for the pure parsing core.

`now` is pinned to a fixed instant so every assertion is deterministic and
no real time passes.
"""

from datetime import datetime, timedelta

import pytest

from alarmclock.parsing import (
    SpecError,
    format_delta,
    parse_clock_time,
    parse_duration,
    parse_spec,
    seconds_until,
)

# A fixed reference "now": 2026-06-09, 10:00:00.
NOW = datetime(2026, 6, 9, 10, 0, 0)


# ---------- durations ----------

@pytest.mark.parametrize(
    "spec, expected",
    [
        ("10m", timedelta(minutes=10)),
        ("90s", timedelta(seconds=90)),
        ("1h30m", timedelta(hours=1, minutes=30)),
        ("2H", timedelta(hours=2)),            # case-insensitive
        ("1h30m15s", timedelta(hours=1, minutes=30, seconds=15)),
    ],
)
def test_parse_duration_valid(spec, expected):
    assert parse_duration(spec) == expected


@pytest.mark.parametrize("spec", ["", "abc", "10x", "0m", "0h0m0s", "-5m", "m"])
def test_parse_duration_invalid(spec):
    with pytest.raises(SpecError):
        parse_duration(spec)


# ---------- clock times ----------

def test_clock_time_later_today_stays_today():
    target = parse_clock_time("10:30", NOW)
    assert target == datetime(2026, 6, 9, 10, 30, 0)


def test_clock_time_already_passed_rolls_to_tomorrow():
    target = parse_clock_time("09:00", NOW)
    assert target == datetime(2026, 6, 10, 9, 0, 0)


def test_clock_time_equal_to_now_rolls_over():
    # Exactly "now" should ring tomorrow, not instantly.
    target = parse_clock_time("10:00", NOW)
    assert target == datetime(2026, 6, 10, 10, 0, 0)


def test_clock_time_accepts_single_digit_hour():
    assert parse_clock_time("7:05", NOW) == datetime(2026, 6, 10, 7, 5, 0)


@pytest.mark.parametrize("spec", ["24:00", "12:60", "99:99", "7:5", "noon"])
def test_clock_time_invalid(spec):
    with pytest.raises(SpecError):
        parse_clock_time(spec, NOW)


# ---------- dispatch ----------

def test_parse_spec_routes_colon_to_clock():
    assert parse_spec("23:00", NOW) == datetime(2026, 6, 9, 23, 0, 0)


def test_parse_spec_routes_plain_to_duration():
    assert parse_spec("15m", NOW) == NOW + timedelta(minutes=15)


# ---------- helpers ----------

def test_seconds_until_is_never_negative():
    past = NOW - timedelta(hours=1)
    assert seconds_until(past, NOW) == 0.0


def test_seconds_until_counts_forward():
    future = NOW + timedelta(seconds=42)
    assert seconds_until(future, NOW) == 42.0


@pytest.mark.parametrize(
    "seconds, text",
    [
        (0, "0s"),
        (45, "45s"),
        (90, "1m 30s"),
        (120, "2m"),
        (3600, "1h"),
        (8040, "2h 14m"),
    ],
)
def test_format_delta(seconds, text):
    assert format_delta(seconds) == text
