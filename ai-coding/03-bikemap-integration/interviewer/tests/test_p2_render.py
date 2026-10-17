import os
import tempfile
import unittest

import mapdraw_harness as h
from ridemap.errors import MapDrawError
from ridemap.mapdraw import MapDrawClient
from ridemap.render import build_basic_request
from ridemap.track import load_track


class Part2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = h.start()
        cls.track = load_track(h.RIDE)

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def test_basic_request_shape(self):
        body = build_basic_request(self.track)
        self.assertEqual(body["size"], {"width": 800, "height": 600})
        self.assertEqual(body["zoom"], 14)
        lat, lon = h.bbox_center(h.raw_ride_points())
        self.assertAlmostEqual(body["center"]["lat"], lat, places=6)
        self.assertAlmostEqual(body["center"]["lon"], lon, places=6)
        self.assertFalse(body.get("markers"))
        self.assertFalse(body.get("paths"))

    def test_render_returns_png_bytes(self):
        png = MapDrawClient(self.srv.url, h.KEY).render(build_basic_request(self.track))
        self.assertIsInstance(png, bytes)
        self.assertTrue(png.startswith(h.PNG_SIG))
        last = self.srv.state.render_posts()[-1]
        self.assertEqual(last["headers"].get("authorization"), "Bearer " + h.KEY)
        self.assertTrue(last["headers"].get("content-type", "").startswith("application/json"))

    def test_error_raises_mapdraw_error_with_status(self):
        body = dict(build_basic_request(self.track), zoom=99)
        with self.assertRaises(MapDrawError) as ctx:
            MapDrawClient(self.srv.url, h.KEY).render(body)
        self.assertEqual(ctx.exception.status, 400)
        self.assertIn("zoom", str(ctx.exception))

    def test_bad_key_is_401(self):
        with self.assertRaises(MapDrawError) as ctx:
            MapDrawClient(self.srv.url, "md_test_wrong").render(build_basic_request(self.track))
        self.assertEqual(ctx.exception.status, 401)

    def test_cli_writes_png(self):
        out = os.path.join(tempfile.mkdtemp(), "bikemap2.png")
        before = self.srv.state.billed
        r = h.run_cli("part2", "--out", out, url=self.srv.url)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, "rb") as f:
            data = f.read()
        self.assertTrue(data.startswith(h.PNG_SIG))
        self.assertEqual(self.srv.state.billed, before + 1)
        rid = max(self.srv.state.renders)
        self.assertEqual(data, self.srv.state.renders[rid].png)


if __name__ == "__main__":
    unittest.main()
