# Work Item ID
002

# Title
Beat-driven lighting scenarios

# State
Active

# User Story
As a Karaoke Host, I want the lights to react to beats and song states so that the
show energy matches the music.

# Acceptance Criteria
- Given the show is running,
  When music plays and beat detection triggers,
  Then DMX groups update using the current scenario's beat mapping.
- Given a song starts or ends,
  When the audio volume thresholds are met,
  Then the scenario transitions follow the defined state machine.

# Implementation Proposal

* Integrate beat detection events with the scenario engine.
* Map each beat to DMX group updates defined in `parameters.py`.
* Ensure state transitions continue to follow the song state machine.

