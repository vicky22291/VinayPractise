# MapDraw Render API (v1)

MapDraw turns a JSON description of a map into a PNG image. You describe the
frame (centre, zoom, size) and what to draw on it (markers and paths). MapDraw
draws it on a plain base map and returns the image.

This is the reference for API version `v1`. Last updated 2026-03-02.

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Requests and responses](#requests-and-responses)
- [Errors](#errors)
- [Rate limits](#rate-limits)
- [Idempotent requests](#idempotent-requests)
- [Billing](#billing)
- [Create a render](#create-a-render-post-v1render)
- [Retrieve a render](#retrieve-a-render)
- [Objects](#objects)
- [Limits](#limits)
- [Changelog](#changelog)

---

## Base URL

```
https://api.mapdraw.example
```

Every path in this document starts with `/v1`. For local development we ship a
fake of the API in `tools/mapdraw_server.py`. It listens on
`http://127.0.0.1:8080` and accepts the test key `md_test_ridemap`.

---

## Authentication

Authenticate every request with your secret key in the `Authorization` header,
using the Bearer scheme:

```
Authorization: Bearer md_test_ridemap
```

Keys that start with `md_test_` render on the test base map and are not billed
in production. Keys that start with `md_live_` are billed. Never put a key in a
query string or commit it to source control.

A missing or malformed header returns `401` with
`"type": "authentication_error"`.

---

## Requests and responses

- Request bodies are JSON. Send `Content-Type: application/json`. Form-encoded
  bodies are rejected with `400`.
- Request bodies are limited to 256 KiB. Larger bodies return `413`.
- A successful render returns the **image itself**, not JSON:
  `Content-Type: image/png`, and the body is the PNG bytes. Write it to disk as
  binary.
- Every response carries a `Request-Id` header. Include it when you contact
  support.
- Successful renders also carry:
  - `X-Render-Id`: the id of the render, for example `rnd_00042`.
  - `X-Billed-Credits`: `1` for a new render, `0` for an idempotent replay.
  - `Idempotent-Replayed: true` when the response is a replay (see below).

---

## Errors

Errors return a JSON body with an `error` object and an HTTP status.

```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "zoom must be an integer from 1 to 18",
    "param": "zoom"
  }
}
```

| Status | `type` | Meaning | Retry? |
|---|---|---|---|
| `400` | `invalid_request_error` | The request is malformed or breaks a limit. `param` names the field when there is one | No. Fix the request |
| `401` | `authentication_error` | No key, wrong scheme, or unknown key | No |
| `404` | `invalid_request_error` | Unknown path or render id | No |
| `409` | `idempotency_error` | An `Idempotency-Key` was reused with different parameters | No |
| `413` | `invalid_request_error` | Body over 256 KiB | No. Send fewer or simpler paths |
| `429` | `rate_limit_error` | Too many requests. See `Retry-After` | Yes, after `Retry-After` seconds |
| `500`, `502`, `503`, `504` | `api_error` | Something went wrong on our side | Yes, with exponential backoff |

Network errors (a reset connection, a timeout) are ambiguous: the render may or
may not have been created. See [Idempotent requests](#idempotent-requests).

---

## Rate limits

Each key may create up to 25 renders per second, with short bursts allowed.
Above that, MapDraw returns `429` with a `Retry-After` header giving the number
of seconds to wait. Clients that ignore `Retry-After` and retry immediately may
be throttled for longer.

---

## Idempotent requests

`POST /v1/render` supports idempotency, so you can retry a request safely
without rendering, and paying for, the same map twice.

Send an `Idempotency-Key` header with a unique value of 1 to 255 characters.
We recommend a V4 UUID, generated once per logical render and reused on every
retry of that render.

```
Idempotency-Key: 4f9d8c2e-0b7a-4d59-9a3e-6c1f2b8e7d10
```

- The first request with a key renders the map and stores the result.
- A later request with the same key and the **same parameters** returns the
  stored image with `Idempotent-Replayed: true` and `X-Billed-Credits: 0`.
- A later request with the same key and **different parameters** returns `409`.
- Keys are scoped to your API key and kept for 24 hours.
- Requests that fail validation (`400`) or are rate limited (`429`) do not
  store anything, so retrying them with the same key is safe.

If you lost the response to a render (for example the connection reset after
you sent it), either retry with the same key, or look the render up with
[`GET /v1/renders?idempotency_key=...`](#find-a-render-by-idempotency-key).

---

## Billing

Each new render costs one credit. Idempotent replays and failed requests are
free. Credits are deducted when the render is created, before the response is
sent.

---

## Create a render: `POST /v1/render`

Renders a map and returns it as a PNG.

### Body parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `size` | object | yes | `{"width": int, "height": int}` in pixels, each 64 to 1280 |
| `center` | [LatLon](#latlon) | yes | Centre of the frame |
| `zoom` | int | yes | 1 (whole world) to 18 (street level). Zoom 14 shows about 6 km across at 800 px wide in mid latitudes |
| `markers` | array of [Marker](#marker) | no | Pins drawn on top of paths |
| `paths` | array of [Path](#path) | no | Polylines |
| `format` | string | no | Only `png` is supported |

Unknown parameters are rejected with `400`. This catches typos such as `centre`.

### Example: two cafes and the walk between them

```bash
curl https://api.mapdraw.example/v1/render \
  -H "Authorization: Bearer md_test_ridemap" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
        "size": {"width": 640, "height": 480},
        "center": {"lat": 37.7694, "lon": -122.4862},
        "zoom": 15,
        "markers": [
          {"lat": 37.7701, "lon": -122.4890, "label": "Cafe A", "color": "#2563eb"},
          {"lat": 37.7688, "lon": -122.4831, "label": "Cafe B"}
        ],
        "paths": [
          {"color": "red", "width": 5,
           "points": [{"lat": 37.7701, "lon": -122.4890}, {"lat": 37.7695, "lon": -122.4860},
                      {"lat": 37.7688, "lon": -122.4831}]}
        ]
      }' \
  --output walk.png
```

### Example: Python

There is no official Python SDK. Any HTTP client works. With the standard
library:

```python
import json, urllib.request

req = urllib.request.Request(
    "https://api.mapdraw.example/v1/render",
    data=json.dumps(body).encode(),
    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    image = resp.read()
```

Note that `urlopen` raises `urllib.error.HTTPError` for 4xx and 5xx responses.
The error JSON is in the exception's body.

---

## Retrieve a render

### `GET /v1/renders/{id}`

Returns the render's metadata as JSON.

```json
{
  "id": "rnd_00042",
  "object": "render",
  "created": 1774000000,
  "idempotency_key": "4f9d8c2e-0b7a-4d59-9a3e-6c1f2b8e7d10",
  "bytes": 18734,
  "image_url": "/v1/renders/rnd_00042/image"
}
```

### `GET /v1/renders/{id}/image`

Returns the PNG for a render you already created. Not billed.

### Find a render by idempotency key

`GET /v1/renders?idempotency_key=<key>` returns a list with zero or one render.

```json
{"object": "list", "data": [{"id": "rnd_00042", "object": "render", "...": "..."}]}
```

---

## Objects

### LatLon

```json
{"lat": 37.7749, "lon": -122.4194}
```

`lat` from -90 to 90, `lon` from -180 to 180, both decimal degrees (WGS 84).

### Marker

| Field | Type | Required | Notes |
|---|---|---|---|
| `lat`, `lon` | number | yes | Position |
| `label` | string | no | 1 to 16 characters. Shown next to the pin |
| `color` | string | no | Named color or `#rrggbb`. Default `red` |

### Path

| Field | Type | Required | Notes |
|---|---|---|---|
| `points` | array of LatLon | yes | 2 to 500 points, drawn in order |
| `color` | string | no | Named color or `#rrggbb`. Default `blue` |
| `width` | int | no | Line width in pixels, 1 to 8. Default 3 |

Named colors: `black`, `white`, `red`, `orange`, `yellow`, `green`, `blue`,
`purple`, `brown`, `gray`.

---

## Limits

| Limit | Value |
|---|---|
| Image size | 64 to 1280 px per side |
| Zoom | 1 to 18 |
| Markers per request | 10 |
| Marker label | 16 characters |
| Paths per request | 100 |
| Points per path | 500 |
| Points per request, all paths | 5,000 |
| Request body | 256 KiB |
| Renders per second per key | 25 |

---

## Changelog

- **2026-03-02.** Added `GET /v1/renders?idempotency_key=`.
- **2025-11-10. Breaking.** Points are now `{"lat": ..., "lon": ...}` objects.
  The old `[lon, lat]` array form, copied from GeoJSON, caused too many swapped
  maps and is rejected with `400`.
- **2025-06-01.** `X-Billed-Credits` header added.
- **2024-09-15.** `v1` released.
