"""Shared helpers for the hidden tests. Loads the kit's own copy of the fake
server, so a candidate who edited tools/mapdraw_server.py is still tested
against the real contract."""
import importlib.util
import json
import os
import subprocess
import sys

KIT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    "mapdraw_server_canonical", os.path.join(KIT, "candidate", "tools", "mapdraw_server.py"))
server_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server_mod)

KEY = "md_test_ridemap"
RUN = os.getcwd()  # kit.py runs hidden tests with the run dir as cwd
RIDE = os.path.join(RUN, "data", "ride-simple.json")
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def start():
    return server_mod.start_in_thread(port=0)


def raw_ride_points():
    with open(RIDE) as f:
        coords = json.load(f)["geometry"]["coordinates"]
    return [(c[1], c[0]) for c in coords]


def run_cli(*args, url=None, cwd=RUN):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if url:
        env["MAPDRAW_URL"] = url
        env["MAPDRAW_API_KEY"] = KEY
    return subprocess.run([sys.executable, "-m", "ridemap", *args], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=60)


def bbox_center(track):
    lats = [p[0] for p in track]
    lons = [p[1] for p in track]
    return (min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2
