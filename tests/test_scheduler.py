"""Tests for the wait/snooze orchestration.

We never sleep for real and never touch the system clock: the scheduler reads
its "now" and "sleep" through module-level indirections (`_now`, `_sleep`) that
these tests replace with a controllable fake clock. The audible Ringer and the
interactive prompt are stubbed too, so the logic runs instantly and silently.
"""

from datetime import datetime, timedelta

import alarmclock.scheduler as scheduler


class FakeClock:
    """A clock that only advances when `sleep` is called."""

    def __init__(self, start: datetime) -> None:
        self.t = start
        self.slept: list[float] = []

    def now(self) -> datetime:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.t += timedelta(seconds=seconds)


class SpyRinger:
    """Stand-in for the real Ringer that records start/stop calls."""

    instances: list["SpyRinger"] = []

    def __init__(self) -> None:
        self.starts = 0
        self.stops = 0
        SpyRinger.instances.append(self)

    def start(self) -> None:
        self.starts += 1

    def stop(self) -> None:
        self.stops += 1


def _install(monkeypatch, clock, answers):
    """Wire the fake clock, spy ringer, and scripted prompt answers in."""
    monkeypatch.setattr(scheduler, "_now", clock.now)
    monkeypatch.setattr(scheduler, "_sleep", clock.sleep)
    monkeypatch.setattr(scheduler, "Ringer", SpyRinger)
    replies = iter(answers)
    # _prompt_snooze calls input(); feed it scripted replies.
    monkeypatch.setattr("builtins.input", lambda *_: next(replies))
    SpyRinger.instances.clear()


def test_waits_then_rings_once_on_dismiss(monkeypatch, capsys):
    clock = FakeClock(datetime(2026, 6, 9, 10, 0, 0))
    _install(monkeypatch, clock, answers=[""])  # "" = dismiss

    target = clock.now() + timedelta(seconds=5)
    scheduler.run_alarm(target, label=None, snooze=None, show_countdown=False)

    ringer = SpyRinger.instances[0]
    assert ringer.starts == 1 and ringer.stops == 1
    # It must not have finished before the target.
    assert clock.now() >= target
    # Some sleeping happened to get there.
    assert sum(clock.slept) >= 5


def test_snooze_re_arms_and_rings_again(monkeypatch):
    clock = FakeClock(datetime(2026, 6, 9, 10, 0, 0))
    _install(monkeypatch, clock, answers=["s", ""])  # snooze once, then dismiss

    target = clock.now() + timedelta(seconds=1)
    snooze = timedelta(seconds=30)
    start = clock.now()
    scheduler.run_alarm(target, label=None, snooze=snooze, show_countdown=False)

    ringer = SpyRinger.instances[0]
    assert ringer.starts == 2  # rang, snoozed, rang again
    assert ringer.stops == 2
    # Total elapsed must cover the initial 1s plus the 30s snooze.
    assert clock.now() - start >= timedelta(seconds=31)


def test_snooze_answer_ignored_when_no_snooze_configured(monkeypatch):
    clock = FakeClock(datetime(2026, 6, 9, 10, 0, 0))
    _install(monkeypatch, clock, answers=["s"])  # asks to snooze...

    target = clock.now() + timedelta(seconds=2)
    # ...but snooze=None, so it must dismiss after a single ring.
    scheduler.run_alarm(target, label=None, snooze=None, show_countdown=False)

    assert SpyRinger.instances[0].starts == 1
