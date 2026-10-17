"""Landmarks near a ride."""
import json
import math

from ridemap.render import build_route_request, latlon

EARTH_RADIUS_M = 6_371_000.0
LABEL_MAX = 16  # MapDraw marker label limit


def load_landmarks(path):
    with open(path) as f:
        return json.load(f)


def haversine_m(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def nearest_points(track, landmarks):
    """[(name, index of nearest track point, meters)] in landmark order. O(L x T), fine for T in the thousands."""
    out = []
    for lm in landmarks:
        pos = (lm["lat"], lm["lon"])
        idx = min(range(len(track)), key=lambda i: haversine_m(pos, track[i]))
        out.append((lm["name"], idx, haversine_m(pos, track[idx])))
    return out


def short_label(name):
    return name if len(name) <= LABEL_MAX else name[:LABEL_MAX - 1].rstrip() + "…"


def build_landmark_request(track, landmarks, max_distance_m=250):
    body = build_route_request(track)
    for lm, (name, idx, meters) in zip(landmarks, nearest_points(track, landmarks)):
        if meters > max_distance_m:
            continue
        body["markers"].append({**latlon((lm["lat"], lm["lon"])), "label": short_label(name), "color": "orange"})
        body["paths"].append({"color": "black", "width": 2,
                              "points": [latlon((lm["lat"], lm["lon"])), latlon(track[idx])]})
    return body
