class DebouncedFlag:
    """Boolean state that changes only after a stable interval."""

    def __init__(self, debounce_time: float = 0.5) -> None:
        self.debounce = debounce_time
        self.state = False
        self._on_since: float | None = None
        self._off_since: float | None = None

    def update(self, observed: bool, now: float) -> bool:
        """Return debounced state for the observed boolean."""
        if observed:
            self._off_since = None
            if self._on_since is None:
                self._on_since = now
            if not self.state and now - self._on_since >= self.debounce:
                self.state = True
        else:
            self._on_since = None
            if self._off_since is None:
                self._off_since = now
            if self.state and now - self._off_since >= self.debounce:
                self.state = False
        return self.state
