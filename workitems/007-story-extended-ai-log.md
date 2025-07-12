# Work Item ID
007

# Title
Timestamped AI log with beat entries

# State
Active

# User Story
As a Karaoke Host, I want `ai.log` to include timestamps and occasional BPM lines so
that I can trace show behavior after a performance.

# Acceptance Criteria
- Given the show runs,
  When any message is written to `ai.log`,
  Then each line includes a timestamp.
- Given BPM printing occurs every few seconds,
  When a new estimate is shown on console,
  Then the same line is appended to `ai.log`.

# Implementation Proposal

* Add a helper function that writes timestamped lines to `ai.log`.
* Call this helper for all console messages and periodic BPM reports.
* Keep each log entry under 100 characters for readability.

