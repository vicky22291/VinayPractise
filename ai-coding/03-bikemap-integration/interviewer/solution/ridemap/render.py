"""Build MapDraw request bodies. Pure functions: no I/O, easy to test."""

WIDTH, HEIGHT, ZOOM = 800, 600, 14
SEGMENTS_PER_PATH = 10
PATH_COLORS = ("blue", "brown")
STRIPE_OFFICE = (37.6627, -122.3891)


def latlon(point):
    lat, lon = point
    return {"lat": lat, "lon": lon}


def bbox_center(track):
    lats = [p[0] for p in track]
    lons = [p[1] for p in track]
    return (min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2


def build_basic_request(track):
    return {
        "size": {"width": WIDTH, "height": HEIGHT},
        "center": latlon(bbox_center(track)),
        "zoom": ZOOM,
    }


def build_route_request(track):
    body = build_basic_request(track)
    body["markers"] = [
        {**latlon(track[0]), "label": "Start", "color": "green"},
        {**latlon(STRIPE_OFFICE), "label": "Stripe", "color": "purple"},
    ]
    # Path i covers segments [10i, 10i + 10), so points [10i, 10i + 10]
    # inclusive: neighbouring paths share an endpoint and leave no gap.
    body["paths"] = [
        {"color": PATH_COLORS[i % len(PATH_COLORS)],
         "points": [latlon(p) for p in track[start:start + SEGMENTS_PER_PATH + 1]]}
        for i, start in enumerate(range(0, len(track) - 1, SEGMENTS_PER_PATH))
    ]
    return body
