import json
import math
import os
import tempfile
import unittest

import mapdraw_harness as h
from ridemap.landmarks import build_landmark_request, nearest_points
from ridemap.mapdraw import MapDrawClient
from ridemap.track import load_track

LANDMARKS = os.path.join(h.RUN, "data", "landmarks.json")


def haversine(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371000.0 * math.asin(math.sqrt(x))


class Part5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = h.start()
        cls.track = load_track(h.RIDE)
        with open(LANDMARKS) as f:
            cls.landmarks = json.load(f)
        cls.dist = [[haversine((lm["lat"], lm["lon"]), p) for p in cls.track] for lm in cls.landmarks]

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def in_range(self, limit=250):
        return {lm["name"] for lm, d in zip(self.landmarks, self.dist) if min(d) <= limit}

    def test_nearest_points(self):
        got = nearest_points(self.track, self.landmarks)
        self.assertEqual([g[0] for g in got], [lm["name"] for lm in self.landmarks])
        for (name, idx, meters), d in zip(got, self.dist):
            with self.subTest(name=name):
                self.assertLessEqual(d[idx], min(d) + 0.5)
                self.assertAlmostEqual(meters, min(d), delta=1.0)

    def test_request_annotates_landmarks_in_range(self):
        body = build_landmark_request(self.track, self.landmarks)
        expected = self.in_range()
        self.assertEqual(len(expected), 6)
        orange = [m for m in body["markers"] if m.get("color") == "orange"]
        self.assertEqual(len(orange), len(expected))
        by_pos = {(lm["lat"], lm["lon"]): lm["name"] for lm in self.landmarks}
        for m in orange:
            name = by_pos[(m["lat"], m["lon"])]
            self.assertIn(name, expected)
            label = m.get("label", "")
            self.assertTrue(0 < len(label) <= 16, label)
            self.assertTrue(name.startswith(label.rstrip(".… ")), (name, label))
        black = [p for p in body["paths"] if p.get("color") == "black"]
        self.assertEqual(len(black), len(expected))
        for p in black:
            ends = {(q["lat"], q["lon"]) for q in p["points"]}
            self.assertEqual(len(p["points"]), 2)
            lm_end = [e for e in ends if e in by_pos]
            self.assertEqual(len(lm_end), 1)
            i = [lm["name"] for lm in self.landmarks].index(by_pos[lm_end[0]])
            track_end = (ends - set(lm_end)).pop()
            self.assertLessEqual(self.dist[i][self.track.index(track_end)], min(self.dist[i]) + 0.5)

    def test_keeps_part3_content(self):
        body = build_landmark_request(self.track, self.landmarks)
        labels = {m.get("label") for m in body["markers"]}
        self.assertTrue({"Start", "Stripe"} <= labels)
        self.assertEqual(sum(1 for p in body["paths"] if p.get("color") in ("blue", "brown")), 50)

    def test_max_distance_param(self):
        body = build_landmark_request(self.track, self.landmarks, max_distance_m=60)
        orange = [m for m in body["markers"] if m.get("color") == "orange"]
        self.assertEqual(len(orange), len(self.in_range(60)))

    def test_mapdraw_accepts_it(self):
        png = MapDrawClient(self.srv.url, h.KEY).render(build_landmark_request(self.track, self.landmarks))
        self.assertTrue(png.startswith(h.PNG_SIG))

    def test_cli_writes_png(self):
        out = os.path.join(tempfile.mkdtemp(), "bikemap5.png")
        r = h.run_cli("part5", "--out", out, url=self.srv.url)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, "rb") as f:
            self.assertTrue(f.read().startswith(h.PNG_SIG))


if __name__ == "__main__":
    unittest.main()
