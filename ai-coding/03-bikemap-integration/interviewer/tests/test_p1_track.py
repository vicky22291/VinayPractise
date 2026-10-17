import json
import os
import tempfile
import unittest

from mapdraw_harness import RIDE, raw_ride_points, run_cli
from ridemap.errors import TrackError
from ridemap.track import load_track


def write(tmp, name, content):
    path = os.path.join(tmp, name)
    with open(path, "w") as f:
        f.write(content if isinstance(content, str) else json.dumps(content))
    return path


def feature(coords):
    return {"type": "Feature", "properties": {}, "geometry": {"type": "LineString", "coordinates": coords}}


class LoadTrack(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_ride_is_lat_lon_tuples(self):
        track = load_track(RIDE)
        self.assertEqual(len(track), 495)
        self.assertEqual(track[:10], raw_ride_points()[:10])
        for p in track:
            self.assertIsInstance(p, tuple)
            self.assertEqual(len(p), 2)
            self.assertIsInstance(p[0], float)
            self.assertIsInstance(p[1], float)

    def test_lat_comes_first(self):
        lat, lon = load_track(RIDE)[0]
        self.assertAlmostEqual(lat, 37.66, places=4)
        self.assertAlmostEqual(lon, -122.381264, places=4)

    def test_two_element_positions(self):
        path = write(self.tmp, "a.json", feature([[-122.0, 37.0], [-122.1, 37.1]]))
        self.assertEqual(load_track(path), [(37.0, -122.0), (37.1, -122.1)])

    def test_integer_coordinates_become_floats(self):
        path = write(self.tmp, "a.json", feature([[-122, 37], [-121, 38]]))
        self.assertEqual(load_track(path), [(37.0, -122.0), (38.0, -121.0)])
        self.assertIsInstance(load_track(path)[0][0], float)

    def test_bare_linestring(self):
        path = write(self.tmp, "a.json", {"type": "LineString", "coordinates": [[-122.0, 37.0, 5], [-122.1, 37.1, 6]]})
        self.assertEqual(load_track(path), [(37.0, -122.0), (37.1, -122.1)])

    def test_bad_files_raise_track_error(self):
        cases = {
            "missing": None,
            "not json": "{not json",
            "point geometry": {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-122.0, 37.0]}},
            "no geometry": {"type": "Feature", "properties": {}},
            "one point": feature([[-122.0, 37.0]]),
            "empty": feature([]),
            "short position": feature([[-122.0], [-122.1, 37.1]]),
            "string coordinate": feature([["-122.0", "37.0"], [-122.1, 37.1]]),
            "lat out of range (swapped file)": feature([[37.0, -122.0], [37.1, -122.1]]),
            "lon out of range": feature([[-190.0, 37.0], [-122.1, 37.1]]),
            "coordinates not a list": {"type": "LineString", "coordinates": "abc"},
            "json array": [1, 2, 3],
        }
        for label, content in cases.items():
            with self.subTest(label):
                path = os.path.join(self.tmp, "nope.json") if content is None else write(self.tmp, "bad.json", content)
                with self.assertRaises(TrackError):
                    load_track(path)


class Part1Cli(unittest.TestCase):
    def test_prints_first_ten(self):
        r = run_cli("part1")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.strip().splitlines()
        expected = [f"{lat:.6f}, {lon:.6f}" for lat, lon in raw_ride_points()[:10]]
        self.assertEqual(lines, expected)

    def test_explicit_path(self):
        r = run_cli("part1", RIDE)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(r.stdout.strip().splitlines()), 10)

    def test_missing_file_is_clean_error(self):
        r = run_cli("part1", "data/does-not-exist.json")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)
        self.assertTrue(r.stderr.lower().startswith("error:"), r.stderr)

    def test_malformed_file_is_clean_error(self):
        tmp = tempfile.mkdtemp()
        path = write(tmp, "bad.json", "{oops")
        r = run_cli("part1", path)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
