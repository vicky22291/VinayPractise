"""Load a recorded ride."""
import json


def load_track(path):
    """Return the points of the ride stored at `path`."""
    with open(path) as f:
        ride = json.load(f)
    return ride["geometry"]["coordinates"]
