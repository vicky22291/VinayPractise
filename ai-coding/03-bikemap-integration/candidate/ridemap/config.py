"""Settings, read from the environment so the same code runs locally and in prod."""
import os

DEFAULT_URL = "http://127.0.0.1:8080"
DEFAULT_KEY = "md_test_ridemap"
DEFAULT_TRACK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ride-simple.json")


def mapdraw_url():
    return os.environ.get("MAPDRAW_URL", DEFAULT_URL)


def mapdraw_key():
    return os.environ.get("MAPDRAW_API_KEY", DEFAULT_KEY)
