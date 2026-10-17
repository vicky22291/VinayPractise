## Part 5: landmarks

`data/landmarks.json` (new in your repo) lists points of interest near the ride.

1. Add `ridemap/landmarks.py` with `nearest_points(track, landmarks)`, where
   `landmarks` is the parsed list from the file. For each landmark, in file
   order, return `(name, index, meters)`: the index of the nearest track point
   and the great-circle distance to it in meters. Use the haversine formula with
   an Earth radius of 6,371,000 m.
2. Add `build_landmark_request(track, landmarks, max_distance_m=250)` to the
   same module. Start from the Part 3 request. For every landmark within
   `max_distance_m` of its nearest track point, add an `orange` marker labelled
   with the landmark's name, and a `black` path from the landmark to that track
   point. MapDraw must accept the request.
3. `python3 -m ridemap part5 [path] [--landmarks data/landmarks.json]
   [--out bikemap5.png]` saves the image.
