# Work Item ID
006

# Title
Apply BPM-based scenario when genre is unknown

# State
New

# User Story
As a Karaoke Host, I want the show to select a scenario by BPM if genre
classification fails so that lighting does not remain stuck in Song Start.

# Acceptance Criteria
- Given a song stays in Ongoing state for five seconds with no genre label,
  When classification did not run or returned empty,
  Then the system calls `scenario_for_bpm` to pick the closest scenario.
- Given the fallback applies,
  When the song later gets classified,
  Then the genre scenario replaces the BPM choice.

# Implementation Proposal



