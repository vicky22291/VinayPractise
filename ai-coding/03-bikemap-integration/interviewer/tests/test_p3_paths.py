import os
import tempfile
import unittest

import mapdraw_harness as h
from ridemap.mapdraw import MapDrawClient
from ridemap.render import build_route_request
from ridemap.track import load_track


def pt(p):
    return {"lat": p[0], "lon": p[1]}


def synthetic(n):
    return [(37.0 + i * 0.001, -122.0 - i * 0.001) for i in range(n)]


class Part3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = h.start()
        cls.track = load_track(h.RIDE)

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def test_frame_matches_part2(self):
        body = build_route_request(self.track)
        self.assertEqual(body["size"], {"width": 800, "height": 600})
        self.assertEqual(body["zoom"], 14)
        lat, lon = h.bbox_center(self.track)
        self.assertAlmostEqual(body["center"]["lat"], lat, places=6)
        self.assertAlmostEqual(body["center"]["lon"], lon, places=6)

    def test_paths_alternate_every_ten_segments(self):
        paths = build_route_request(self.track)["paths"]
        self.assertEqual(len(paths), 50)  # 494 segments
        for i, p in enumerate(paths):
            with self.subTest(path=i):
                self.assertEqual(p["color"], "blue" if i % 2 == 0 else "brown")
                self.assertEqual([(q["lat"], q["lon"]) for q in p["points"]], self.track[10 * i:10 * i + 11])
        self.assertEqual(len(paths[-1]["points"]), 5)

    def test_no_gaps_between_paths(self):
        paths = build_route_request(self.track)["paths"]
        for a, b in zip(paths, paths[1:]):
            self.assertEqual(a["points"][-1], b["points"][0])
        drawn = sum(len(p["points"]) - 1 for p in paths)
        self.assertEqual(drawn, len(self.track) - 1)

    def test_short_and_exact_tracks(self):
        self.assertEqual(len(build_route_request(synthetic(2))["paths"]), 1)
        paths = build_route_request(synthetic(21))["paths"]
        self.assertEqual(len(paths), 2)
        self.assertEqual([p["color"] for p in paths], ["blue", "brown"])
        self.assertEqual(len(build_route_request(synthetic(22))["paths"]), 3)

    def test_markers(self):
        markers = {m.get("label"): m for m in build_route_request(self.track)["markers"]}
        start, office = markers["Start"], markers["Stripe"]
        self.assertEqual((start["lat"], start["lon"]), self.track[0])
        self.assertEqual(start.get("color"), "green")
        self.assertEqual((office["lat"], office["lon"]), (37.6627, -122.3891))
        self.assertEqual(office.get("color"), "purple")

    def test_mapdraw_accepts_it(self):
        png = MapDrawClient(self.srv.url, h.KEY).render(build_route_request(self.track))
        self.assertTrue(png.startswith(h.PNG_SIG))

    def test_cli_writes_png(self):
        out = os.path.join(tempfile.mkdtemp(), "bikemap3.png")
        r = h.run_cli("part3", "--out", out, url=self.srv.url)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, "rb") as f:
            self.assertTrue(f.read().startswith(h.PNG_SIG))
        body = self.srv.state.render_posts()[-1]["json"]
        self.assertEqual(len(body["paths"]), 50)


if __name__ == "__main__":
    unittest.main()
