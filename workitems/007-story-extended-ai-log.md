# Work Item ID
007

# Title
Timestamped AI log with beat entries

# User Story
As a developer, I want `ai.log` to include timestamps and occasional BPM lines so
that I can trace show behavior after a performance.

# Acceptance Criteria
- Given the show runs,
  When any message is written to `ai.log`,
  Then each line includes a timestamp.
- Given BPM printing occurs every few seconds,
  When a new estimate is shown on console,
  Then the same line is appended to `ai.log`.
