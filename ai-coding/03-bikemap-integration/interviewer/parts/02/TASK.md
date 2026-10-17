## Part 2: render a basic map

Call MapDraw to render the area of the ride and save the image.

1. Add `ridemap/render.py` with `build_basic_request(track)`. It returns the
   JSON body for `POST /v1/render`: an 800 x 600 image at zoom 14, centred on
   the middle of the ride's bounding box. The middle is the midpoint of the
   lowest and highest latitude, and of the lowest and highest longitude. No
   markers or paths yet.
2. `MapDrawClient.render(body)` sends the request and returns the image as
   `bytes`. On an error response it raises `MapDrawError` with `.status` set to
   the HTTP status and the API's error message in the text.
3. `python3 -m ridemap part2 [path] [--out bikemap2.png]` renders the map and
   saves it. The API location and key come from the `MAPDRAW_URL` and
   `MAPDRAW_API_KEY` environment variables, through `ridemap/config.py`.

Open the PNG and look at it.
