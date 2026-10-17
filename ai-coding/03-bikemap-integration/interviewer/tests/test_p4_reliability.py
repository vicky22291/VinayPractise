import unittest

import mapdraw_harness as h
from ridemap.errors import MapDrawError
from ridemap.mapdraw import MapDrawClient
from ridemap.render import build_basic_request
from ridemap.track import load_track


class Part4(unittest.TestCase):
    def setUp(self):
        self.srv = h.start()
        self.sleeps = []
        self.client = MapDrawClient(self.srv.url, h.KEY, sleep=self.sleeps.append)
        self.body = build_basic_request(load_track(h.RIDE))

    def tearDown(self):
        self.srv.stop()

    def posts(self):
        return self.srv.state.render_posts()

    def test_happy_path_one_post_no_sleep(self):
        self.assertTrue(self.client.render(self.body).startswith(h.PNG_SIG))
        self.assertEqual(len(self.posts()), 1)
        self.assertEqual(self.sleeps, [])
        self.assertEqual(self.srv.state.billed, 1)

    def test_429_honours_retry_after(self):
        self.srv.state.inject({"status": 429, "retry_after": 2})
        self.assertTrue(self.client.render(self.body).startswith(h.PNG_SIG))
        self.assertEqual(len(self.posts()), 2)
        self.assertEqual(len(self.sleeps), 1)
        self.assertGreaterEqual(self.sleeps[0], 2)
        self.assertEqual(self.srv.state.billed, 1)

    def test_503_backoff_then_success(self):
        self.srv.state.inject({"status": 503}, {"status": 502})
        self.assertTrue(self.client.render(self.body).startswith(h.PNG_SIG))
        self.assertEqual(len(self.posts()), 3)
        self.assertEqual(len(self.sleeps), 2)
        self.assertGreaterEqual(self.sleeps[0], 0.5)
        self.assertGreaterEqual(self.sleeps[1], 1.0)

    def test_gives_up_after_five_attempts(self):
        self.srv.state.inject(*[{"status": 503}] * 6)
        with self.assertRaises(MapDrawError) as ctx:
            self.client.render(self.body)
        self.assertEqual(ctx.exception.status, 503)
        self.assertEqual(len(self.posts()), 5)
        self.assertEqual(len(self.sleeps), 4)
        for i, s in enumerate(self.sleeps):
            self.assertGreaterEqual(s, 0.5 * 2 ** i - 1e-9)

    def test_400_is_not_retried(self):
        with self.assertRaises(MapDrawError) as ctx:
            self.client.render(dict(self.body, zoom=0))
        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(len(self.posts()), 1)
        self.assertEqual(self.sleeps, [])

    def test_401_is_not_retried(self):
        client = MapDrawClient(self.srv.url, "md_test_wrong", sleep=self.sleeps.append)
        with self.assertRaises(MapDrawError):
            client.render(self.body)
        self.assertEqual(len(self.posts()), 1)

    def test_lost_response_is_billed_once(self):
        self.srv.state.inject({"drop": "after_accept"})
        png = self.client.render(self.body)
        self.assertTrue(png.startswith(h.PNG_SIG))
        self.assertEqual(self.srv.state.billed, 1)
        keys = [p["headers"].get("idempotency-key") for p in self.posts()]
        self.assertEqual(len(keys), 2)
        self.assertTrue(keys[0])
        self.assertEqual(keys[0], keys[1])
        self.assertEqual(png, next(iter(self.srv.state.renders.values())).png)

    def test_dropped_before_accept_is_retried(self):
        self.srv.state.inject({"drop": "before_accept"})
        self.assertTrue(self.client.render(self.body).startswith(h.PNG_SIG))
        self.assertEqual(self.srv.state.billed, 1)

    def test_mixed_faults(self):
        self.srv.state.inject({"status": 429, "retry_after": 1}, {"drop": "after_accept"}, {"status": 500})
        self.assertTrue(self.client.render(self.body).startswith(h.PNG_SIG))
        self.assertEqual(self.srv.state.billed, 1)
        self.assertEqual(len(self.posts()), 4)

    def test_separate_calls_are_separate_renders(self):
        self.client.render(self.body)
        self.client.render(dict(self.body, zoom=13))
        self.assertEqual(self.srv.state.billed, 2)


if __name__ == "__main__":
    unittest.main()
