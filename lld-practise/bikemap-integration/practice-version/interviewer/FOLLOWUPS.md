# Interviewer only staged prompts

Keep this file closed during a first attempt. Reveal only the next stage when the candidate is ready. Append that stage's prompt to TASK.md; do not reveal the remainder of this file. All new Java classes below belong to `com.practice.stripe.ridemap` unless stated otherwise. These are requirements, not solutions.

## Part 2 render a basic map

Call MapDraw to render the area of the ride and save the image.

1. Add `RenderRequests` with `JsonNode buildBasicRequest(List<GeoPoint> track)`. Return the JSON body for `POST /v1/render`: an 800 by 600 image at zoom 14, centered on the midpoint of the ride's bounding box. Use the midpoint of minimum and maximum latitude, and of minimum and maximum longitude. No markers or paths yet.
2. Change `MapDrawClient.render(JsonNode body)` to return the image as `byte[]`. On an error response, throw `MapDrawError` with `status()` equal to the HTTP status and the vendor's error message included in the exception text. Constructors may accept an ObjectMapper or other dependencies if useful.
3. Add `Practice part2 [path] [--out bikemap2.png]`. Use `Config` for the `MAPDRAW_URL` and `MAPDRAW_API_KEY` environment variables and save the image. Convert failures into clear stderr messages and a nonzero exit status rather than stack traces.

Open the PNG and look at it. Write tests for what you build.

## Part 3 draw the route

1. Add `JsonNode buildRouteRequest(List<GeoPoint> track)` to `RenderRequests`. Use the same size, zoom, and center as Part 2, plus:
   - Paths: the first ten segments in blue, the next ten in brown, alternating to the end. A segment joins two consecutive points.
   - A green marker labeled `Start` at the first point.
   - A purple marker labeled `Stripe` at latitude `37.6627`, longitude `-122.3891`.
2. Add `Practice part3 [path] [--out bikemap3.png]` to save the image.

Write tests for the request and its boundaries.

## Part 4 survive production

MapDraw sometimes returns 429 or 5xx and sometimes loses the connection after accepting a render. Each render costs one credit.

1. Support a constructor `MapDrawClient(String baseUrl, String apiKey, Duration timeout, Sleeper sleeper)`, retaining the existing convenient constructors. Define `Sleeper` as a functional interface with `void sleep(Duration duration) throws InterruptedException`. Route every application-controlled wait through this dependency so tests can record waits without sleeping.
2. On 429, wait the number of seconds from `Retry-After`, then retry.
3. On 500, 502, 503, 504, a dropped connection, or a timeout, retry with exponential waits of 0.5, 1, 2, and 4 seconds.
4. Make at most five attempts per `render` call. After exhaustion, throw `MapDrawError`; retain the last HTTP status when available, or use status 0 for a transport failure.
5. Never retry other statuses, such as 400, 401, or 409. Interruption should stop the operation rather than trigger another attempt.
6. A single `render` call must never cost more than one credit, even if the first response was lost.

For a manual run, restart the vendor with `python3 tools/mapdraw_server.py --fault-rate 0.4`. It prints billed renders when stopped. Before coding, explain what you would log.

Use deterministic failures and an injected sleeper in automated tests. The supplied Python simulator exposes `State.inject(...)` for a local harness if useful; it does not require you to alter vendor behavior.

## Part 5 landmarks

Interviewer setup: copy `interviewer/files/part5/data/landmarks.json` to `data/landmarks.json` only when revealing this stage.

1. Add `Landmarks` with `List<NearestPoint> nearestPoints(List<GeoPoint> track, JsonNode landmarks)`. The landmarks argument is the parsed array from the new file. Return one `NearestPoint(String name, int index, double meters)` per landmark in file order. The index is its nearest track point; distance is great-circle distance in meters using the haversine formula and Earth radius 6,371,000 meters. Choose the earliest index on a tie.
2. Add `JsonNode buildLandmarkRequest(List<GeoPoint> track, JsonNode landmarks, double maxDistanceMeters)` and a convenience overload defaulting to 250 meters. Start from Part 3's request. For each landmark within the distance threshold of its nearest track point, add an orange marker labeled with its name and a black path from the landmark to that point. The resulting request must satisfy MapDraw's documented limits.
3. Add `Practice part5 [path] [--landmarks data/landmarks.json] [--out bikemap5.png]` to save the image.

Write tests and open the result.
