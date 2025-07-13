# Work Item ID
001

# Title
Genre classification fails to set lighting scenario

# State
Closed

# Description
The show stays in the Song Start scenario for entire songs. Logs show the
classifier outputs no genre even though audio is playing. BPM-based fallback
is not applied so the scenario never changes.

# Steps to Reproduce
- Run `python main.py`.
- Start playing music.
- Observe console output. Genre remains blank and `State changed to Starting`
  repeats.
- Song continues without switching to any genre lighting scenario.

# Expected vs. Actual Results
Expected: After a few seconds of music the genre classifier predicts a label and
lighting shifts to the matching scenario. Classification must succeed; simply
falling back to BPM is not acceptable.
Actual: Genre stays empty, leaving the show stuck in Song Start.

# Environment
- Windows 11
- Python 3.12
- sounddevice 0.4.6
- Run from PowerShell terminal.

# Solution Attempts
- Bundled the model locally under `models/music_genres_classification`.
- Added a verbose flag and AI logging to track model loading and predictions.
- `ai.log` records every state change and classification result without
  duplicates.
- Genre state resets when a new song begins so classification can run again.
- Buffer now starts only when a song reaches Ongoing and classification waits
  five seconds before launching.
- Reset stored genre on startup and clear persisted value.
- Keep a rolling 5-second buffer of audio before songs.
- Guard threads with a song ID so results from old songs are dropped.
- Print state changes and genre results using the logging module.

# Solution
Genre classification now retries every five seconds while the show
remains in the Song Start scenario. The song start duration was
increased to five seconds so the classifier works with a larger audio
sample. Once a genre is detected the show switches to the matching
scenario and resumes normal timing.

# Fix Proposal

## Observations from the Current Logs

The provided console log confirms the **genre remains blank** throughout the song and the lighting stays in the **“Song Start” scenario** instead of switching to a genre-specific scenario. For example, the dashboard prints **"Initial genre "** with nothing after it, and no genre is ever displayed during playback. The show repeatedly logs state transitions (“State changed to Starting” etc.) and beat detections (“Beat at ... BPM”), but never a genre prediction. According to the bug report, *“The show stays in the Song Start scenario for entire songs... classifier outputs no genre even though audio is playing. BPM-based fallback is not applied so the scenario never changes.”*. In other words, even after a song begins (and BPM is detected), the system **never logs a genre label or shifts out of the Song Start lighting scene**.

This suggests that the **genre classification step is not succeeding** – either it never runs properly or it runs but returns an empty result. The absence of any log like “Predicted genre label: X” in the console is telling. The code uses `logging.info` to report the predicted label (e.g., *“Predicted genre label: Rock”*) when the classifier returns a result. Since we don’t see that, it implies one of two things:

* **The classification thread never actually ran** (or exited early), so no prediction was made.
* **The classifier returned an empty prediction**, causing the label to be an empty string (and thus the console would log “Predicted genre label:” with nothing after it, which may have been easy to miss).

In either case, the lighting scenario remained stuck in `SONG_START` (the “Song Start” scene) instead of transitioning. The bug description confirms the *expected* behavior is that after a few seconds of music the classifier predicts a genre and the lighting shifts accordingly. This isn’t happening.

## Enhancing Logging for Diagnosis

To debug this issue, it’s crucial to add **more granular logging** around the genre classification process and state transitions. Currently, some logging to the file **`ai.log`** is implemented, but the console output and logs might not be telling the full story. Here are some improvements to implement:

* **Log State Changes to the AI Log and Console**: The code already prints state changes to the console (e.g. *“State changed to Starting”*). It would help to also record these in `ai.log` for a persistent record. In fact, the code has been updated to call `self._ai_log(f"State changed to {state.value}")` on each state change, which is good. Ensure this is working by checking `ai.log`. Each transition (Intermission → Starting → Ongoing → Ending, etc.) should be logged there. This will confirm the timing of when the song actually reaches the **ONGOING** state (which triggers classification).

* **Log Genre Classification Start/End**: We want to know if and when the classifier thread starts, and if it finishes. The code does call `_ai_log("Starting genre classification: X samples")` when launching the thread, and logs `"Genre classification finished"` at the end of the thread. However, these messages currently go only to `ai.log`. To make debugging easier, you could also print a console message or use `logging.info` for these events. For example, when starting classification, do something like:

  ```python
  logging.info(f"Starting genre classification on {samples.shape[0]} samples...")
  ```

  This will appear in the console (since `logging.basicConfig` is set to INFO) and let you know in real-time that the classifier was triggered. Likewise, logging when the classification thread finishes (and how long it took) can be informative.

* **Log Classifier Outcomes in Detail**: The classifier’s internal logging (with `verbose=True`) should print messages to console or `ai.log`. It will log when the model is loaded and each call to classify, including a message if no predictions were returned. Make sure you actually see these. For example, the classifier should print *“Loading genre model from ...”* the first time and *“Genre label returned: {label}”* or *“genre model returned no predictions”*. If these aren’t visible on the console, check the `ai.log` file. In the current design, **`ai.log` is the primary place where genre classifier details are recorded**. If `ai.log` remains nearly empty (only the “AI logging started” line), that indicates the classifier never ran or logged anything beyond initialization.

* **Surface Classification Skips**: There are conditions where `_launch_genre_classifier_immediately()` will **skip running the classifier** – for example, if the pre-song audio buffer is empty, or if a classification is already in progress. These conditions are logged to `ai.log` (e.g., *“Skipping classification: pre-song buffer empty”*). It would help to also print these skip reasons to the console or clearly to the log so you can catch them during a test. If, say, the buffer was empty at the moment of transition, you’d see that message and know why classification didn’t run. Consider temporarily adding a `print()` or `logging.warning()` in those branches for visibility.

* **Log Scenario Changes**: The code prints *“Genre changed to X”* on the console when a new lighting scenario is applied. This is great for seeing real-time changes. Additionally, the `_set_scenario` method already logs the scenario change to `ai.log`. Verify these logs appear so you know when the genre update occurs. Since the goal is to fix classification rather than use a fallback, any empty label should be treated as an error worth logging.

* **Include BPM info periodically** (optional): Logging the BPM around the time classification runs can help diagnose why a genre wasn’t detected. The system prints “Beat at XX BPM” on each beat. You might also log the average or last BPM reading when classification starts to correlate tempo with any classifier issues.

By implementing these logging improvements, you’ll have a much clearer picture in `ai.log` and console of the sequence: song state changes, classifier start, classifier result (or lack thereof), and scenario changes. The goal is that after the next run, you can **open `ai.log`** and see a timeline of events (with timestamps, ideally) that shows, for example:

* *State changed to STARTING* (song detected)
* *State changed to ONGOING* (song confirmed ongoing)
* *Starting genre classification: 88200 samples* (thread launched with \~2s of audio)
* *Genre model returned no predictions* (classifier didn’t identify a genre)
* *Predicted genre: **\[empty]*** (main thread got empty label)
* *Scenario: Song Ongoing – Slow* (fallback was triggered because no genre was detected)
* *Scenario changed to Song Ongoing – Slow* (this fallback behavior is not desired)
* … etc.

If you find entries like “Skipping classification: pre-song buffer empty” or no “Starting genre classification” at all, that tells us the classification didn’t run when expected.

## Diagnosing the Genre Classification Issue

With improved logging in place, you can pinpoint why the classifier isn’t yielding a genre. Based on the code and behavior, a few likely causes and solutions are:

* **Classification Trigger Timing**: Currently, the genre classifier is launched as soon as the song state switches to **ONGOING** (after \~2 seconds of sustained audio by default). That means it might be trying to classify using only the first \~2 seconds of audio. If the music has a quiet intro or the model needs more data, this could fail. In the bug notes, you intended to *“start classification after five seconds of audio”*. To do this, you have a 5-second `deque` buffer for pre-song audio, but the state machine still triggers at 2s. **Solution:** Consider increasing the `START_DURATION` for song start to 5 seconds (in `parameters.py`) so that `SongState.ONGOING` (and thus classification) only happens after 5 seconds of consistent audio. This gives the model a larger audio sample (up to 5s) to work with for genre prediction. For example, set `START_DURATION = 5.0` seconds instead of 2.0. This change would align with the 5-second buffer and likely improve the classifier’s output. If you don’t want to alter the state logic, another approach is to **delay the classification thread**: e.g., in `_handle_state_change`, you could launch a timer/thread to wait a few more seconds after Ongoing before calling `_launch_genre_classifier_immediately()` – but adjusting the parameter is simpler.

* **Ensuring Sufficient Audio in Buffer**: Related to the above, double-check that the **pre-song buffer** actually contains enough audio frames when classification runs. The code uses a 5s buffer (`maxlen=5*samplerate`). If the classifier still returns nothing, perhaps the buffer wasn’t full. Logging the sample count (which we already do when starting classification) will tell you how many samples were passed. If it’s significantly less than 5 seconds worth (220,500 samples at 44.1kHz), it means classification ran early. The fix is again to wait longer or require a minimum sample count before classifying. For instance, you could modify `_launch_genre_classifier_immediately` to skip if `samples.size < some_threshold`. As a quick test, try forcing the code to wait until the buffer is full: don’t call `_launch_genre_classifier_immediately()` on the first state change to Ongoing, but perhaps only call it after Ongoing has been sustained for a few seconds (you could set a flag when entering Ongoing and then check in the processing loop after a delay). This might be overkill if simply using 5s start duration solves it.

* **Model Output / Pipeline Issues**: If logging shows that the classifier did run on a decent chunk of audio but still returned an empty result (the `pipeline` gave `[]` or no label), then the issue may lie in the model or input format. The model you’re using (likely a Wav2Vec2-based genre classifier) should normally output a top prediction for any input audio. An empty result is unusual. Make sure the audio data is formatted correctly for the Hugging Face pipeline. The code passes `{"array": samples, "sampling_rate": sr}` to the `pipeline`, which is correct. If `samples` is very short or nearly silent, the pipeline might not produce a prediction. **Suggestion:** Test the classifier in isolation with a known audio sample (perhaps a WAV file of a song) to verify it predicts genres as expected. If it doesn’t, there may be an issue with the model checkpoint or the environment (e.g., missing dependencies for the model, though that would likely throw an error, not return empty). The logging around model loading (“Loading genre model from…”) will confirm the model is found and loaded. Also, ensure PyTorch or TensorFlow is installed (the code checks for `is_torch_available()` and will raise if not). Since you didn’t see any ImportError, it’s presumably using PyTorch fine.

* **Classification Finishing After Song End**: It’s possible the classification thread started, but by the time it finished, the song had already ended or changed state. The code only applies the new scenario if the song is still in Ongoing state when the result comes back. If the song went to ENDING/INTERMISSION before the classifier returned, the genre label is effectively ignored (no scenario change). The log snippet actually shows the song ending relatively soon (it hit an Ending state around the time BPM spiked) without any genre change. If your classifier model is heavy, it might take a few seconds to run – enough that the song ended first. **Solution:** You might need to account for this race condition. For instance, if the song ends while classification is in progress, maybe still apply the result at least for the record or for the next song. At minimum, log that “classification result came after song ended, ignoring.” However, a better approach is to try to get the classification done earlier (by feeding it audio sooner, as above). Using a 5-second window early in the song is typically sufficient for a genre guess. If the first song was very short or stopped, that could also explain it. Keep an eye on the timestamps in `ai.log` (add timestamps if not present) to see how long classification took versus the song duration.

* **Focus on Fixing Classification**: Earlier drafts suggested creating a BPM-based
  fallback if the classifier returned no label. This bug now explicitly requires
  solving the root cause of the missing genre prediction instead of relying on a
  fallback. Ensure the classifier reliably returns a genre so the show can switch
  to the correct scenario.

* **Verify Reset for Subsequent Songs**: You already fixed the logic to reset `last_genre` on a new song start, which ensures the classifier will run for each new song (good). Make sure that’s working by checking that when the state went from Ending back to Starting for the next song, `last_genre` became `None` and `classifying` flag reset. The logs show multiple “State changed to Starting” events, which likely correspond to new song detections, so that part seems okay.

In summary, the likely root issue is **timing/insufficient data for the classifier**. The lights stayed in the “Song Start” scene because the classifier didn’t output a genre in time (or at all). Focus on improving the classification timing and reliability so the show transitions to the correct genre without relying on BPM-based fallbacks.
