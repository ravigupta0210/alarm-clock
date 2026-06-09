# ⏰ alarm-clock

A small, dependency-free **command-line alarm clock** in Python.

```console
$ python alarm.py 07:30 --label "Standup"
⏰  Alarm set for 07:30:00 "Standup" — ringing in 2h 14m.
   Press Ctrl+C to cancel.

   Ringing in 2h 13m …
```

When the time comes it rings (looping sound) and asks whether to **dismiss** or **snooze**.

This was built as a 30-minute take-home. The brief was deliberately open ("decide what to build"), so most of the value below is in the **reasoning** — what I chose to build, what I cut, and how I validated it — not the feature count.

---

## Usage

```console
python alarm.py 07:30                  # ring at the next 07:30 (today, or tomorrow if passed)
python alarm.py 10m                    # ring in 10 minutes
python alarm.py 1h30m                  # 1 hour 30 minutes
python alarm.py 90s                    # 90 seconds
python alarm.py 07:30 --label "Standup"   # show a message when it rings
python alarm.py 25m   --snooze 3m         # custom snooze length (default 5m)
python alarm.py 10m   --no-countdown      # suppress the live countdown line
python alarm.py --help
```

**When it rings:** a sound loops and you see a prompt — press **Enter** to dismiss, or **`s`** then Enter to snooze. **Ctrl+C** cancels cleanly at any time.

The spec format is unambiguous by design: anything containing `:` is read as a 24-hour clock time, everything else as a relative duration.

---

## Run it / test it

Requires **Python 3.8+**. No third-party packages to run.

```console
python alarm.py 5s --label "It works"     # try a 5-second alarm
```

Tests use `pytest` (the only dev dependency):

```console
pip install pytest
pytest -q          # 34 tests, runs in ~0.02s — no real waiting, no real clock
```

---

## Requirements & design

**Framing the problem.** There was no spec, so I defined one. A CLI "alarm clock" really serves two everyday needs, and I scoped to exactly those:

1. *Wake me at a wall-clock time* → `07:30`
2. *Remind me after some time* → `10m`, `1h30m`

Everything else (snooze, labels, graceful cancel) supports those two without inventing scope.

**The one genuinely hard part is time math**, so that's where the engineering effort went:
- "07:30" should mean *the next* 07:30 — today if it's still ahead, tomorrow if it's passed. Edge case: exactly *now* rolls to tomorrow (you don't want an alarm that fires instantly).
- Durations compose: `1h30m`, `90s`, `1h30m15s`.
- Bad input must fail fast with a message a human can act on, not a stack trace.

**Deliberately cut** (with reasons — these were choices, not omissions):

| Not built | Why |
| --- | --- |
| Multiple concurrent / recurring alarms | Each needs a persistent store + a always-on scheduler. Big surface, little signal for a 30-min exercise. |
| Survives reboot / runs in background | A real always-on alarm belongs to the OS scheduler (`launchd`/`cron`/`systemd`), not a Python loop. Re-implementing that badly would be worse than not doing it. |
| Persistence / database | The brief says no database, and a foreground alarm needs no state. |
| A snooze via single keypress | Raw-key handling (`termios`) is platform-specific and fragile; a one-line `input()` prompt is portable and obvious. |

**Key decision — foreground, blocking process.** The alarm runs in your terminal and waits. This is the simplest *correct* model: no hidden daemons, no persisted state to corrupt, fully observable. The honest limitation (doesn't survive closing the terminal) is documented rather than papered over.

---

## Architecture

Logic is separated from I/O so the tricky parts are testable without real time or real sound:

```
alarm-clock/
├── alarm.py                 # CLI entry: argparse, friendly output, exit codes
└── alarmclock/
    ├── parsing.py           # PURE time math — takes `now` as an argument, no clock, no I/O
    ├── scheduler.py         # wait-until-target loop + snooze loop
    └── sound.py             # Ringer: loops a sound on a background thread
```

- **`parsing.py` never calls `datetime.now()`** — the caller injects "now". That single decision makes every interesting case (day rollover, equal-to-now, duration composition) a fast, deterministic unit test.
- **`scheduler.py` reads its clock and sleep through swappable indirections** (`_now`, `_sleep`), so tests drive a fake clock that only advances when asked — the snooze-re-arm path is verified in milliseconds, with zero real waiting.
- **`sound.py` rings on a daemon thread** so the main thread can wait for dismiss/snooze at the same time. It prefers macOS `afplay` (a built-in system sound) and falls back to the terminal bell `\a`, so it makes noise with no install and still degrades gracefully off-Mac.

---

## Validation

- **34 unit tests** cover the logic that's easy to get wrong: clock rollover, equal-to-now, single-digit hours, out-of-range times, duration formats, invalid input, the snooze re-arm loop, and "snooze pressed but no snooze configured." They use a pinned `now` and a fake clock — **no real time passes**.
- **Manual smoke tests** for the things tests shouldn't cover (real audio, real `Ctrl+C`): a 5-second alarm rings and dismisses; `Ctrl+C` exits cleanly with code 130; bad input prints a usage message and exits 2.
- **Edge cases considered:** midnight rollover, zero-length durations rejected, non-TTY/piped stdin treated as dismiss, no-audio machines fall back to the bell.

---

## How AI was used

Per the brief, AI drove the early thinking, and I directed and reviewed it:

1. **Requirements** — used AI to enumerate what a CLI alarm should/shouldn't do, then *narrowed* it to the two core use cases above rather than accepting the long feature list.
2. **Design** — chose the pure-core / injected-clock architecture specifically so the time logic is testable without sleeping; pushed back on suggestions that added persistence or a daemon as scope creep.
3. **Implementation** — generated the modules, then reviewed each: tightened error messages, made the ring loop responsive to `stop()` (so it doesn't keep playing after dismiss), and made stdin handling safe under pipes.
4. **Validation** — wrote tests first for the rollover/duration edge cases; one caught a wrong *test* expectation (`90s` → `1m 30s`, not `1m`), which I fixed rather than dumbing down the output.

The throughline: AI for breadth and first drafts, human judgment for **scope, correctness, and what to leave out**.

---

## What I'd add with more time

- Multiple named alarms backed by a small JSON store, with `list` / `cancel`.
- Recurring alarms (e.g. weekdays at 07:30) handed off to the OS scheduler.
- Packaging as a `pipx`-installable `alarm` command with an entry point.
- A configurable sound and volume.
