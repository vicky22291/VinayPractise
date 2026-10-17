"""Command line: python3 -m ridemap <command> [args]"""
import argparse

from ridemap import config
from ridemap.track import load_track


def cmd_part1(args):
    for point in load_track(args.track)[:10]:
        print(point)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ridemap")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("part1", help="print the first ten points of the ride")
    p.add_argument("track", nargs="?", default=config.DEFAULT_TRACK)
    p.set_defaults(fn=cmd_part1)
    args = ap.parse_args(argv)
    return args.fn(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
