# Default configuration parameters for DMX and beat detection

# Audio settings
SAMPLERATE = 44100

# Volume-based song state detection
AMPLITUDE_THRESHOLD = 0.02  # RMS amplitude considered "loud"
START_DURATION = 2.0        # seconds of sustained volume to mark song start
END_DURATION = 3.0          # seconds of quiet to mark song end

# DMX blink script defaults
UNIVERSE = 1
CHANNEL = 1
