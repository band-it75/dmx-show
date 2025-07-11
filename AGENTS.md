# Repository Guidelines

- Keep documentation lines under 100 characters when possible.
- After modifying Python files, run `pytest -q` to ensure no errors occur.
- When documenting show cues, mention:
  - LumiPar 12UAW5 units double as house lights
  - Overhead effects pulse with BPM
  - Smoke bursts last 3 seconds with a 30-second gap
  - Genre-specific colors, intensities and timing
  - Moving head stays on artist during songs and points at the audience to end
    each song
  - Stage lights fade to black during songs and return when the moving head
    faces the audience
- Avoid cues that rely on detecting solos or other musical details the
   software cannot sense
  - Chorus and crescendo detection uses a 0.5-second debounce to avoid
    flicker
  - `DMX_FPS` sets how many DMX frames are transmitted per second
