# Work Item ID
004

# Title
Genre classification sets lighting scenarios

# User Story
As an operator, I want the show to classify the music genre so that lighting
changes to a matching scenario automatically.

# Acceptance Criteria
- Given a new song begins,
  When five seconds of audio are buffered,
  Then the genre model runs in a background thread.
- Given the model returns a label,
  When classification completes,
  Then the corresponding scenario replaces Song Start and the result logs to
  `ai.log`.
