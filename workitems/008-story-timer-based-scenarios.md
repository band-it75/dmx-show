# Work Item ID
008

# Title
Support timer-based color transitions in scenarios

# State
Active

# User Story
As a Karaoke Host, I want scenarios to define beat, chorus and timed color
changes so that complex cues run without code changes.

# Acceptance Criteria
- Given a scenario includes a `timer` entry,
  When the specified seconds elapse after entering the scenario,
  Then colors fade from the `from` values to the `to` values over the duration.
- Given `beat` or `snare_hit` events exist,
  When those audio events occur,
  Then the configured groups update for the specified duration.

# Implementation Proposal

* Extend scenario definitions with a `timer` section for timed transitions.
* Schedule color fades using the main loop and current DMX FPS value.
* Combine timer events with beat or chorus triggers for complex cues.

