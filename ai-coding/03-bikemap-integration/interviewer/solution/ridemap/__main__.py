"""Command line: python3 -m ridemap <command> [args]"""
import argparse
import logging
import sys

from ridemap import config
from ridemap.errors import RidemapError
from ridemap.landmarks import build_landmark_request, load_landmarks
from ridemap.mapdraw import MapDrawClient
from ridemap.render import build_basic_request, build_route_request
from ridemap.track import load_track


def _client():
    return MapDrawClient(config.mapdraw_url(), config.mapdraw_key())


def _save(png, path):
    with open(path, "wb") as f:
        f.write(png)
    print(f"saved {path} ({len(png)} bytes)")


def cmd_part1(args):
    for lat, lon in load_track(args.track)[:10]:
        print(f"{lat:.6f}, {lon:.6f}")


def cmd_part2(args):
    _save(_client().render(build_basic_request(load_track(args.track))), args.out)


def cmd_part3(args):
    _save(_client().render(build_route_request(load_track(args.track))), args.out)


def cmd_part5(args):
    body = build_landmark_request(load_track(args.track), load_landmarks(args.landmarks))
    _save(_client().render(body), args.out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ridemap")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, out, help_ in [
        ("part1", cmd_part1, None, "print the first ten points of the ride"),
        ("part2", cmd_part2, "bikemap2.png", "render the ride's area"),
        ("part3", cmd_part3, "bikemap3.png", "render the route"),
        ("part5", cmd_part5, "bikemap5.png", "render the route with nearby landmarks"),
    ]:
        p = sub.add_parser(name, help=help_)
        p.add_argument("track", nargs="?", default=config.DEFAULT_TRACK)
        if out:
            p.add_argument("--out", default=out)
        if name == "part5":
            p.add_argument("--landmarks", default="data/landmarks.json")
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        return args.fn(args) or 0
    except (RidemapError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
