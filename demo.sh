#!/usr/bin/env bash
#
# demo.sh — a guided walkthrough of the alarm clock, one scenario at a time.
# Pauses between scenarios so you can narrate (great for a screen recording).
#
# Usage:
#   bash demo.sh [ALARM_TIME] [SNOOZE_TIME] [CANCEL_TIME]
#
# All arguments are optional and accept any spec the app understands
# (e.g. 5s, 30s, 2m, 1h30m). Defaults shown in brackets.
#
# Examples:
#   bash demo.sh              # alarm 5s,  snooze 5s,  cancel 30s
#   bash demo.sh 10s          # alarm 10s, snooze 5s,  cancel 30s
#   bash demo.sh 10s 3s       # alarm 10s, snooze 3s,  cancel 30s
#   bash demo.sh 8s 4s 20s    # set all three
#
set -u

PY=python3
ALARM="${1:-5s}"      # how long until each alarm rings
SNOOZE="${2:-5s}"     # how long a snooze lasts
CANCEL="${3:-30s}"    # length of the alarm you'll cancel with Ctrl+C

pause() { echo; read -r -p "▶︎  Press Enter to start this scenario… "; echo; }
line()  { echo "------------------------------------------------------------"; }

clear
echo "🎬  Alarm clock — live demo   (alarm=$ALARM  snooze=$SNOOZE  cancel=$CANCEL)"
line
echo "Three short scenarios:"
echo "  1) ${ALARM} alarm  → press ENTER to DISMISS"
echo "  2) ${ALARM} alarm  → press 's' then ENTER to SNOOZE (${SNOOZE}), then ENTER to dismiss"
echo "  3) ${CANCEL} alarm → press Ctrl+C to CANCEL before it rings"
line

# ----------------------------------------------------------------------------
echo
echo "①  DISMISS — a ${ALARM} alarm."
echo "    When it rings, just press ENTER. The sound stops and it exits."
pause
$PY alarm.py "$ALARM" --label "Dismiss me"

# ----------------------------------------------------------------------------
echo
line
echo "②  SNOOZE — a ${ALARM} alarm with a ${SNOOZE} snooze."
echo "    When it rings, type:  s  then ENTER."
echo "    It re-arms for ${SNOOZE} and rings AGAIN — that time, press ENTER to dismiss."
pause
$PY alarm.py "$ALARM" --label "Snooze me" --snooze "$SNOOZE"

# ----------------------------------------------------------------------------
echo
line
echo "③  CANCEL — a ${CANCEL} alarm you stop early."
echo "    While it's counting down, press Ctrl+C. It exits cleanly (no ring)."
pause
$PY alarm.py "$CANCEL" --label "You won't hear me"

# ----------------------------------------------------------------------------
echo
line
echo "✅  Demo complete."
