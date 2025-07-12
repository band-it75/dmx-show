# Work Item ID
009

# Title
Song Start transitions back to Intermission unexpectedly

# State
Active

# Description
After a song starts the lights enter the Song Start scenario. A moment later
Intermission is triggered again even though this transition is disallowed.

# Steps to Reproduce
1. Run `python main.py`.
2. Play a short burst of loud audio.
3. Watch the console log: "State changed to Starting" then "State changed to
   Intermission".
4. Intermission lighting values are applied despite never reaching Song Ending.

# Expected vs. Actual Results
Expected: The Song Start scenario stays active until the song reaches Ending or a
valid successor.
Actual: The scenario reverts directly to Intermission.

# Proposed Fix
`_set_scenario` checks allowed transitions using the incoming value `name`. When
`name` is not the canonical enum instance the comparison fails, letting the
change through. Compare using the resolved variable `scn` instead:

```python
current = self.scenario
if (
    not force
    and scn != current
    and (current not in scn.predecessors or scn not in current.successors)
):
    return
```

This enforces the intended transition rules.
