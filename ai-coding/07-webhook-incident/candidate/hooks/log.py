"""One key=value line per log record, timestamped by the injected clock."""
import datetime


def _fmt(value):
    text = str(value)
    if text == "" or any(c in text for c in ' ="'):
        return '"' + text.replace('"', "'") + '"'
    return text


class Logger:
    """Writes to `sink` (a list, or anything with write()). Keeps lines in memory by default."""

    def __init__(self, clock, sink=None):
        self.clock = clock
        self.sink = [] if sink is None else sink

    def _emit(self, level, msg, fields):
        ts = datetime.datetime.fromtimestamp(self.clock.now(), datetime.timezone.utc)
        parts = [ts.strftime("%Y-%m-%dT%H:%M:%SZ"), level, msg]
        parts += [f"{k}={_fmt(v)}" for k, v in fields.items()]
        line = " ".join(parts)
        if hasattr(self.sink, "write"):
            self.sink.write(line + "\n")
        else:
            self.sink.append(line)

    def info(self, msg, **fields):
        self._emit("INFO", msg, fields)

    def warn(self, msg, **fields):
        self._emit("WARN", msg, fields)

    def error(self, msg, **fields):
        self._emit("ERROR", msg, fields)
