"""The tests a strong candidate writes along the way."""
import json
import os
import tempfile
import unittest

from ridemap.errors import TrackError
from ridemap.render import build_route_request
from ridemap.track import load_track


def ride(coords):
    return {"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords}}


class TrackTest(unittest.TestCase):
    def load(self, obj):
        path = os.path.join(tempfile.mkdtemp(), "r.json")
        with open(path, "w") as f:
            json.dump(obj, f)
        return load_track(path)

    def test_swaps_to_lat_lon_and_drops_elevation(self):
        self.assertEqual(self.load(ride([[-122.0, 37.0, 9.5], [-122.1, 37.1, 10]])), [(37.0, -122.0), (37.1, -122.1)])

    def test_lat_lon_file_is_rejected(self):
        with self.assertRaises(TrackError):
            self.load(ride([[37.0, -122.0], [37.1, -122.1]]))

    def test_single_point_rejected(self):
        with self.assertRaises(TrackError):
            self.load(ride([[-122.0, 37.0]]))


class RouteTest(unittest.TestCase):
    def test_paths_share_endpoints(self):
        track = [(37.0 + i / 1000, -122.0) for i in range(25)]
        paths = build_route_request(track)["paths"]
        self.assertEqual([len(p["points"]) for p in paths], [11, 11, 5])
        self.assertEqual(paths[0]["points"][-1], paths[1]["points"][0])


if __name__ == "__main__":
    unittest.main()
