"""Load a recorded ride."""
import json
import math

from ridemap.errors import TrackError


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def load_track(path):
    """Return the ride at `path` as a list of (lat, lon) floats.

    GeoJSON positions are [lon, lat] with an optional elevation, so the order is
    swapped here, once, and nowhere else.
    """
    try:
        with open(path) as f:
            ride = json.load(f)
    except FileNotFoundError:
        raise TrackError(f"no such ride file: {path}") from None
    except (OSError, ValueError) as e:
        raise TrackError(f"cannot read {path}: {e}") from None

    geometry = ride.get("geometry") if isinstance(ride, dict) and ride.get("type") == "Feature" else ride
    if not isinstance(geometry, dict) or geometry.get("type") != "LineString":
        raise TrackError(f"{path}: expected a LineString or a Feature with a LineString geometry")
    coords = geometry.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        raise TrackError(f"{path}: a ride needs at least two points")

    track = []
    for i, pos in enumerate(coords):
        if not isinstance(pos, list) or len(pos) not in (2, 3) or not all(_is_number(v) for v in pos):
            raise TrackError(f"{path}: point {i} is not a [lon, lat] position: {pos!r}")
        lon, lat = float(pos[0]), float(pos[1])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise TrackError(f"{path}: point {i} is out of range (is the file [lat, lon]?): {pos!r}")
        track.append((lat, lon))
    return track
