# Work Item ID
001

# Title
Genre classification fails to set lighting scenario

# State
Active

# Description
The show stays in the Song Start scenario for entire songs. Logs show the
classifier outputs no genre even though audio is playing. BPM-based fallback
is not applied so the scenario never changes.

# Steps to Reproduce
- Run `python main.py`.
- Start playing music.
- Observe console output. Genre remains blank and `State changed to Starting`
  repeats.
- Song continues without switching to any genre lighting scenario.

# Expected vs. Actual Results
Expected: After a few seconds of music the genre classifier predicts a label and
lighting shifts to the matching scenario. If classification fails a BPM-based
fallback should run.
Actual: Genre stays empty, leaving the show stuck in Song Start.

# Environment
- Windows 11
- Python 3.12
- sounddevice 0.4.6
- Run from PowerShell terminal.

# Solution Attempts
- Bundled the model locally under `models/music_genres_classification`.
- Added a verbose flag and AI logging to track model loading and predictions.
- `ai.log` records every state change and classification result without
  duplicates.
- Genre state resets when a new song begins so classification can run again.
- Fixed buffering logic to start classification after five seconds of audio.
- Reset stored genre on startup and clear persisted value.
- Keep a rolling 5-second buffer of audio before songs.
- Start classification immediately when a song becomes Ongoing.
- Guard threads with a song ID so results from old songs are dropped.
- Print state changes and genre results using the logging module.

# Solution
(Not solved yet)

# Implementation Proposal



