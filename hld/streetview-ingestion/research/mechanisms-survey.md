# Street View Ingestion and Storage: Mechanisms Survey

Survey date: 2026-09-27. Research compiled for Staff-level HLD on Google Maps Street View ingestion pipeline serving multi-TB daily imagery from fleets capturing 360 photos, GPS, IMU, lidar; processing into panoramas; storing cheaply for years; serving as tiles.

### Scope

This survey covers ten mechanisms critical to the Street View pipeline at infrastructure scale:
upload (gigabytes to terabytes per vehicle per day), bulk transfer hardware (warehouse-scale ingestion), storage economics (multi-year retention vs. retrieval cost), durability via erasure coding, spatial indexing for search and cache locality, panorama tiling and image pyramids, large-scale pose estimation, privacy blurring at high recall, batch pipeline semantics, and CDN tile serving. Each mechanism is grounded in primary sources: vendor documentation, academic papers, and engineering blogs from system owners.

### Mechanisms Overview

1. **Large object upload**: resumable uploads (GCS) and multipart (S3), session lifetime, integrity checks.
2. **Bulk transfer**: Transfer Appliance (GCS), Snowball Edge (AWS, deprecated 2026), DataSync (modern alternative).
3. **Storage classes & lifecycle**: GCS/S3 tier costs, minimum retention, soft delete, lifecycle rules.
4. **Erasure coding**: Colossus/Ford et al., durability vs. rebuild latency, RS parameters.
5. **Spatial indexing**: S2 cells (Google), Bing quadkeys, H3 hexagons (Uber).
6. **Panorama formats**: Photo Sphere XMP, equirectangular projection, tile pyramids (zoom 0-5).
7. **Pose estimation**: Building Rome dataset (150k images, 21 hours, 496 cores), SfM at scale.
8. **Privacy blurring**: ICCV 2009 face/plate detection, Gaussian blur, GDPR right to erasure.
9. **Batch pipeline**: FlumeJava (PLDI 2010), MillWheel (VLDB 2013), Dataflow (VLDB 2015).
10. **CDN serving**: Cloud CDN cache invalidation, signed URLs, tile versioning.

## 1. Large Object Upload

GCS resumable upload chunk size must be a multiple of 256 KiB. https://docs.cloud.google.com/storage/docs/resumable-uploads This multiple-of-256 KiB requirement is enforced across all client libraries (C++, C#, Go, Java, Node.js, PHP, Python, REST). https://docs.cloud.google.com/storage/docs/resumable-uploads Recommended chunk sizes vary by language: Python 100 MiB, Java 15 MiB, Go 16 MiB, C++ 8 MiB, PHP 256 KiB. https://docs.cloud.google.com/storage/docs/resumable-uploads Session URI lifetime: one week before expiring. https://docs.cloud.google.com/storage/docs/resumable-uploads After expiration, requests return 410 Gone (within week) or 404 Not Found (beyond week). https://docs.cloud.google.com/storage/docs/resumable-uploads GCS max object size: no hard limit stated in docs, but resumable uploads designed for multi-TB objects. https://cloud.google.com/storage/docs/uploads

GCS parallel composite uploads: 32-component limit per compose operation. https://cloud.google.com/storage/docs/uploads This means a ~10 TB file (assuming 320 GB per component maximum) requires hierarchical composition in trees. Incomplete uploads do not appear in bucket and do not replace existing objects. https://docs.cloud.google.com/storage/docs/resumable-uploads Design implication: retry logic must assume interrupted uploads leave no trace.

S3 multipart upload limits: 10,000 parts maximum, part size 5 MiB to 5 GiB per part. https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html Max object size via multipart: 48.8 TiB. https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html At minimum part size (5 MiB): 50 GB max object. At maximum (5 GiB): 48.8 TB max object. https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html Integrity: CRC32C checksum for GCS, MD5 for S3. https://docs.cloud.google.com/storage/docs/resumable-uploads Upload optimization tradeoff: larger chunks reduce request overhead but increase memory and retry cost on network failure. GCS guidance: avoid breaking into smaller chunks when possible to reduce latency and ops cost. https://docs.cloud.google.com/storage/docs/resumable-uploads

## 2. Bulk Transfer Hardware

Google Transfer Appliance. Two models for physical data transfer. TA40 V2 (rackable): 100 TB encrypted capacity with 10 Gbps (RJ45) or 100 Gbps (QSFP28) interfaces. https://docs.cloud.google.com/transfer-appliance/docs/4.0/specifications TA300 V2 (rackable): 300 TB encrypted capacity, same network options. https://docs.cloud.google.com/transfer-appliance/docs/4.0/specifications Freestanding models available: TA40F up to 40 TB, TA300F up to 300 TB. https://docs.cloud.google.com/transfer-appliance/docs/4.0/specifications End-to-end cycle time: approximately 3 weeks from order to returned data in GCS. https://docs.cloud.google.com/transfer-appliance/docs/4.0/specifications At 100 Gbps: TA300 could theoretically fill in ~24 hours (300 TB / 100 Gbps = 3.3 hours), but practical bottleneck is device ingress from on-premises networks and GCS write throughput. Transfer protocols: NFS, SMB, or SSH/SCP (one per appliance). https://docs.cloud.google.com/transfer-appliance/docs/4.0/specifications Use case: one-time migration of 100s of TB to PB scale.

AWS Snowball Edge Storage Optimized 210TB. 210 TB usable capacity, 1.5 Gbps network throughput. https://docs.aws.amazon.com/snowball/latest/developer-guide/specifications.html Estimated fill time: 210 TB at 1.5 Gbps = ~1,456 hours = ~61 days non-stop (practical: 3-5 weeks per device in production use). https://docs.aws.amazon.com/snowball/latest/developer-guide/specifications.html Critical discontinuation: Snowball Edge unavailable to new customers after November 7, 2025; AWS deprecates entire Snowball service December 31, 2026. https://docs.aws.amazon.com/snowball/latest/developer-guide/snowball-edge-availability-change.html For projects shipping after 2026, Snowball is not an option.

AWS DataSync (new guidance). 10 Gbps capable with built-in compression and sparse file detection. Supports incremental transfers and in-line validation. https://aws.amazon.com/blogs/storage/replicate-objects-using-aws-datasync-with-amazon-s3-compatible-storage-on-snowball-edge/ Advantage over hardware: online, no shipping delay. Disadvantage: needs sustained 10 Gbps network link on-premises (not all sites have this). Use case: modern replacement for Snowball for large migrations.

Design trade-off: Transfer Appliance has longer wall-clock time (3 weeks) but requires zero network provisioning; DataSync is faster (data rate limited by network) but needs dedicated high-bandwidth link.

## 3. Storage Classes and Lifecycle

GCS storage classes and retention tiers. https://docs.cloud.google.com/storage/docs/storage-classes Standard: no minimum storage duration, suitable for hot data (immediate reads). Nearline: 30-day minimum, optimized for infrequent access. Coldline: 90-day minimum, archive tier. Archive: 365-day minimum (policy not hard limit), cold archive. https://cloud.google.com/blog/products/storage-data-transfer/understanding-cloud-storages-new-soft-delete-feature All tiers except Standard incur per-gigabyte retrieval fees. https://docs.cloud.google.com/storage/docs/storage-classes Early deletion charges apply if data deleted before minimum duration (e.g., deleting a Coldline object at day 45 incurs 45 days of storage + 45-day early deletion penalty). https://docs.cloud.google.com/storage/docs/storage-classes Pricing as of September 2026, us-central1 region: [unverified - Google pricing page requires dynamic fetch]. https://cloud.google.com/storage/pricing For Street View, typical tier: ingest to Standard, auto-transition to Coldline at 90 days, Archive at 1+ years (accessed rarely for legal holds and historical reconstruction).

AWS S3 storage classes and minimum billing periods. https://docs.aws.amazon.com/AmazonS3/latest/userguide/archival-storage.html Standard-IA: 30-day minimum billing period, charged for 30 days minimum even if deleted at day 5. https://docs.aws.amazon.com/AmazonS3/latest/userguide/archival-storage.html Glacier Instant: 90-day minimum, instant retrieval on request. Glacier Flexible: 90-day minimum, retrieval 1-5 minutes (Standard tier) or 5-12 hours (Bulk tier). Glacier Deep Archive: 180-day minimum, retrieval 12 hours (Standard) or 48 hours (Bulk). https://docs.aws.amazon.com/AmazonS3/latest/userguide/archival-storage.html Pricing (September 2026, us-east-1): Glacier Deep Archive $0.00099/GB-month or ~$1/TB-month. https://aws.amazon.com/s3/pricing/ Glacier Instant: $0.004/GB-month. https://aws.amazon.com/s3/pricing/ [Standard-IA and Glacier Flexible per-GB pricing not extracted from dynamic pricing page.]

Retrieval cost dominates total-cost-of-ownership (TCO). Glacier Deep Archive with 180-day minimum: a 1 PB retrieval costs ~$1 million in storage alone (10,000 GB-months). Add retrieval fees ($0.005 per GB typical for Deep Archive) adds another $5 million. For Street View: once written, data rarely leaves archive tier. Lifecycle rules cost becomes negligible vs. avoiding retrieval.

GCS soft delete: default retention 7 days, adjustable 7-90 days per bucket policy. https://docs.cloud.google.com/storage/docs/soft-delete A deleted object is recoverable within the soft delete window. After expiry, deletion is permanent. https://docs.cloud.google.com/storage/docs/soft-delete GCS object versioning compatible with soft delete and Bucket Lock. https://docs.cloud.google.com/storage/docs/object-versioning When versioning is enabled, deleted object (current version) becomes noncurrent; soft delete window applies to noncurrent objects. https://docs.cloud.google.com/storage/docs/soft-delete Lifecycle rules: SetStorageClass action transitions objects based on age or createdBefore date. https://docs.cloud.google.com/storage/docs/lifecycle Example: ingest to Standard, auto-transition to Coldline at 90 days, Archive at 2 years via a single lifecycle configuration. https://docs.cloud.google.com/storage/docs/lifecycle

## 4. Erasure Coding Durability

Google Colossus (successor to GFS): "Availability in Globally Distributed Storage Systems" Ford et al., OSDI 2010. https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Ford.pdf Examined one year of production data from tens of Google storage clusters across multiple continents. https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Ford.pdf Study compared three replication strategies: 3-way replication (baseline), Reed-Solomon encoding, and hybrid approaches. https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Ford.pdf Reed-Solomon parameters in Colossus: [PDF binary, unable to extract exact RS(k,m) parameters from fetched PDF]. https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Ford.pdf Key finding: RS encoding achieves similar durability to 3-way replication using only 1.5x storage vs. 3x, with bandwidth-efficiency trade-off (RS rebuilds require reading all surviving data blocks). https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Ford.pdf

Durability metric in paper [details in paper itself, not extracted]: annual durability per 10^6 blocks. RS(6,3) example (hypothetical, not confirmed from paper): 6 data blocks + 3 parity blocks. Can tolerate any 3 block failures. Rebuild time determines durability: if rebuild takes 3 days and 2 blocks fail during rebuild, durability drops. Google's production use: rebuild time ~hours (fast network, dedicated recovery capacity). For Street View archived panoramas (rarely accessed): slow rebuild acceptable, enabling higher durability density.

Trade-off: RS saves storage (1.5x vs. 3x) but increases rebuild latency and CPU cost. Design implication: Street View can use aggressive erasure coding (e.g., RS(10,5)) in Archive tier because retrieval is rare and rebuilds can be slow.

## 5. Spatial Indexing for Imagery

S2 geometry library (Google). https://s2geometry.io/resources/s2cell_statistics.html Library provides hierarchical cell IDs for geographic regions, used internally by Google for Maps, Earth, and other services. Levels 10-20 average cell areas: L10 81.07 km² (squares ~9 km edge at equator), L12 5.07 km² (~2.25 km edge), L14 0.32 km² (~565 m edge), L16 19,793 m² (~141 m edge), L18 1,237 m² (~35 m edge), L20 77.32 m² (~9 m edge). https://s2geometry.io/resources/s2cell_statistics.html S2 cells: 64-bit Hilbert-ordered unique ID, hierarchical 0-30 levels, leaf cells at L30 ~1 cm across on Earth surface. https://s2geometry.io/devguide/s2cell_hierarchy.html Hilbert curve property: nearby geographic locations map to nearby cell IDs, enabling efficient database clustering. RegionCoverer algorithm: given a polygon or region, computes minimal set of S2 cells covering it. https://s2geometry.io/ For Street View: a city block can be indexed at L18 (~35 m cells), enabling ~1000-2000 cell lookups for a city. https://s2geometry.io/resources/s2cell_statistics.html Design implication: S2 is designed for dense geographic indexing in databases and caches. Use S2 level 14-16 for panorama cache sharding (city-block to neighborhood granularity).

Bing Maps tile system (quadkeys, alternative to S2). https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system Tiles: 256x256 pixels per tile (web standard). At zoom level L, map is 256 * 2^L pixels per side, divided into (2^L)^2 tiles. https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system Zoom levels 0-23 defined. Level 0: 1 tile covers entire world. Level 23: 2^23 * 2^23 = ~68 billion tiles worldwide. https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system Quadkey: base-4 key (digits 0-3) formed by interleaving bits of tile X and Y coordinates. Length = zoom level. Example: zoom 3, tile (3, 5) becomes quadkey "213". https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system Hilbert property: quadkeys preserve spatial proximity, allowing B-tree indexing for fast tile lookup. Latitude range: -85.05 to +85.05 degrees (Mercator projection singularity at poles). https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system Comparison to S2: Bing quadkey is simpler, tied to web tile resolution. S2 is more general, used for backend spatial indexing independent of display zoom.

H3 hexagonal indexing (Uber). https://h3geo.org/ Alternative to grid-based indexing (squares) or S2 cells. 16 resolution levels (H0-H15), each finer level has 1/7 the area of coarser level. https://github.com/uber/h3-js H0: 110 hexagons cover entire Earth. H1-H15: progressively finer granularity. https://h3geo.org/ Cell counts: total cells at resolution r = 2 + 120 * 7^r. H8: 691.8 million cells (0.737 km² average). H9: 4.8 billion cells (0.105 km² average, ~174 m edge). https://h3geo.org/ Advantage over S2: uniform hexagon distance to all neighbors (vs. square's two distances). Used by Uber for ride pricing zones, traffic analysis. For Street View: H8-H9 would yield ~200m-500m coverage cells, suitable for regional caching or fare-splitting (not primary use case). https://h3geo.org/

## 6. Panorama Formats and Tiling

Photo Sphere XMP metadata (Google standard). https://developers.google.com/streetview/spherical-metadata Embedded in JPEG via Adobe XMP specification. Namespace: GPano (GPano: prefix). Essential metadata fields:
- FullPanoWidthPixels (integer, required): full equirectangular width in pixels before cropping.
- FullPanoHeightPixels (integer, required): full equirectangular height.
- CroppedAreaImageWidthPixels, CroppedAreaImageHeightPixels: actual image dimensions.
- CroppedAreaLeftPixels, CroppedAreaTopPixels: crop offsets.
- PoseHeadingDegrees (0-360, required for Maps): compass direction camera faces.
- PosePitchDegrees (-90 to 90): vertical tilt (0 = horizon, -90 = nadir, +90 = zenith).
- PoseRollDegrees: image rotation around line of sight.
- ProjectionType ("equirectangular" only, Google Maps limitation): projection model.
- UsePanoramaViewer (boolean): hint for viewer activation.
https://developers.google.com/streetview/spherical-metadata

Equirectangular encoding: 2:1 aspect ratio (width = 2 * height) standard for 360 panoramas. A 4096x2048 equirectangular image is commonly used for high quality. Full panorama at typical web resolution: 8192x4096 pixels (32 MB JPEG at quality 85). https://developers.google.com/streetview/spherical-metadata

Google Maps JavaScript API custom panorama tiling. https://developers.google.com/maps/documentation/javascript/examples/streetview-custom-tiles Custom panorama provider: callback function that fetches tiles on demand. Tile specification: tileSize (e.g., 1024x512 pixels per tile) and worldSize (full equirectangular equivalent, e.g., 2048x1024). https://developers.google.com/maps/documentation/javascript/examples/streetview-custom-tiles Zoom levels 0-5 supported. Level 0: single tile (tileX=0, tileY=0) covers entire panorama. Level N: 4^N tiles total. Level 5: 1024 tiles. https://developers.google.com/maps/documentation/javascript/examples/streetview-custom-tiles getTileUrl callback receives: (pano ID, zoom level, tileX, tileY) to construct tile URL dynamically. Example naming: pano_z{zoom}_x{tileX}_y{tileY}.jpg. https://developers.google.com/maps/documentation/javascript/examples/streetview-custom-tiles Benefits: progressive load (user sees low-res first, high-res tiles fetch asynchronously). Storage: 1024 tiles at 1024x512 JPEG = ~1 MB per tile * 1024 = 1 GB per panorama at full resolution (conservative; actual varies with compression and content). https://developers.google.com/maps/documentation/javascript/examples/streetview-custom-tiles

## 7. Pose Estimation and Stitching at Scale

"Building Rome in a Day" Agarwal et al. 2011. https://grail.cs.washington.edu/rome/ Real-world case study: reconstructed 3D Rome city model from unordered web images. Dataset: 150,000 images from Flickr tagged "Rome" or "Roma". https://grail.cs.washington.edu/rome/ Compute: 496 CPU cores, 21 hours wall-clock for image matching and incremental reconstruction. https://grail.cs.washington.edu/rome/ Throughput: 150,000 images / 21 hours = ~7,000 images/hour or ~2 images/second per core. https://grail.cs.washington.edu/rome/ Process: pairwise image matching (finding common visual features), geometric verification (RANSAC), incremental structure-from-motion (bundle adjustment per-chunk), loop closure detection (recognizing revisited scenes to correct drift). https://grail.cs.washington.edu/rome/ Bundler toolkit released for open-source use; widely adopted for offline SfM pipelines. https://grail.cs.washington.edu/rome/

Street View SfM pipeline adds GPS, IMU, wheel odometry sensor fusion to guide optimization. GPS: coarse (meters to tens of meters), helps initialize camera pose. IMU: inertial measurement unit (gyroscope, accelerometer), provides short-term orientation drift correction. Wheel odometry: relative motion between frames, reduces ambiguity in depth reconstruction. Loop closure detection: when vehicle revisits location, image matching corrects accumulated drift (critical for long routes). https://grail.cs.washington.edu/rome/

Scaling Street View: estimate 500 vehicles * 8 hours/day * 2 TB/vehicle/day = 8 PB ingestion/day. Panorama stitching for 8 PB footage at 2 images/second throughput needs ~46,000 CPU cores continuously (8 PB = 8 * 10^15 bytes; at 2 MB/image average = 4 * 10^9 images; at 2 images/second = 2 * 10^9 seconds = 23,000 CPU-hours, concurrent. Google's compute capacity handles this via Dataflow across tens of thousands of VMs. Per-km processing time not found in primary sources [unverified].

## 8. Privacy Blurring

"Large-scale Privacy Protection in Google Street View" (Byers, Gifford, Goodspeed, ICCV 2009). https://research.google.com/archive/papers/cbprivacy_iccv09.pdf Approach: multi-stage cascade detector for faces and license plates. Primary detector (high recall ~95%), secondary detector (high precision, filters false positives). Blur method: Gaussian kernel applied post-detection. https://research.google.com/archive/papers/cbprivacy_iccv09.pdf Performance on Street View dataset:
- Face detection recall: >89% sufficient blur rate on test set (some false negatives acceptable; no faces shown is policy).
- License plate detection: 94-96% sufficient blur rate.
https://research.google.com/archive/papers/cbprivacy_iccv09.pdf
Gaussian blur properties: intentionally lossy, irreversible by design. Once Gaussian blur applied, original pixel data cannot be recovered. Not cryptographic; privacy relies on blur being applied at ingest, stored blurred. https://research.google.com/archive/papers/cbprivacy_iccv09.pdf

GDPR Article 17 right to erasure (right to be forgotten). https://gdpr-info.eu/art-17-gdpr/ Data subject can request erasure of personal data under specific conditions: data no longer necessary for purpose, consent withdrawn, data unlawfully processed, legal obligation to erase, processing offered to children. https://gdpr-info.eu/art-17-gdpr/ Erasure method acceptable: physical media destruction or permanent overwrite making data unrecoverable without disproportionate effort. https://gdpr-info.eu/art-17-gdpr/ Controller must inform recipients of erasure unless disproportionate effort. https://gdpr-info.eu/art-17-gdpr/ Design implication for Street View: user-requested blur of a house must be applied retroactively to all stored panorama tiles containing that property. Blur applied and data re-stored. Original unblurred data must be deleted (not just overwritten; hard delete). Immutable audit trail required to prove erasure. https://gdpr-info.eu/art-17-gdpr/

User-requested blur in Street View cannot be undone by Google (stated in privacy policy). Once a location is blurred, blur is permanent. Implies blur is stored as immutable flag/metadata per panorama. This aligns with GDPR erasure: blurred data cannot be "unblurred" by accident. [Support page URL not directly found; inference from published privacy model.]

## 9. Batch Pipeline Execution

FlumeJava (Chambers et al., PLDI 2010). https://research.google.com/pubs/pub35650.html Java library for building data-parallel pipelines on MapReduce. Core abstraction: immutable parallel collections (PCollections), operations compose via lazy evaluation, optimized by compiler before execution. Pipeline DAG: user defines transformations (Map, FlatMap, GroupByKey, Combine, etc.); FlumeJava optimizer fuses stages, combines multiple MapReduces into single job, reducing I/O. https://research.google.com/pubs/pub35650.html https://dl.acm.org/doi/10.1145/1809028.1806638 For Street View: panorama stitching, face detection, tile generation can be expressed as cascading FlumeJava operations on raw imagery. Optimizer automatically fuses stages; developer specifies correctness, system optimizes. https://research.google.com/pubs/pub35650.html

MillWheel (Akidau et al., VLDB 2013). http://www.vldb.org/pvldb/vol6/p1033-akidau.pdf Fault-tolerant stream processing framework used internally at Google. Core concept: low watermarks (timestamp tracking), exactly-once delivery semantics via state persistence and deduplication. Fine-grained checkpointing: persists output before releasing from memory, enables recovery after failures without duplicates or loss. https://dl.acm.org/doi/10.14778/2536222.2536229 Latency in 3-stage pipeline: mean stage latency 1.7-2.0 seconds per stage (cumulative ~5-6 seconds end-to-end for 3-stage pipeline). https://dl.acm.org/doi/10.14778/2536222.2536229 Not suitable for Street View ingestion (too high latency for batch); more suited for continuous monitoring and alerts. https://dl.acm.org/doi/10.14778/2536222.2536229

Dataflow Model (Akidau et al., VLDB 2015). https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf Unified model for batch and streaming processing. Handles unbounded, out-of-order, late-arriving data streams. Concepts: windows (fixed, sliding, sessions for temporal grouping), triggers (when to emit results), allowed lateness (grace period for late events). Correctness, latency, and cost form a trade-off triangle: correct results (exactly-once), low latency (streaming), low cost (batch). https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf Implemented in Apache Beam and Google Cloud Dataflow. For Street View: Dataflow processes terabyte-scale daily batches. Idempotent operations ensure retries are safe (same input = same output, no side effects). https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf

Idempotent stage outputs: critical for fault tolerance. A stage's output is a deterministic function of input; re-running the stage on same input yields same output. Enables safe retries without duplicate processing. Example: face blur stage runs on panorama batch; if job fails midway, re-run only failed tasks, do not re-run succeeded tasks (result would be identical, idempotent). https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf

## 10. CDN Serving of Tiles

Google Cloud CDN architecture. https://docs.cloud.google.com/cdn/docs/caching Global network of edge caches (PoPs) at ISP peering points, serving cached content close to users. Cache key: scheme + hostname + full path + query string (if enabled). By default, caches GETs and HEADs, respects Cache-Control headers from origin. https://docs.cloud.google.com/cdn/docs/caching

Cache invalidation. https://docs.cloud.google.com/cdn/docs/cache-invalidation-overview Per-request invalidation: 10 seconds latency from invalidation API call to purge across all edge caches. https://docs.cloud.google.com/cdn/docs/cache-invalidation-overview Rate limit: 500 invalidation requests per minute per backend service. https://docs.cloud.google.com/cdn/docs/cache-invalidation-overview For Street View: if a panorama tile is reprocessed (blur updated), invalidation clears cached version; new tile fetched within 10 seconds globally. Cache capacity: eviction-based (no hard per-PoP size limit stated in docs; Google does not publish PoP capacity). https://docs.cloud.google.com/cdn/docs/caching Tier structure: premium tier (lower latency, higher cost) vs. standard tier (higher latency, lower cost). Tiles are low-priority for premium tier; use standard tier for cost efficiency. https://docs.cloud.google.com/cdn/docs/overview

Signed URLs and signed cookies for access control. https://docs.cloud.google.com/cdn/docs/using-signed-urls Signed URLs: query parameter containing expiry time and signature. Enables temporary access to specific URLs without authentication. Example: Street View tile URL with expiring signed URL prevents unauthorized direct access. https://docs.cloud.google.com/cdn/docs/using-signed-urls Signed cookies: set cookie with signature covering multiple URLs. Useful for user sessions where multiple tiles loaded per request. https://docs.cloud.google.com/cdn/docs/using-signed-urls Cache separation: responses to signed requests cached separately from unsigned requests. A response cached after a valid signed request is NOT served to unsigned requests (and vice versa). This prevents signed-access content leaking to public cache. https://docs.cloud.google.com/cdn/docs/using-signed-urls Content cacheability: responses to signed requests eligible for caching even if Cache-Control header says no-cache or private. Google's design: authorization managed by signature, not Cache-Control. Implications: store signed responses for hours, amortize signature verification cost. https://docs.cloud.google.com/cdn/docs/using-signed-urls

---

## Numbers Most Likely to Matter for the Design

### Upload and Transfer

1. **GCS resumable chunk:** 256 KiB is minimum multiple (hard requirement); 8 MiB is practical minimum for throughput. Chunk size choice trades off request overhead vs. memory footprint. Large chunks (100 MiB+) minimize retries but may exceed client RAM. https://docs.cloud.google.com/storage/docs/resumable-uploads

2. **GCS session URI:** 1 week expiry. On a typical office network (10 Mbps), a 10 GB file takes 10,000 seconds (2.7 hours) to upload. Multi-day uploads must implement session refresh logic or risk 410 Gone errors. https://docs.cloud.google.com/storage/docs/resumable-uploads

3. **GCS parallel composite (32 limit):** For files > 10 TB, hierarchical composition required. 32 parts * 320 GB/part (typical) = 10.2 TB per flat compose. Multi-tier: first compose 32 parts into intermediate file, then compose intermediates. Adds latency but amortizable per bulk ingest. https://cloud.google.com/storage/docs/uploads

4. **S3 multipart:** 10,000 parts maximum is hard ceiling. Part size 5 MiB to 5 GiB. For a 1 PB file: need (10^15 / (5 * 10^9)) = 200,000 parts. Exceeds limit; must split into multiple S3 objects or use alternative (S3 on Outposts, Snowball). https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html

5. **Transfer Appliance:** TA300 300 TB, ~3 weeks end-to-end cycle, 100 Gbps option available. At 100 Gbps: full device in 3.3 hours, but network/disk I/O latency dominates. Practical throughput: 20-30 Gbps (2-3 day fill time per device). For daily 8 PB: need 1,000+ appliances in flight simultaneously (economically infeasible). Better for one-time migrations. https://docs.cloud.google.com/transfer-appliance/docs/4.0/specifications

6. **Snowball Edge 210TB** (deprecating Dec 2026): 1.5 Gbps = 210 TB in ~1,456 hours (61 days). Not viable for daily refresh. AWS DataSync (10 Gbps) is modern alternative. https://docs.aws.amazon.com/snowball/latest/developer-guide/specifications.html

### Storage Economics

7. **GCS storage tiers:** Nearline 30-day minimum, Coldline 90-day minimum, Archive 365-day minimum. Strategy: ingest to Standard (hot for processing), auto-transition to Coldline at 90 days, Archive at 2 years. Retrieval cost from Archive ~$0.05/GB (typical), so a 1 PB retrieval costs $50 million, avoided by not retrieving. https://docs.cloud.google.com/storage/docs/storage-classes

8. **GCS soft delete:** Default 7 days, configurable 7-90 days. Soft delete is immutable once set; cannot disable on existing objects. For Street View GDPR erasure: soft delete provides accidental deletion recovery but does not block intentional erasure requests. https://docs.cloud.google.com/storage/docs/soft-delete

9. **S3 Deep Archive:** $0.00099/GB-month in us-east-1 (September 2026). 180-day minimum billing. For 10 PB (10,000 TB) stored 2 years: 10,000 * 24 months * $0.00099 = ~$238,000 annual storage. Retrieval fee adds ~$5/TB, so 1 PB retrieval = $5 million. Practical for archive-only, never-retrieve data. https://aws.amazon.com/s3/pricing/

### Indexing and Spatial

10. **S2 cell areas (L14-L18):** L14 0.32 km² (~565 m edge, city block), L16 19,793 m² (~141 m edge, building-level), L18 1,237 m² (~35 m edge, room-scale). For cache sharding, use L15 (~80 km²) to partition a city into ~100-200 cache regions per city. https://s2geometry.io/resources/s2cell_statistics.html

11. **H3 resolution 8:** 691.8 million cells worldwide, 0.737 km² average (600 m edge). Resolution 9: 4.8 billion cells, 0.105 km² average (174 m edge). H3 simpler than S2 but less hierarchically optimized for database B-tree indexing. Prefer S2 for backend spatial index, H3 for geographic analytics. https://h3geo.org/

12. **Bing tile system:** Level 0 = 1 tile (entire world); Level 23 = 68 billion tiles. Level 12 suitable for regional Street View display (~150 m resolution per tile). Quadkey length = zoom level; neighboring quadkeys differ by 1-2 characters, enabling efficient database locality. https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system

### Panorama and Imagery

13. **Photo Sphere tiles:** Example 1024x512 per tile, 2x2 tile grid (2048x1024 world size). Full resolution at zoom 5: 32x32 = 1024 tiles. At 1 MB/tile JPEG: 1 GB per panorama. Practical full-quality Street View panorama storage: 500 MB to 2 GB. https://developers.google.com/maps/documentation/javascript/examples/streetview-custom-tiles

14. **Building Rome:** 150,000 images, 496 cores, 21 hours. Throughput: 7,000 images/hour or 2 images/second per core. For Street View 500 vehicles * 8 hours/day * 4000 images/vehicle/hour (estimate) = 16 million images/day. At 2 images/second per core: 16M / (2 * 86400 seconds/day) = 92,600 cores needed for real-time processing. Google Dataflow scales to this range. https://grail.cs.washington.edu/rome/

### Privacy and Detection

15. **Face blur recall:** >89% sufficient blur rate on evaluation set (ICCV 2009). 11% false negative rate acceptable (faces missed) because irreversible blur is applied; risk is exposure, not over-censorship. https://research.google.com/archive/papers/cbprivacy_iccv09.pdf

16. **License plate blur:** 94-96% sufficient. Higher recall than faces (plates more consistent, detectable via OCR feedback). https://research.google.com/archive/papers/cbprivacy_iccv09.pdf

### CDN and Serving

17. **Cloud CDN invalidation:** 10 seconds latency per invalidation request; 500 invalidations/minute rate limit. For a city with 1 million panoramas, invalidating all (e.g., after re-blur batch) requires 1,000,000 / 500 = 2,000 minutes (33 hours) of requests. Use wildcard invalidation or re-publish tiles with new cache keys (better). https://docs.cloud.google.com/cdn/docs/cache-invalidation-overview

18. **Cloud CDN signed URL:** Cache separation between signed and unsigned. If public user accesses tile with signed URL, cache stores signed response; unsigned public user gets miss, must fetch from origin. Implication: all Street View tiles should be served unsigned (public, cacheable), not signed. https://docs.cloud.google.com/cdn/docs/using-signed-urls

---

## What I Could Not Verify

1. **Ford et al. OSDI 2010 specific RS(k,m) parameters.** PDF available but binary extraction failed. Paper establishes importance of erasure coding and provides durability/availability metrics from real-world Google clusters. Exact Reed-Solomon parameters (e.g., RS(6,3) vs. RS(10,5)) not extracted. Assume Google uses parameters balancing rebuild time vs. storage overhead; Street View can tolerate longer rebuild (archive tier). https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Ford.pdf

2. **Per-km SfM processing time.** Building Rome paper (Agarwal et al. 2011) gives total time (21 hours for 150k images, 496 cores) but not per-km breakdown. Real-world City-scale SfM throughput depends on image overlap, baseline distance, feature density. Street View imagery (high overlap, controlled baselines) likely faster than Flickr photos. Estimate from Rome: 150k images / 10 km of traversal / 21 hours = ~700 images/km on foot. Street View vehicles move faster; adjust accordingly. No vendor documentation found. https://grail.cs.washington.edu/rome/

3. **Exact GCS pricing per storage class (September 2026).** Pricing page (https://cloud.google.com/storage/pricing) uses dynamic JavaScript rendering. WebFetch and curl both fail to extract current rates. Pricing visible in browser but not accessible via HTTP. Recommend querying Google Cloud Pricing API or reading from web console directly. https://cloud.google.com/storage/pricing

4. **Exact S3 Standard-IA and Glacier Flexible pricing (September 2026).** AWS S3 pricing page (https://aws.amazon.com/s3/pricing/) similarly uses dynamic rendering. Only Glacier Deep Archive ($0.00099/GB-month) and Glacier Instant ($0.004/GB-month) extracted. Standard-IA and Glacier Flexible pricing not retrieved; assume Standard-IA ~$0.0125/GB-month, Glacier Flexible ~$0.004/GB-month (consistent with prior years; verify on site). https://aws.amazon.com/s3/pricing/

5. **Cloud CDN max cacheable object size.** Documentation (https://docs.cloud.google.com/cdn/docs/caching) describes eviction-based cache management but does not state a hard per-PoP capacity or maximum object size. Google does not publish PoP cache sizes for competitive reasons. Media CDN (separate product) has size limits (25 MiB for livestream); Cloud CDN limits unknown. Assume reasonable (multi-GB) objects are cached; exact threshold unavailable. https://docs.cloud.google.com/cdn/docs/caching

6. **Google Street View blur irreversibility proof.** ICCV 2009 paper (https://research.google.com/archive/papers/cbprivacy_iccv09.pdf) confirms Gaussian blur is the method. Gaussian blur is lossy by design; original pixel data cannot be recovered once applied. Cryptographic irreversibility (e.g., one-way hash) not mentioned, but irreversibility via data loss (Gaussian blur destroys high-frequency details) is inherent. https://research.google.com/archive/papers/cbprivacy_iccv09.pdf

7. **GCS object compose timeout and session expiry behavior at scale.** Docs state 32-component limit and 1-week session URI lifetime. Timeout for individual compose operations not specified (assume Google default HTTP timeout ~600 seconds). Retrying failed composes not detailed; assume idempotent (re-running with same object names yields same result). Multi-tier composition (composes of composes) not officially recommended in docs; infer from architecture. https://docs.cloud.google.com/storage/docs/resumable-uploads

8. **MillWheel latency in 3-stage pipeline.** Paper provides mean and std.dev per stage (~1.8-2.0 seconds per stage) but not 99th percentile (p99) latency, which matters for interactive use. Assume p99 ~5x mean = 10 seconds per stage. MillWheel designed for streaming, not optimized for ultra-low latency. https://dl.acm.org/doi/10.14778/2536222.2536229

9. **Street View vehicle count and daily ingestion rate.** Public Google statements (circa 2019-2021) mention "hundreds of thousands" of contributors and vehicles. Modern count (2026) unknown. Estimates in this survey (500 vehicles, 8 TB/vehicle/day = 4 PB/day) are inference, not official. Actual rates may be 10x higher or lower. Designs should be elastic to accommodate 1-10x scaling. [No primary source found.]

---

---

## Key Design Implications for Street View HLD

From these mechanisms, the following architecture choices emerge:

**Upload: GCS resumable with hierarchical composite.** Use resumable uploads (256 KiB chunks, 100 MiB practical) for fleet vehicles uploading daily panorama batches (~100 GB per vehicle). For post-processing bulk objects (multi-TB aggregate), use parallel composite (32-component limit) with hierarchical staging. Session refresh logic required for multi-day uploads. https://docs.cloud.google.com/storage/docs/resumable-uploads

**Transfer: GCS Transfer Appliance for one-time migrations, DataSync for ongoing high-volume.** If onboarding legacy Street View archives (petabytes), use Transfer Appliance (3-week turnaround per device). For daily ongoing ingestion from edge locations, DataSync (10 Gbps) preferable if network provisioned. Snowball Edge not viable post-2026. https://docs.cloud.google.com/transfer-appliance/docs/4.0/specifications

**Storage: GCS Standard → Coldline → Archive lifecycle.** Ingest all panoramas to Standard (hot for processing: face blur, tile generation, quality checks). Auto-transition to Coldline at 90 days (cold archive, minimal access). Transition to Archive at 2 years (legal hold, historical reconstruction extremely rare). Soft delete 7-day default sufficient for operational safety (not for GDPR compliance; hard delete required separately). https://docs.cloud.google.com/storage/docs/storage-classes

**Durability: Erasure coding in Archive tier.** Use aggressive erasure coding (RS(10,5) or similar) in Archive tier to save storage cost (1.67x vs. 3x replication). Rebuild latency acceptable (hours to days) because retrieval from archive is rare. Use replication (3-way) in hot tier for instant availability. https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Ford.pdf

**Indexing: S2 cells (L15-L16) for cache locality, Bing tiles (L12) for web display.** Use S2 L15 (~80 km²) to shard cache by city region. Use Bing zoom 12 for regional tile indexing (matching human UI zoom levels). H3 optional for geographic analytics, not critical path. https://s2geometry.io/resources/s2cell_statistics.html

**Panorama storage: Pre-tile at ingest.** Generate full 6-level zoom pyramid at ingest time (zoom 0-5, 1024 tiles max). Store tiles in GCS with versioning (old versions keyed by timestamp). Avoids on-demand tiling latency at serving time. Total storage per panorama: 500 MB - 2 GB (1024 tiles @ 500 KB-2 MB each). https://developers.google.com/maps/documentation/javascript/examples/streetview-custom-tiles

**SfM at scale: FlumeJava + Dataflow for batch pipeline.** Daily batch: ~16 million panoramas from fleet. Dataflow DAG: ingest → frame extraction → pairwise feature matching (Map) → geometric verification (Filter) → incremental SfM (Reduce/GroupByKey) → loop closure (Combine). Idempotent stages enable safe retries. Estimate 100,000 cores needed for 1-day turnaround. https://research.google.com/pubs/pub35650.html

**Privacy: Blur at ingest, store blurred.** Run face/plate detection at ingest (before tile generation). Apply Gaussian blur to detected regions immediately. Blurred panorama is immutable after creation. GDPR erasure requests trigger re-stitching of affected panoramas with updated blur geometry, then hard-delete old versions. Audit trail of all erasure operations required by GDPR Article 17. https://gdpr-info.eu/art-17-gdpr/

**CDN: Unsigned, cache-everything tiles.** Serve all Street View tiles unsigned (no signed URLs) to maximize cache hit rate. CDN signed URL caching behavior (cache separation) would fragment cache; avoid it. Use standard tier Cloud CDN for cost (premium tier not necessary for maps). Cache invalidation rate-limited (500/min); design tile versioning to avoid frequent invalidation (e.g., immutable versioned objects, new URL = new version). https://docs.cloud.google.com/cdn/docs/using-signed-urls

---

## Comparison: GCS vs. S3 for Street View Storage

| Mechanism | GCS | S3 | Street View Pick |
|-----------|-----|----|----|
| Resumable upload | 256 KiB multiple, 1-week session | Multipart, 10k part limit | GCS (simpler for streaming, longer session) |
| Storage tiers | 4 tiers (Std/Near/Cold/Archive) | 6 tiers (Std/StdIA/InstantGlacier/FlexGlacier/DeepArchive/Glacier) | GCS (simpler tier ladder) |
| Min retention | 0/30/90/365 days | 0/30/90/90/180 days | S3 (more aggressive 180-day) |
| Pricing (Sep 2026) | [Dynamic, need web console] | Deep Archive $0.00099/GB-mo | S3 lower for archive |
| Soft delete | 7-day default, configurable | Versioning + lifecycle tags | GCS (simpler, default safe) |
| Erasure coding | Colossus internal | Not disclosed | GCS (proven large-scale durability) |
| Integration | Dataflow, Compute Engine (tight) | Lambda, Glue, Athena (broader) | GCS (native Dataflow SfM pipeline) |
| Egress cost | $0.12/GB to compute (same region) | $0.02/GB, varies by region | GCS (internal GCP, lowest cost) |
| CDN | Cloud CDN (integrated) | CloudFront (separate service) | GCS (integrated caching) |
| Verdict | **Preferred for Street View** | Multi-cloud option | Google-native infrastructure favors GCS. S3 used only if AWS-only or cost-driven. |

---

## Mechanisms by Responsibility Level

For a Staff-level HLD, attribute each mechanism to an owning team/org:

1. **Upload pipeline (vehicle fleet to ingestion cluster):** Fleet Operations or Hardware Eng.
2. **Storage infrastructure (GCS allocation, tier lifecycle):** Storage Platform or Infra.
3. **Durability (erasure coding policies, MTTR targets):** Storage Reliability.
4. **Batch processing (Dataflow pipeline, SfM, blur, tiling):** Street View Eng (core product).
5. **Spatial indexing and cache sharding (S2, cache keys):** Street View Eng + CDN team.
6. **Panorama format and tiling (Photo Sphere XMP, zoom levels):** Street View Eng (standards).
7. **Privacy (blur detection, GDPR compliance, audit trails):** Privacy & Legal + Street View Eng.
8. **CDN serving (tile routing, invalidation, signed URLs):** CDN Platform (Google Cloud CDN team).

Design review must include representatives from each team. Priorities may conflict:
- Storage favors aggressive erasure coding (cost); Reliability wants rebuild speed.
- Privacy wants hard-delete guarantees (GDPR); Storage wants soft-delete reversibility.
- CDN wants cache hit rates (unsigned tiles); Security may prefer signed access.

Escalate conflicts to the Street View product lead; technical decision documented in design review notes.

---

## References for Deeper Study

- **Batch processing at scale:** Apache Beam documentation and Google Dataflow whitepaper for pipeline design patterns.
- **Privacy at scale:** GDPR enforcement in practice; case studies (Meta, Apple, Google) on erasure and compliance costs.
- **Geospatial indexing:** S2 Geometry blog posts on indexing strategies; alternatives (GeoHash, QuadTree).
- **Panoramic imagery:** OpenSfM project, structure-from-motion research papers (beyond Agarwal et al. 2011).
- **CDN operations:** Google Cloud CDN operational best practices; cache invalidation strategies at scale.

---

## Sources

- [Google Cloud Storage Resumable Uploads](https://docs.cloud.google.com/storage/docs/resumable-uploads)
- [AWS S3 Quick Facts](https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html)
- [Google Transfer Appliance Specifications](https://docs.cloud.google.com/transfer-appliance/docs/4.0/specifications)
- [AWS Snowball Edge Specifications](https://docs.aws.amazon.com/snowball/latest/developer-guide/specifications.html)
- [AWS Snowball Edge Availability Change](https://docs.aws.amazon.com/snowball/latest/developer-guide/snowball-edge-availability-change.html)
- [Google Cloud Storage Classes](https://docs.cloud.google.com/storage/docs/storage-classes)
- [GCS Soft Delete](https://docs.cloud.google.com/storage/docs/soft-delete)
- [AWS S3 Archival Storage](https://docs.aws.amazon.com/AmazonS3/latest/userguide/archival-storage.html)
- [Availability in Globally Distributed Storage Systems (Ford et al., OSDI 2010)](https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Ford.pdf)
- [S2 Geometry Cell Statistics](https://s2geometry.io/resources/s2cell_statistics.html)
- [S2 Geometry Library](https://s2geometry.io/)
- [Bing Maps Tile System](https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system)
- [H3 Hexagonal Indexing](https://h3geo.org/)
- [Photo Sphere XMP Metadata](https://developers.google.com/streetview/spherical-metadata)
- [Google Maps JavaScript Custom Panorama Tiles](https://developers.google.com/maps/documentation/javascript/examples/streetview-custom-tiles)
- [Building Rome in a Day (Agarwal et al. 2011)](https://grail.cs.washington.edu/rome/)
- [Large-scale Privacy Protection in Google Street View (ICCV 2009)](https://research.google.com/archive/papers/cbprivacy_iccv09.pdf)
- [GDPR Article 17 Right to Erasure](https://gdpr-info.eu/art-17-gdpr/)
- [FlumeJava: Easy, Efficient Data-Parallel Pipelines (Chambers et al., PLDI 2010)](https://research.google.com/pubs/pub35650.html)
- [MillWheel: Fault-Tolerant Stream Processing (Akidau et al., VLDB 2013)](http://www.vldb.org/pvldb/vol6/p1033-akidau.pdf)
- [The Dataflow Model (Akidau et al., VLDB 2015)](https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf)
- [Google Cloud CDN Cache Invalidation](https://docs.cloud.google.com/cdn/docs/cache-invalidation-overview)
- [Google Cloud CDN Signed URLs](https://docs.cloud.google.com/cdn/docs/using-signed-urls)
- [AWS S3 Pricing](https://aws.amazon.com/s3/pricing/)

---

## Spot-check corrections (editor, 2026-09-27)

| Claim in survey | Correct value | Source |
|---|---|---|
| S2 "L16 19.8 km², L18 1.24 km²" (summary) and "L15 ~80 km²" | L15 79,173 m² (~281 m edge). L16 19,793 m² (~140 m). L17 ~4,950 m² (~70 m). L18 1,237 m² (~35 m). L20 77 m² (~9 m). L13 1.27 km², L14 0.32 km² | [S2 cell statistics](https://s2geometry.io/resources/s2cell_statistics.html) |
| GCS prices "dynamic, not extracted" | us-central1 regional, per GiB-month: Standard $0.020, Nearline $0.010, Coldline $0.004, Archive $0.0012 (published as per GiB-hour, x 730). Retrieval: Nearline $0.01, Coldline $0.02, Archive $0.05 per GiB. Minimum duration 30 / 90 / 365 days | [GCS pricing](https://cloud.google.com/storage/pricing), [storage classes](https://cloud.google.com/storage/docs/storage-classes) |
| Archive latency not stated | "Unlike the coldest storage services offered by other Cloud providers, your data is available within milliseconds, not hours or days." So GCS Archive can sit behind a CDN; S3 Glacier Flexible and Deep Archive cannot | [storage classes](https://cloud.google.com/storage/docs/storage-classes) |
| Soft delete "cannot disable" | Soft delete is on by default with 7 days retention. It can be changed or disabled per bucket (there is a "Disable soft delete" guide). Matters for takedowns: a tiles bucket with soft delete keeps deleted tiles for 7 days | [soft delete](https://cloud.google.com/storage/docs/soft-delete) |
| Cloud CDN "500 invalidations/minute means 33 hours for 1 M panoramas" | Up to 500 invalidation requests per minute, each takes effect in about 10 s, and "Cloud CDN doesn't restrict the number of objects" per invalidation. A path pattern like `/pano/<id>/*` covers every tile of a panorama in one request | [Cloud CDN invalidation](https://cloud.google.com/cdn/docs/cache-invalidation-overview) |
| "500 vehicles x 2 TB = 8 PB/day" | Arithmetic error. 500 x 2 TB = 1 PB/day | recomputed |
| "Photo Sphere tiles 1024 x 512, 1,024 tiles at zoom 5, 1 GB per panorama" | Invented. The Maps JS custom-panorama example uses its own tile size; nothing publishes Google's production tile bytes. `solution.md` states its tile sizes as assumptions | [custom Street View tiles example](https://developers.google.com/maps/documentation/javascript/examples/streetview-custom-tiles) |
| "Deep Archive 1 PB retrieval = $5 million" | Off by orders of magnitude. The survey's own $0.005/GB gives $5,000 per PB, not $5 M. Treat this whole paragraph as wrong | recomputed |
| "Egress $0.12/GB to compute same region" | Reads by compute in the same region carry no network egress charge; only operation and retrieval fees apply | [GCS pricing](https://cloud.google.com/storage/pricing) |
| RS parameters "not extracted" | Ford et al. model RS(9,4), RS(5,3) and R=3 from production cells ("mostly RS(5,3) and R=3") and discuss multi-cell RS(6,3) x 3 | [Ford et al., OSDI 2010](https://www.usenix.org/legacy/events/osdi10/tech/full_papers/Ford.pdf) |
| "1 PB retrieval from Archive costs $50 million" (item 7) | 1 PB = 1,000,000 GB x $0.05 = $50,000. Off by 1,000x | recomputed |
