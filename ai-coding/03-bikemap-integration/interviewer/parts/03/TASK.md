## Part 3: draw the route

1. Add `build_route_request(track)` to `ridemap/render.py`. It has the same
   size, zoom and centre as Part 2, plus:
   - **Paths.** The first ten segments of the ride in `blue`, the next ten in
     `brown`, and so on, alternating to the end of the ride. A segment joins
     two consecutive points.
   - A `green` marker labelled `Start` at the first point of the ride.
   - A `purple` marker labelled `Stripe` at the Stripe office:
     lat `37.6627`, lon `-122.3891`.
2. `python3 -m ridemap part3 [path] [--out bikemap3.png]` saves the image.
