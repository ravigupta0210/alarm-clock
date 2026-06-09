"""Audible ringing — isolated so the rest of the app stays testable.

The :class:`Ringer` plays a sound on a loop in a background daemon thread so
the main thread can simultaneously wait for the user to dismiss/snooze.

Playback strategy, in order of preference:

1. ``afplay`` with a macOS system sound  (rich audio, present on every Mac)
2. ASCII terminal bell ``"\\a"``          (universal fallback, no deps)

This keeps the project pure-stdlib while still making real noise on the
machine it was built for.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import threading
import time

# A standard macOS system sound — exists on every stock install.
_MAC_SOUND = "/System/Library/Sounds/Glass.aiff"


class Ringer:
    """Loops an alarm sound until :meth:`stop` is called."""

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._afplay = shutil.which("afplay")

    @property
    def backend(self) -> str:
        """Human-readable name of the playback backend in use."""
        return "afplay" if self._afplay else "terminal-bell"

    def start(self) -> None:
        """Begin ringing on a background thread (no-op if already ringing)."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop ringing and wait briefly for the thread to wind down."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop.is_set():
            if self._afplay:
                # Run afplay but stay responsive to stop: poll the process.
                proc = subprocess.Popen(
                    [self._afplay, _MAC_SOUND],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                while proc.poll() is None:
                    if self._stop.is_set():
                        proc.terminate()
                        break
                    time.sleep(0.1)
            else:
                # Fallback: write the bell character and flush.
                sys.stdout.write("\a")
                sys.stdout.flush()
                self._stop.wait(1.0)
