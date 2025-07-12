# Work Item ID
004

# Title
Genre classification sets lighting scenarios

# State
New

# User Story
As a Karaoke Host, I want the show to classify the music genre so that lighting
changes to a matching scenario automatically.

# Acceptance Criteria
- Given a new song begins,
  When five seconds of audio are buffered,
  Then the genre model runs in a background thread.
- Given the model returns a label,
  When classification completes,
  Then the corresponding scenario replaces Song Start and the result logs to
  `ai.log`.

# Implementation Proposal



