# Google Maps Street View ingestion and storage

> One-line answer: a car-day (~1.4 TB) is encrypted on the rig and written twice (swappable cartridge plus an onboard mirror that keeps every drive until it is LANDED), uploaded from a depot ingest station into an encrypted landing bucket, and declared LANDED only when a strongly consistent drive registry has matched every segment against the rig-signed manifest, which is the only moment the cartridge may be wiped; a durable per-drive workflow poses, stitches, blurs, selects one panorama per ~10 m road slot and tiles it into immutable versioned tiles; a publisher moves each slot's "current" pointer in 1 km chunks after the tiles exist; a cached metadata API keyed by S2 cell and a CDN serve reads; unblurred raw is crypto-shredded at 180 days, current imagery is tiered by access and history goes to Archive; a blur request is a footprint on the ground that re-blurs every past panorama, and for a house every future drive. At 1,000 cars that is ~1.4 PB of raw a day, 15 M panoramas a day, and storage costing ~15 to 20x compute. The red node is the depot ingest station.

Tier 3, problem #27 in [`hld/README.md`](../README.md). Reported as a Google L6/L7 question. Reusable blocks: [`../../concepts/signed-url.md`](../../concepts/signed-url.md) (scoped upload credentials, start / bytes / complete), [`../../concepts/geospatial-index.md`](../../concepts/geospatial-index.md) (S2, cells, coverings), [`../../concepts/erasure-coding.md`](../../concepts/erasure-coding.md) (what the object store does underneath), [`../../concepts/temporal-durable-execution.md`](../../concepts/temporal-durable-execution.md) (one workflow per drive), [`../../concepts/leases-fencing-clocks.md`](../../concepts/leases-fencing-clocks.md) (fencing a zombie stage), [`../../concepts/caching-patterns.md`](../../concepts/caching-patterns.md), [`../immutable-object-store/`](../immutable-object-store/) (commit point, erasure-coded placement), [`../multi-region-metadata-store/`](../multi-region-metadata-store/) (the registry and index underneath).

## Problem statement (as given)

Two published phrasings, both verified on 2026-09-27:

- "Design Google Street View using 1000 cars to map every address and image worldwide." ([TryExponent](https://www.tryexponent.com/questions/2109/design-google-street-view-1000-cars))
- "Design a system for collecting Street View images from taxi-mounted cameras that can handle high-volume uploads, deduplication, and prepare images for privacy/quality processing." Asked at Google. ([Hello Interview](https://www.hellointerview.com/community/questions/image-uploader-dedup/cm4t1rgrn005988ilm7ct8ma1))

The index row calls it "ingestion and storage": huge objects, spatial indexing, lifecycle, batch pipelines. No candidate debrief with follow-ups is published, so the probe list below is built from the primary sources and marked as such.

## What the web research changed

Sources checked on 2026-09-27. Notes and spot-check corrections in [`research/`](research/).

| Change | Requirement | Evidence |
|---|---|---|
| ADD | Design point is **1,000 cars**. At ~150 km a day that is ~37.5 M km a year, which re-drives ~40 M km of covered roads (about half the world's ~80 M km) about once a year | TryExponent prompt. World roads "roughly 50 million miles" in [Anguelov et al. 2010](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/36899.pdf) |
| ADD | **Offload is physical.** Car-days travel on drives, not over the air | The 2010 paper: rigs logged to hard drives, "shock-mounted disk enclosures" and "custom-shipping packaging". §2 math: 150 h per car-day on LTE |
| ADD | **Dedup**, and for the taxi variant dedup **before upload** | Hello Interview prompt names deduplication; taxis re-drive the same streets |
| ADD | **Unblurred raw has a retention cap** (180 days) and must be provably destroyed | EU Article 29 Working Party asked Google on 2010-02-11 to cut unblurred retention from 1 year to 6 months ([EDRi](https://edri.org/our-work/edrigramnumber8-5article-29-wp-google-street-view/)) |
| ADD | **Blur requests at scale and before launch**, applied to all dates and future drives | Germany 2010: 244,237 of 8,458,084 households (2.89%) opted out before launch ([Google Europe Blog](https://europe.googleblog.com/2010/10/how-many-german-households-have-opted.html)) |
| ADD | **Contributor uploads** use the same pipeline | [Street View Publish API](https://developers.google.com/streetview/publish/first-app): start upload, bytes to URL, create with pose. Photo Spheres 2:1, >= 7.5 MP, <= 75 MB ([requirements](https://support.google.com/maps/answer/7012050?hl=en)) |
| UPDATE | "Blur faces and plates" becomes: **recall-first detector plus user reports**, because automatic recall is not 100% | [Frome et al., ICCV 2009](https://static.googleusercontent.com/media/research.google.com/en//archive/papers/cbprivacy_iccv09.pdf): 89.0% hand-counted face recall, 94 to 96% plates, users report the rest |
| UPDATE | "Store the images" becomes: **small index in a database, bytes in the object store, locality-named keys** | Bigtable paper §8.2: Earth used a ~70 TB raw table with rows named so adjacent segments sit together, and a ~500 GB serving index over GFS ([OSDI 2006](https://static.googleusercontent.com/media/research.google.com/en//archive/bigtable-osdi06.pdf)) |
| UPDATE | "Hot and cold storage" becomes **tier by access, and history is still served online** | GCS Archive returns data "within milliseconds, not hours or days" ([storage classes](https://cloud.google.com/storage/docs/storage-classes)). The 2010 paper: panoramas replicated "according to usage patterns" |
| KEEP | Pipeline order: pose, stitch, tile, blur, publish | Anguelov et al. 2010, "launch pipeline" |
| DELETE | Nothing. **Rejected as requirements:** streaming imagery from cars in real time, per-image perceptual dedup across the archive | No need for minutes-fresh imagery; slot-level dedup does the job |

## Final requirements

Functional:
1. Ingest a car-day (~1.4 TB, ~1,400 segments of 1 GB) durably and verifiably, from depots or by courier. Contributor photos enter the same way.
2. Process a landed drive into blurred panoramas: pose, pick one capture per ~10 m slot, stitch, blur, QA, tile.
3. Index panoramas by location, road slot and time. Exactly one current panorama per slot; older ones are history. Publishing never exposes missing tiles or dead arrows.
4. Serve "panorama at this point (and date)" plus tiles at the viewer's zoom.
5. Apply an approved blur request to every published copy, current and historical, within 24 h, permanently. For a house or other fixed object, also to every future drive.

Non-functional: no car-day lost after capture (two copies until LANDED). Capture to LANDED p99 48 h, LANDED to published p95 7 days. Metadata p99 < 100 ms, tile p99 < 150 ms at the edge, ~1 M tile requests/s peak. Serving 99.99%. Unblurred raw gone by 180 days. Storage per published km flat or falling.

## What interviewers probe

Built from the prompts and the primary sources (no published debrief lists follow-ups):
1. 1,000 cars. How many TB a day, and how do they reach the datacenter? Do the cellular math.
2. When is it safe to delete the data on the car? What is the commit point?
3. The depot has no internet for three days. What happens to the fleet?
4. Cameras are on taxis that drive the same streets all day. How do you dedup, and where?
5. How do you find the panorama at a point, and show the one from 2015?
6. Two drives of the same street. Which is current, and how do you switch without broken arrows?
7. Storage for 15 years: what do you keep, in which class, and what do you delete?
8. The face detector improves. What do you reprocess, and from what?
9. Someone asks to blur their house. What changes, where, and how fast?
10. Tiles sit in every CDN edge cache. How does a blur ever take effect, and why is the edge lifetime 30 days rather than a year?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one diagram built one requirement at a time, deep dives that change the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/vehicle-offload-and-landing.md`](deep-dives/vehicle-offload-and-landing.md) | The red node: cartridges, onboard mirror, depot station, resumable create-only uploads, the LANDED commit point, network vs courier, the taxi variant |
| [`deep-dives/processing-pipeline-and-reprocessing.md`](deep-dives/processing-pipeline-and-reprocessing.md) | Per-drive durable workflow, shards, manifests, leases and epochs, dead-letter drives, fresh vs backfill lanes |
| [`deep-dives/spatial-index-and-publish.md`](deep-dives/spatial-index-and-publish.md) | S2 keys, coverings, nearest and by-date lookup, slots and the current pointer, chunked publish, runnable Python |
| [`deep-dives/storage-tiers-and-lifecycle.md`](deep-dives/storage-tiers-and-lifecycle.md) | What each byte is for, class per tier, Archive vs Coldline break-even, crypto-shredding, access-based tiering, runnable cost model |
| [`deep-dives/privacy-blur-and-takedowns.md`](deep-dives/privacy-blur-and-takedowns.md) | Recall-first detection, footprints not boxes, the blur registry, takedown checklist, retention caps |
| [`deep-dives/tile-serving-and-cdn.md`](deep-dives/tile-serving-and-cdn.md) | Tile pyramid, immutable versioned URLs, CDN hit rate, invalidation budget, serving history from Archive |
| [`research/`](research/) | Three web surveys (real-world systems, mechanisms, interview framing), each with a spot-check corrections table |
| `streetview-ingestion.excalidraw` | My drawing. Missing until I draw it |
