# Google Maps Street View Ingestion: Interview Framing Survey

**Survey Date:** 2026-09-27  
**Objective:** Inventory how this L6/L7 system design prompt appears, what interviewers probe, and grading standards.

**Why This Question Tests Staff Level:**
Street View ingestion sits at the intersection of several Staff-level concerns: petabyte-scale distributed storage, real-time image capture from a mobile fleet with poor/intermittent connectivity, privacy and legal (GDPR, takedowns, face-blurring), spatial indexing to enable search and serving, and cost optimization across hot/cold tiers. A Senior engineer designs one service. A Staff engineer designs how a team would operate this system across data centers, with observability, migration paths, and trade-offs between velocity, cost, and correctness.

---

## 1. How the Prompt Appears in Candidate Reports

### Verified Phrasings

**TryExponent.com** (3 documented instances, last asked 4 years ago):
"Design Google Street View using 1000 cars to map every address and image worldwide."  
[https://www.tryexponent.com/questions/2109/design-google-street-view-1000-cars](https://www.tryexponent.com/questions/2109/design-google-street-view-1000-cars)

**HelloInterview.com** (in community questions):
"Design a system for collecting Street View images from taxi-mounted cameras that can handle high-volume uploads, deduplication, and prepare images for privacy/quality processing."  
[https://www.hellointerview.com/community/questions/image-uploader-dedup/cm4t1rgrn005988ilm7ct8ma1](https://www.hellointerview.com/community/questions/image-uploader-dedup/cm4t1rgrn005988ilm7ct8ma1)

**IGotAnOffer.com**:
"Design Street View" listed as a Google system design interview question.  
[https://igotanoffer.com/blogs/tech/google-system-design-interview](https://igotanoffer.com/blogs/tech/google-system-design-interview)

**SystemDesignHandbook.com**:
"Google Maps System Design" covers full mapping infrastructure including Street View. Specifies: "Specialized vehicles equipped with cameras capture 360-degree photos along roads worldwide, with pedestrian-mounted cameras covering areas inaccessible by vehicle."  
[https://www.systemdesignhandbook.com/guides/google-maps-system-design/](https://www.systemdesignhandbook.com/guides/google-maps-system-design/)

### Prompt Variants Inferred from Analogs

Based on prep site patterns and vehicle telemetry design questions widely asked:
- "Design the pipeline that ingests images from Street View cars" (inference: operational framing)
- "Store and serve petabytes of 360-degree imagery with location indexing" (inference: storage-focused framing)
- "Design a system for high-bandwidth image collection from a fleet of vehicles with poor connectivity" (inference: networking constraint emphasis)
- Related at other companies: "Design a system to collect and label driving footage" (Tesla, Waymo, Applied Intuition)

---

## 2. What Interviewers Probed

### Verified From Prep Sites

**TryExponent system design evaluation signals** (L6 context):
1. Requirement framing: "turn a one-line prompt into concrete design, naming users, scale, and latency targets before you build"
2. First-principles depth: explain how a component works, not just name the product
3. Trade-off reasoning: weigh real alternatives and defend the choice out loud
4. Scaling judgment: account for load, growth, failure early; say plainly when a clean approach stops working at Google scale
5. Collaboration: respond to constraints and pushback in real time, treat as working session  
[https://www.tryexponent.com/blog/google-system-design-interview](https://www.tryexponent.com/blog/google-system-design-interview)

**DesignGurus vehicle data ingestion** (Applied Intuition, similar scale):
- Storage cost of massive drive log volumes
- Indexing and retrieval to locate specific events
- Log replay capability for scenario reconstruction
- Safety-first validation (late brake command has physical cost)
- Problem scoping ability scores higher than architectural complexity
[https://www.designgurus.io/answers/detail/what-to-expect-in-the-applied-intuition-system-design-interview](https://www.designgurus.io/answers/detail/what-to-expect-in-the-applied-intuition-system-design-interview)

**Samsara fleet telemetry** (500k vehicles, 100k writes per second):
- Scale: 500,000 vehicles, one location every 5 seconds = 100,000 writes per second
- Freshness vs cost trade-off: "dashboards may show data a few seconds late"
- Offline handling and retry logic for late-arriving data
- Duplicate message detection via sequence numbering
- Partitioning strategy: "by device and by time window"
- Live state in cache (Redis) vs archival in time-series DB
[https://www.designgurus.io/answers/detail/what-to-expect-in-the-samsara-system-design-interview](https://www.designgurus.io/answers/detail/what-to-expect-in-the-samsara-system-design-interview)

### Likely Probe Areas (Inference)

Based on vehicle + imaging analogs (Tesla, Waymo, Rivian, Google Photos):
- Number of cars, frequency of image capture (images per second, TB per car per day)
- Upload connectivity: how to handle poor/intermittent connectivity from vehicles
- Object size: handling massive 360-degree panoramas (multiple GB per capture)
- Deduplication: preventing duplicate uploads, content-based dedup (bloom filters, hashing)
- Spatial indexing: "find images near latitude/longitude" (geohashing, quadtrees)
- Lifecycle and cost tiers: hot storage (recent images, fast access) vs cold (archive)
- Reprocessing strategy: when CV algorithms improve, which images need reprocessing? Replay logs?
- Privacy concerns: auto-blurring of faces and license plates
- Takedown requests: GDPR, "right to be forgotten" for specific locations/times
- Serving tiles and freshness: how quickly do new images appear in Maps?
- Async processing: thumbnail generation, stitching 360s, privacy processing shouldn't block upload confirmation

---

## 3. How Google L6 / L7 System Design is Graded

### From Published Rubrics

**DesignGurus: L6 is a Different Bar, Not Harder L5**  
[https://www.designgurus.io/blog/system-design-interview-l6-engineers](https://www.designgurus.io/blog/system-design-interview-l6-engineers)

"At L5 you prove you can design a system. At L6 you prove you can design how a team designs systems."

L6 systems are platforms hosting many services (not one service). L6 questions come with conflicting business priorities; candidates decide which to honor.

**Seven Grading Signals (L6):**
1. Interview Leadership: drive scope, name constraints, don't answer passively
2. Business Acumen: make priorities visible (latency vs cost vs correctness), not just technical
3. Comparative Analysis: hold multiple alternatives, articulate why rejected options are inferior
4. Failure Mode Thinking: cascading failures, partial degradation, dependency chains
5. Organizational Ownership: which teams own which parts, define contracts
6. Operational Maturity: deployment, observability, runbooks, migration plans (L5 skips these)
7. Scaled Communication: explain complexity so multiple teams with different priorities understand

**HelloInterview: L6 Architectural Expectations**  
[https://www.hellointerview.com/guides/google/l6](https://www.hellointerview.com/guides/google/l6)

Must address global scale (millions of users or QPS), multi-datacenter availability, replication and partitioning strategies, consistency models, fault tolerance, security, long-term evolution planning. Demonstrates proactive depth, not waiting for prompts.

**TryExponent: Five Evaluation Dimensions**  
[https://www.tryexponent.com/blog/google-system-design-interview](https://www.tryexponent.com/blog/google-system-design-interview)

1. Requirement framing
2. First-principles depth
3. Trade-off reasoning
4. Scaling judgment
5. Collaboration

### Google's Public Position

Google does not publish a public rubric for this round. The above reflects consistent patterns candidates report.  
[https://www.designgurus.io/blog/system-design-interview-l6-engineers](https://www.designgurus.io/blog/system-design-interview-l6-engineers)

### Interview Structure

For L6 and above, candidates usually face two system design interviews in an onsite loop (total 5 interviews: 2 coding, 2 design, 1 behavioral). The design rounds run 45 minutes to an hour each and are graded on breadth (how wide you scope) and depth (how deep you probe your own design).

**L7 Addition:** System design becomes the deciding round twice. L7 loops include two system design interviews, each potentially longer than standard 45 minutes, suggesting an even higher bar for complexity and tradeoff articulation.  
[https://www.designgurus.io/answers/detail/what-is-a-level-7-engineer-at-google](https://www.designgurus.io/answers/detail/what-is-a-level-7-engineer-at-google)

---

## 4. Published Worked Answers

### Exact Street View Answer

**Not found.** No verbatim Street View solution is publicly available on the allowed domains.

TryExponent has the question but requires login for detailed answer guidance.

### Closest Analogs Published in Full

**Google Photos System Design**  
[https://www.systemdesignhandbook.com/guides/google-photos-system-design/](https://www.systemdesignhandbook.com/guides/google-photos-system-design/)

Functional Requirements: multi-device upload, EXIF metadata extraction (location, timestamp, camera), thumbnails and search (by date, location, objects, faces, OCR), sharing/albums.

Non-Functional Requirements: high availability for metadata; durability with geographic replication; sub-200ms latency for thumbnails and search; cost optimization at scale.

Scale: over 1B photos daily; trillions total storage.

Ingestion: client-side dedup (hash before upload), resumable uploads (4-8MB chunks), asynchronous processing (thumbnails, transcoding, ML inference triggered via message queue while user gets immediate confirmation).

Storage: multi-resolution (256×256 thumbnail, preview, original); content-addressable by SHA-256; access frequency determines tier (recent in hot, 90+ days to cold).

**Google Maps System Design** (includes Street View component)  
[https://www.systemdesignhandbook.com/guides/google-maps-system-design/](https://www.systemdesignhandbook.com/guides/google-maps-system-design/)

Covers map data ingestion, spatial indexing (quadtrees, R-trees, geohashing), vector vs raster tile rendering, geocoding, routing, real-time traffic.

On Street View specifically: "Specialized vehicles equipped with cameras capture 360-degree photos along roads worldwide, with pedestrian-mounted cameras covering areas inaccessible by vehicle." Requires massive storage for billions of images optimized for sequential access, stitching algorithms for seamless panoramas, privacy processing (auto-blur faces/plates), spatial indexing to locate images near coordinates.

**Samsara Fleet Telemetry** (sensor ingestion from vehicles at scale)  
[https://www.designgurus.io/answers/detail/what-to-expect-in-the-samsara-system-design-interview](https://www.designgurus.io/answers/detail/what-to-expect-in-the-samsara-system-design-interview)

Scale: 500k vehicles, one location every 5 seconds (100k writes per second), trillions of sensor points per year.

Architecture: devices send to gateway service (auth), write to message queue (Kafka), recent state in cache (Redis), full history in time-series DB.

Trade-offs: freshness vs cost (allow seconds of lag); offline handling (devices upload late data when reconnected); duplicate detection (sequence numbers).

Storage partitioning: by device and by time window.

**Tesla System Design** (driving footage collection and labeling)  
[https://www.systemdesignhandbook.com/guides/tesla-system-design-interview/](https://www.systemdesignhandbook.com/guides/tesla-system-design-interview/)

Common question: "Design a system to collect and label driving footage for training models."

Key challenges: high-bandwidth video ingestion, distributed labeling queues, human-in-the-loop feedback, data storage optimization (object storage, sharding).

**Waymo Fleet Telemetry and Events**  
[https://www.designgurus.io/answers/detail/what-to-expect-in-the-waymo-system-design-interview](https://www.designgurus.io/answers/detail/what-to-expect-in-the-waymo-system-design-interview)

Design fleet telemetry and event pipelines where vehicles generate enormous sensor volumes. Key decisions: what uploads real-time (health, incidents) vs at depot (full logs), event triage, incident reconstruction (complete data around any event).

---

## 5. Probe Questions Ranked by Likelihood

**Verified Report (V) / Prep-Site Pattern (P) / Inference (I)**

These are ordered by likelihood based on what prep sites say interviewers consistently probe, what vehicle/imaging analogs reveal, and what the TryExponent prompt surfaces.

1. **(V/P)** "You have 1000 cars, each with 10 cameras capturing continuously. Roughly how many images per second, and how many TB per day?" (Scale estimation; from TryExponent prompt and Samsara 100k writes per second pattern)

2. **(V/P)** "A car is in a tunnel with no signal for 2 hours. How do you handle the image buffer and eventual upload when connectivity returns?" (Poor connectivity; from vehicle telemetry analogs like Samsara, Applied Intuition)

3. **(V/P)** "How do you detect and prevent uploading the same image twice?" (Deduplication; from Google Photos ingestion, applied to same road traveled multiple days)

4. **(I)** "Given a 360-degree panorama is 2-4 GB, how do you handle upload resumption mid-transfer?" (Large objects; from "large blobs pattern" and Google Photos multi-chunk upload)

5. **(I)** "A user requests their image removed from Street View (GDPR takedown). How do you find and delete it?" (Takedown requests; standard privacy concern for location imagery)

6. **(I)** "We improve the face-blur algorithm. How do you reprocess old images without re-downloading?" (Reprocessing; from vehicle data replay concept in Applied Intuition)

7. **(I)** "New images should appear in Google Maps within 30 days. How does that affect your storage and processing architecture?" (Freshness SLA; from TryExponent "scaling judgment" and Samsara "freshness vs cost")

8. **(I)** "Design a query to find all images within 500 meters of lat/lon. What index structure do you use?" (Spatial indexing; implied by "map near coordinates" in Google Maps guide, geohashing/quadtree standard)

9. **(P)** "Differentiate between images for offline download (compressed thumbnails), search (searchable metadata), and machine learning (high-fidelity originals). How do storage and cost differ?" (Lifecycle tiers; from Google Photos hot/cold strategy and Applied Intuition "storage cost" probe)

10. **(I)** "A competitor's car captured the same intersection. Do you deduplicate across fleets, or keep separate?" (Business/scope boundary; from DesignGurus "organizational ownership" L6 signal)

11. **(I)** "Describe your observability strategy. What metric wakes up an on-call engineer at 3am?" (Operability; from DesignGurus L6 signal on operational maturity)

12. **(P)** "How would you incrementally migrate this system if it already exists in production?" (Migration and rollback; from DesignGurus L6 signal on migration plans)

---

## 6. What Could Not Be Verified

1. **Exact candidate reports.** No TeamBlind or Reddit thread discusses Street View ingestion as a specific question with candidate debriefs. Search results returned general L6 interview posts but no Street View-specific experience reports.

2. **Official Google rubric.** Google does not publish system design grading criteria. All rubrics cited come from prep sites summarizing reported patterns.

3. **Number of cars and scale specifics.** TryExponent specifies "1000 cars" but this may be illustrative. No source confirms whether Google actually uses this exact scale in the question.

4. **Interview variants across teams.** It is unknown whether Street View ingestion is asked the same way across Google Cloud, Maps, and Search teams, or how L5 vs L6 versions differ.

5. **Interviewer follow-up scripts.** No public document exists showing the exact follow-up questions or pivots Google interviewers use.

---

## Sources

- [TryExponent: Design Google Street View](https://www.tryexponent.com/questions/2109/design-google-street-view-1000-cars)
- [HelloInterview: Image Uploader Deduplication](https://www.hellointerview.com/community/questions/image-uploader-dedup/cm4t1rgrn005988ilm7ct8ma1)
- [IGotAnOffer: Google System Design Interviews](https://igotanoffer.com/blogs/tech/google-system-design-interview)
- [SystemDesignHandbook: Google Maps System Design](https://www.systemdesignhandbook.com/guides/google-maps-system-design/)
- [SystemDesignHandbook: Google Photos System Design](https://www.systemdesignhandbook.com/guides/google-photos-system-design/)
- [DesignGurus: System Design Interview L6 Engineers](https://www.designgurus.io/blog/system-design-interview-l6-engineers)
- [DesignGurus: Google L6 (Staff) Interview Guide](https://www.designgurus.io/blog/google-software-engineer-levels)
- [DesignGurus: Applied Intuition System Design Interview](https://www.designgurus.io/answers/detail/what-to-expect-in-the-applied-intuition-system-design-interview)
- [DesignGurus: Samsara System Design Interview](https://www.designgurus.io/answers/detail/what-to-expect-in-the-samsara-system-design-interview)
- [DesignGurus: Waymo System Design Interview](https://www.designgurus.io/answers/detail/what-to-expect-in-the-waymo-system-design-interview)
- [HelloInterview: Google L6 Guide](https://www.hellointerview.com/guides/google/l6)
- [TryExponent: Google System Design Interview Blog](https://www.tryexponent.com/blog/google-system-design-interview)
- [HelloInterview: Handling Large Blobs Pattern](https://www.hellointerview.com/learn/system-design/patterns/large-blobs)
- [SystemDesignHandbook: Tesla System Design](https://www.systemdesignhandbook.com/guides/tesla-system-design-interview/)
- [GitHub: donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer)

---

## Spot-check corrections (editor, 2026-09-27)

| Claim in survey | Check | Source |
|---|---|---|
| TryExponent prompt "Design Google Street View using 1000 cars to map every address and image worldwide" | Confirmed verbatim on the page title | [TryExponent](https://www.tryexponent.com/questions/2109/design-google-street-view-1000-cars) |
| Hello Interview "Design an Image Uploader" for taxi-mounted Street View cameras | Confirmed verbatim, tagged "Asked at: Google" | [Hello Interview](https://www.hellointerview.com/community/questions/image-uploader-dedup/cm4t1rgrn005988ilm7ct8ma1) |
| Probe 4 "a 360 panorama is 2 to 4 GB" | Invented number. A published Photo Sphere is capped at 75 MB. A raw capture from a multi-camera rig is tens of MB. `solution.md` uses its own stated assumptions | [photo requirements](https://support.google.com/maps/answer/7012050?hl=en) |
| Probes tagged (V/P) 1 to 3 | Only the prompts are verified. The follow-up wording is the agent's inference from analog questions, not a candidate report | n/a |
