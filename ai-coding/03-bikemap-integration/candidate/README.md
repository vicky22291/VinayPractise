# ridemap

Draws recorded bike rides on a map, using the MapDraw render API.

```
ridemap/track.py      load_track(path): read a GeoJSON ride
ridemap/mapdraw.py    MapDrawClient: thin HTTP client for MapDraw
ridemap/config.py     MAPDRAW_URL and MAPDRAW_API_KEY from the environment
ridemap/errors.py     TrackError, MapDrawError
ridemap/__main__.py   python3 -m ridemap <command>
data/                 sample rides
docs/MAPDRAW_API.md   MapDraw API reference
tools/mapdraw_server.py   local fake of MapDraw (python3 tools/mapdraw_server.py)
tests/                python3 -m unittest
```

Python 3.11+, standard library only.

## Local setup

```
$ python3 tools/mapdraw_server.py            # terminal 1: fake API on :8080
$ python3 -m ridemap part1                   # terminal 2
```

`MAPDRAW_URL` defaults to `http://127.0.0.1:8080` and `MAPDRAW_API_KEY` to
the test key `md_test_ridemap`.
