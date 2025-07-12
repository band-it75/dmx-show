# Work Item ID
001

# Title
Genre classification fails to set lighting scenario

# State
Active

# Description:
The show stays in the Song Start scenario for entire songs. Logs show the
classifier outputs no genre even though audio is playing. BPM-based fallback
is not applied so the scenario never changes.

# Steps to Reproduce:
- Run `python main.py`.
- Start playing music.
- Observe console output. Genre remains blank and `State changed to Starting`
  repeats.
- Song continues without switching to any genre lighting scenario.

# Expected vs. Actual Results:
Expected: After a few seconds of music the genre classifier predicts a label and
lighting shifts to the matching scenario. If classification fails a BPM-based
fallback should run.
Actual: Genre stays empty, leaving the show stuck in Song Start.

# Environment:
- Windows 11
- Python 3.12
- sounddevice 0.4.6
- Run from PowerShell terminal.
