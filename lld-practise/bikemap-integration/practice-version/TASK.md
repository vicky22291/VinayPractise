# BikeMap integration interview task

Finish a teammate's Java application that draws recorded bike rides using the MapDraw API, one part at a time.

The vendor contract is in `docs/MAPDRAW_API.md`. Start its local simulator with `python3 tools/mapdraw_server.py` when needed. Treat the simulator as the vendor; do not change its behavior to make your application pass.

Read the starter, skim the docs, and run `mvn test` before making changes. Add tests for your implementation. The interviewer reveals new requirements as you finish; you are not expected to complete every part in one timed session.

## Part 1 read the ride

`data/ride-simple.json` is a recorded ride: a GeoJSON Feature with a LineString geometry. Also accept a bare LineString geometry.

1. Implement `TrackLoader.load(Path path)` in `com.practice.stripe.ridemap`. Return `List<GeoPoint>` in file order, where `GeoPoint(double lat, double lon)` holds decimal-degree coordinates. Ignore extra position components such as elevation.
2. `Practice part1 [path]` must print the first ten points, one per line, as `lat, lon` with six decimals and a decimal point regardless of the machine's locale. Example: `37.660000, -122.381264`. Default to `data/ride-simple.json`.
3. For a missing file, invalid JSON, unsupported geometry, fewer than two points, or an invalid position, throw `TrackError` with a clear message. A valid position has at least two finite numeric coordinates in the geographic ranges. The command must print `error: <message>` to stderr, return exit status 1, and avoid a stack trace.

The Java entry point is `com.practice.stripe.Practice`. Keep `Practice.run(String[] args, PrintStream out, PrintStream err)` available for CLI tests, returning the intended exit status. `main` should use that status for the process exit code.

Run the current command:

```bash
mvn -q compile exec:java -Dexec.args="part1"
mvn -q compile exec:java -Dexec.args="part1 data/ride-simple.json"
```

The existing tests check setup only. Write tests for the ride and command behavior required above.
