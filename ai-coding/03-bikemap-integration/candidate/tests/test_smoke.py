import json
import os
import unittest
from unittest import mock

from ridemap import config
from ridemap.mapdraw import MapDrawClient


class ConfigTest(unittest.TestCase):
    def test_defaults_point_at_local_fake(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(config.mapdraw_url(), "http://127.0.0.1:8080")
            self.assertTrue(config.mapdraw_key().startswith("md_test_"))

    def test_env_overrides(self):
        with mock.patch.dict(os.environ, {"MAPDRAW_URL": "http://x:1", "MAPDRAW_API_KEY": "md_test_k"}):
            self.assertEqual(config.mapdraw_url(), "http://x:1")
            self.assertEqual(config.mapdraw_key(), "md_test_k")


class DataTest(unittest.TestCase):
    def test_ride_file_is_geojson(self):
        with open(config.DEFAULT_TRACK) as f:
            ride = json.load(f)
        self.assertEqual(ride["type"], "Feature")
        self.assertEqual(ride["geometry"]["type"], "LineString")


class ClientTest(unittest.TestCase):
    def test_base_url_trailing_slash(self):
        self.assertEqual(MapDrawClient("http://h:1/", "k").base_url, "http://h:1")


if __name__ == "__main__":
    unittest.main()
