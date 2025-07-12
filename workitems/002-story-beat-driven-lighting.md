# Work Item ID
002

# Title
Beat-driven lighting scenarios

# State
New

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



