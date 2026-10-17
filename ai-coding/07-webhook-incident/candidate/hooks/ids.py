"""Sequential ids such as evt_000001. Deterministic, so logs and tests are stable."""


class IdGenerator:
    def __init__(self):
        self._counters = {}

    def new(self, prefix):
        n = self._counters.get(prefix, 0) + 1
        self._counters[prefix] = n
        return f"{prefix}_{n:06d}"
