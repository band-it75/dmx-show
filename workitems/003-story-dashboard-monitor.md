# Work Item ID
003

# Title
Dashboard shows real-time audio and lighting status

# State
Active

# User Story
As a Karaoke Host, I want a console dashboard that displays BPM, VU and cue states
so that I can monitor the show at a glance.

# Acceptance Criteria
- Given dashboard mode is enabled,
  When the show runs,
  Then BPM, VU levels, smoke state and active groups refresh on screen.
- Given chorus or crescendo detection triggers,
  When those flags change,
  Then the dashboard highlights them without flicker.

# Implementation Proposal

* Build a curses-based dashboard to render BPM, VU and scenario data.
* Update the display each loop using metrics from the main application.
* Highlight chorus and crescendo flags with minimal flicker.

