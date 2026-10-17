"""serving_features: the last-hour pickup count, computed the way the serving service computes it.

The service keeps each zone's recent pickups in memory, fed by the trip stream, and answers one
request at a time. serving_counts() replays January through that code: the stream and the
requests in time order, one count per request.
"""
from collections import defaultdict, deque

import numpy as np
import pandas as pd

HOUR = pd.Timedelta(1, unit="h")


class ZoneWindows:
    """Each zone's recent pickup times, oldest first."""

    def __init__(self):
        self.recent = defaultdict(deque)

    def add(self, zone, pickup_time):
        self.recent[zone].append(pickup_time)

    def last_hour(self, zone, request_time):
        now = request_time.tz_localize("America/New_York").tz_convert("UTC").tz_localize(None)
        window = self.recent[zone]
        while window and window[0] <= now - HOUR:
            window.popleft()
        return len(window)


def serving_counts(events, queries):
    """Pickups in each query's zone in the last hour: one count per query, in query order.

    events: every pickup (columns zone and time), sorted by time. This is the stream.
    queries: the requests (columns zone and time), sorted by time.
    """
    store, counts = ZoneWindows(), np.zeros(len(queries), dtype=np.int64)
    stream = zip(events["zone"].to_numpy(), events["time"])
    zone, time = next(stream, (None, None))
    for k, (q_zone, q_time) in enumerate(zip(queries["zone"].to_numpy(), queries["time"])):
        while time is not None and time <= q_time:
            store.add(zone, time)
            zone, time = next(stream, (None, None))
        counts[k] = store.last_hour(q_zone, q_time)
    return counts
