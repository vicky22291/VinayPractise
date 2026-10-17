# ridemap: interview task

ridemap draws bike rides on a map. A teammate started it: it can open a ride
file, and it has a small client for the MapDraw render API. Nothing calls the
API yet. You will finish the integration one part at a time.

- MapDraw's docs are in `docs/MAPDRAW_API.md`.
- A local fake of MapDraw is in `tools/`. Start it with
  `python3 tools/mapdraw_server.py` and leave it running.

Read the code, skim the docs and run the tests before you change anything.
The interviewer adds more parts as you finish each one. Nobody is expected to
finish every part.

## Part 1: read the ride

`data/ride-simple.json` is a recorded ride: a GeoJSON Feature with a
LineString geometry. A bare LineString geometry is also valid GeoJSON, so
accept that too.

1. `ridemap.track.load_track(path)` returns the ride as a list of
   `(lat, lon)` tuples of floats, in file order.
2. `python3 -m ridemap part1 [path]` prints the first ten points, one per
   line, as `lat, lon` with six decimals, for example
   `37.660000, -122.381264`. The path defaults to `data/ride-simple.json`.
3. A bad ride file must not produce a traceback. `load_track` raises
   `ridemap.errors.TrackError` with a clear message. The command prints
   `error: <message>` to stderr and exits with status 1. Bad means: the file is
   missing, it is not JSON, it is not a LineString, it has fewer than two
   points, or a point is not a valid position.

Write tests for what you build.
