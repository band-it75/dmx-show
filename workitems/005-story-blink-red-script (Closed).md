# Work Item ID
005

# Title
Provide blink_red.py demo script

# State
Closed

# User Story
As a Karaoke Host, I want a simple script to flash a LumiPar 7UTRI so that I can test
DMX output without running the full show.

# Acceptance Criteria
- Given the repository is installed,
  When I run `python blink_red.py --port COM4 --start-address 1 --blink-times 3`,
  Then the fixture flashes red three times and exits.
- Given a missing command argument,
  When the script starts,
  Then it prints usage instructions.

# Implementation Proposal



