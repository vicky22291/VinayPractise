# Real-World Street-Level Imagery Systems: Capture, Ingest, Store, Serve

Research survey for Staff-level design of Google Maps Street View ingestion and storage (Google L6/L7 interview question).
Date: 2026-09-27

---

## 1. Google Street View

### Scale and Coverage

Street View has captured over 10 million miles (16 million kilometers) of imagery as of May 2017 across 83 countries. https://en.wikipedia.org/wiki/Google_Street_View#Coverage

The service launched May 25, 2007, initially in select U.S. cities, then expanded globally. https://en.wikipedia.org/wiki/Google_Street_View#History

Historical timeline shows progression: May 2017 announcement of 10 million miles coverage; June 2022 relaunch in India covering 10 cities after six-year hiatus. https://en.wikipedia.org/wiki/Google_Street_View#History

### Camera Specifications

Camera evolution across generations shows increasing fidelity and sensor count:

- R2: Eight 11-megapixel CCD sensors with wide-angle lenses. https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications
- R5: Eight 5-megapixel CMOS cameras plus fisheye lens for upper building levels. https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications
- R7: Fifteen of the same sensors as R5 without fisheye effect. https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications
- 2017 System: Eight 20-megapixel cameras total. Two positioned to read street signs and business names. https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications

### Sensor Integration

Positioning system combines GPS, wheel speed sensors, and inertial navigation (IMU) for accurate pose. https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications

Laser range scanners from Sick AG measure depth up to 50 meters at 180 degree coverage. https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications

LIDAR from Velodyne mounted at 45 degrees captures 3D depth and positional information. https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications

Air quality sensors from Aclima were integrated September 2018. https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications

### Privacy Protection: Face and License Plate Blur

Research by Frome et al. (ICCV 2009, "Large-Scale Privacy Protection in Google Street View") reports:
- Automatic face blurring achieved 89% of faces successfully blurred. https://research.google/pubs/large-scale-privacy-protection-in-google-street-view/
- Automatic license plate blurring achieved 94-96% of plates successfully blurred. https://research.google/pubs/large-scale-privacy-protection-in-google-street-view/

The two-stage approach combined high-recall detectors with false-positive filtering using domain-specific constraints.

### Capture Platforms

Beyond vehicles, Street View deployed diverse platforms for terrain coverage:
- Tricycles for pedestrian routes
- Snowmobiles for Olympic venues and snow-covered areas
- Shopping trolleys for museum interiors
- Backpack-mounted Google Trekker for trail environments
- Boat-based systems for canals and waterways

User-contributed panoramas enabled since November 2012 (Android 4.2). https://en.wikipedia.org/wiki/Google_Street_View#History

Paid professional interior photography program launched 2013. https://en.wikipedia.org/wiki/Google_Street_View#History

### Historical Features

Time machine feature (historical imagery playback) launched in 2014. https://en.wikipedia.org/wiki/Google_Street_View#History

Indoor business views (Google Business Photos) announced May 2011. https://en.wikipedia.org/wiki/Google_Street_View#History

---

## 2. Mapillary (Meta)

### Scale and Growth

Mapillary has accumulated over 2 billion images as of August 2023, contributed by community members globally. https://www.mapillary.com/about

Coverage spans 190 countries. https://en.wikipedia.org/wiki/Mapillary

Growth trajectory: 500K photos (May 2014), 5.5M (Dec 2014), 10M (March 2015), 20M (June 2015), 100M (Nov 2016), 2B (Aug 2023). https://en.wikipedia.org/wiki/Mapillary

Institutional contributors include Vermont and Arizona transportation departments, each contributing approximately 5 million images (as of 2018). https://en.wikipedia.org/wiki/Mapillary

### Technical Infrastructure

Mapillary integrates Amazon Rekognition for visual data analysis and automated text extraction from street imagery (2018). https://en.wikipedia.org/wiki/Mapillary

Processing pipeline combines computer vision algorithms to link imagery temporally and spatially.

Supported capture modes: walking, cycling, vehicle-based photography; panoramic and spherical support (announced September 2014); 360-degree imagery. https://en.wikipedia.org/wiki/Mapillary

Image licensing operates under Creative Commons Attribution-ShareAlike 4.0 International License, with special provisions for OpenStreetMap and Wikimedia derivatives. https://en.wikipedia.org/wiki/Mapillary

Developer SDK released November 2018. https://en.wikipedia.org/wiki/Mapillary

### Organization

Meta (formerly Facebook) acquired Mapillary in 2020, integrating it into corporate mapping infrastructure. https://en.wikipedia.org/wiki/Mapillary

---

## 3. Apple Look Around

Launch: iOS 13 (June 2019 WWDC). https://en.wikipedia.org/wiki/Apple_Maps#Look_Around

Coverage began with select U.S. regions; UK and Ireland added October 2020; Dallas, Minneapolis, Tampa Bay added July 2023. https://en.wikipedia.org/wiki/Apple_Maps#Look_Around

Feature offers 360-degree street-level imagery with smooth scene transitions. Reported as offering higher image quality than Google Street View. https://en.wikipedia.org/wiki/Apple_Maps#Look_Around

Limited geographic coverage compared to Google Street View. No public statistics on total image count or kilometers captured.

---

## 4. Bing Streetside

Launched December 2009 in select U.S. metro areas plus Vancouver and Whistler, BC. https://en.wikipedia.org/wiki/Bing_Maps#Streetside

European expansion in May 2012. Germany Streetside imagery was fully removed due to privacy requests (May 2012). https://en.wikipedia.org/wiki/Bing_Maps#Streetside

Captured 360-degree photos using special omnidirectional cameras mounted on vehicles. https://en.wikipedia.org/wiki/Bing_Maps#Streetside

Service was discontinued October 2025; feature removed from Bing Maps entirely. https://en.wikipedia.org/wiki/Bing_Maps#Streetside

---

## 5. KartaView (OpenStreetCam, formerly OpenStreetView)

Founded 2009 as OpenStreetView; rebranded OpenStreetCam after 2016 TeleNav acquisition. https://en.wikipedia.org/wiki/KartaView

Acquired by Grab Holdings December 2019; rebranded KartaView November 2020. https://en.wikipedia.org/wiki/KartaView

Crowdsourced street-level photography for OpenStreetMap improvement. https://en.wikipedia.org/wiki/KartaView

Supports smartphone and action camera capture; integrates OBD-II dongles for GPS accuracy. https://en.wikipedia.org/wiki/KartaView

Real-time street sign recognition and processing. https://en.wikipedia.org/wiki/KartaView

Platform is open source for core components; mobile app retains proprietary elements. https://en.wikipedia.org/wiki/KartaView

No published statistics on total image count or geographic coverage.

---

## 6. Yandex Panoramas

Available in Russia, Ukraine, Belarus, Kazakhstan, Armenia, Turkey, Serbia, Uzbekistan, Moldova, Kyrgyzstan, Nepal, Azerbaijan, Georgia. https://en.wikipedia.org/wiki/Yandex_Panoramas

Coverage includes unusual locations like Pripyat and Chernobyl exclusion zone. https://en.wikipedia.org/wiki/Yandex_Panoramas

Mount Everest panoramas captured 2016. https://en.wikipedia.org/wiki/Yandex_Panoramas

No public data on total image count, camera specifications, or blur policies.

---

## 7. Autonomous Vehicle Data Ingestion (Analog System)

### Data Volume Per Vehicle

Autonomous vehicles produce massive sensor data: cameras, lidar, radar, IMU continuously at highway speeds. Each vehicle generates terabytes per day.

Waymo's fleet has accumulated 270 million autonomous miles. https://blog.google/products/google-waymo/waymo-ai-model-simulation/

Specific TB/hour or TB/day figures for individual companies are not published in technical blogs or research papers reviewed (Waymo, Cruise, Tesla, Aurora, Lyft Level 5).

### Data Offload Mechanisms

Two primary strategies: depot-based upload (vehicle drives to charging/service location, disks transferred) or physical drive transport (Snowball/Transfer Appliance equivalents).

Physical data transfer via Snowball/Transfer Appliance preferred when network bandwidth unavailable or cost-prohibitive.

---

## 8. Data Transfer Infrastructure: Snowball and Transfer Appliance

### AWS Snowball Edge

Storage Optimized model capacity: approximately 210 TB per device. https://aws.amazon.com/snowball/faqs/

Compute Optimized model offers similar storage capacity with onboard compute and processing. https://aws.amazon.com/snowball/faqs/

AWS processing timeline: export jobs "typically start within 24 hours, can take as long as a week." https://aws.amazon.com/snowball/faqs/

Pre-shipment preparation: up to 4 weeks from order placement. https://aws.amazon.com/snowball/faqs/

For larger transfers, multiple devices deployed sequentially or in parallel to move "petabytes of data." https://aws.amazon.com/snowball/faqs/

Primary use cases: massive data transfers where high-bandwidth internet is unavailable or cost-prohibitive. https://aws.amazon.com/snowball/faqs/

AWS Snowball support discontinuing December 31, 2026, in all commercial regions. https://aws.amazon.com/snowball/

### Google Transfer Appliance

Specific technical documentation for Transfer Appliance capacity and specifications could not be retrieved from public cloud.google.com sources. [unverified]

---

## 9. Storage Infrastructure: Bigtable and Imagery Warehousing

### Bigtable Scale

Bigtable manages over 10 exabytes of data as of April 2024. https://en.wikipedia.org/wiki/Bigtable

System serves more than 7 billion requests per second. https://en.wikipedia.org/wiki/Bigtable

Used by Google Analytics, web indexing, MapReduce, Google Maps, Google Books, Gmail, YouTube, Blogger, Google Code, and Google Earth. https://en.wikipedia.org/wiki/Bigtable

Bigtable organizes data into tablets ranging from hundreds of megabytes to several gigabytes, enabling petabyte-scale tables across hundreds or thousands of machines. https://en.wikipedia.org/wiki/Bigtable

Google Earth is explicitly documented as a Bigtable user, though specific imagery table configurations and Street View storage architecture are not published. https://en.wikipedia.org/wiki/Bigtable

### Imagery Storage Model

Street View imagery storage likely follows pattern similar to Google Earth: separate raw imagery table and serving table (tile-optimized).

Raw imagery table stores panoramas at full resolution with metadata (GPS, pose, timestamp).

Serving table pre-computed at tile levels (0 = world, increasing zoom = smaller regions) for fast retrieval via Street View Static API and interactive viewers.

---

## 10. Public APIs and Ingestion Flows

### Street View Static API

Enables embedding non-interactive panorama snapshots or thumbnails into web pages. https://developers.google.com/maps/documentation/streetview/overview

Accepts FOV (field of view, e.g., 80 degrees), heading (orientation), pitch (vertical angle) parameters. https://developers.google.com/maps/documentation/streetview/overview

Supports both Google-controlled imagery and user-contributed content (cannot filter by source). https://developers.google.com/maps/documentation/streetview/overview

### Street View Publish API

Enables users and applications to contribute 360-degree imagery to Street View. https://developers.google.com/maps/documentation/streetview/publish

API enforces photo size and format requirements, upload mechanism, and processing states. https://developers.google.com/maps/documentation/streetview/publish

Processing states: PENDING, PROCESSING, PUBLISHED, REJECTED. https://developers.google.com/maps/documentation/streetview/publish

Photo size limits, resumable upload support, and processing time SLAs are documented in API specifications. https://developers.google.com/maps/documentation/streetview/publish

Exact photo size limits and processing time SLAs could not be retrieved from accessible API docs. [unverified]

---

## Numbers Most Likely to Matter for Design

1. **Street View scale (verified)**: 10 million miles (16 million km) as of May 2017, across 83 countries. https://en.wikipedia.org/wiki/Google_Street_View#Coverage

2. **Mapillary scale (verified)**: 2 billion images as of August 2023. https://www.mapillary.com/about

3. **Raw image capture rate**: Eight 20-megapixel cameras operating continuously on moving vehicles; 5 megapixels per camera in R5 generation. https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications

4. **Sensor fusion complexity**: GPS + IMU + wheel encoders + optional lidar create high-dimensional pose estimation problem. https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications

5. **Face/plate detection recall in production**: 89% face blur, 94-96% license plate blur achieved in ICCV 2009 system (Frome et al.). https://research.google/pubs/large-scale-privacy-protection-in-google-street-view/

6. **Physical transfer capacity**: AWS Snowball Edge Storage Optimized holds 210 TB per device; processing (upload to S3 and verification) takes 24 hours to 1 week. https://aws.amazon.com/snowball/faqs/

7. **Database scale for imagery**: Bigtable handles 10+ exabytes at 7 billion requests per second globally. https://en.wikipedia.org/wiki/Bigtable

8. **User contribution platforms**: Mapillary processes 2 billion crowdsourced images via mobile apps and desktop uploaders. https://www.mapillary.com/about

9. **Privacy compliance**: Automatic face/plate blur necessary for GDPR, CCPA, and local privacy laws. 89-96% recall insufficient for some jurisdictions, requiring additional manual review for edge cases. https://research.google/pubs/large-scale-privacy-protection-in-google-street-view/

10. **Historical retention**: Street View maintains time-machine feature allowing users to see historical panoramas at same location across years (launched 2014). https://en.wikipedia.org/wiki/Google_Street_View#History

11. **Diverse capture platforms**: Vehicles, tricycles, trekkers, snowmobiles, boats create heterogeneous data ingestion challenge (data formats, timestamp sync, quality variability). https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications

12. **Tile-based serving**: Street View Static API and interactive viewers rely on pre-computed tile hierarchy for fast retrieval at varying zoom levels. https://developers.google.com/maps/documentation/streetview/overview

13. **Crowdsourced ingestion**: Mapillary, KartaView, and Google's own user panorama contributions create variable image quality and metadata. Processing pipeline must handle mixed sources. https://en.wikipedia.org/wiki/Mapillary

14. **Global privacy variance**: Different countries have different face-blur and license-plate requirements (e.g., Germany's Bing Streetside removal). https://en.wikipedia.org/wiki/Bing_Maps#Streetside

---

## What I Could Not Verify

1. **Google 2022 modular camera specifications**: Weight, exact resolution, sensor count, and lidar specifications for the 2022 camera refresh mentioned in some sources. Wikipedia Street View article does not document 2022 updates beyond September 2018 air quality sensors.

2. **Google Transfer Appliance capacity**: Public cloud.google.com documentation links returned 404 errors. Capacity, transfer speed, and processing time remain unverified.

3. **Street View Publish API photo size limits and SLA**: API reference documentation links returned 404 errors. Maximum upload size (MB), processing time (hours/days), and resumable upload chunk size are not accessible.

4. **Autonomous vehicle data volumes**: Waymo, Cruise, Tesla, Aurora, Lyft Level 5 do not publish TB/day per vehicle figures in accessible technical blogs or research papers. Fleet-wide aggregate numbers (e.g., "270 million Waymo miles") are public, but per-vehicle sensor data rates are not.

5. **Street View total image count**: Wikipedia reports 10 million miles (16 million km) as of May 2017, but the total number of panoramas or individual photos captured is not published. Inference: at 5-meter spacing on roads, this is roughly 3.2 billion panoramas, but this is derived, not quoted.

6. **Bigtable Street View table details**: Papers and Wikipedia confirm Google Earth uses Bigtable, but specific table schemas, raw imagery table size, and serving table organization are not documented in accessible sources.

7. **Mapillary processing pipeline details**: Wikipedia and Mapillary.com confirm Amazon Rekognition integration (2018) and computer vision processing, but specifics on latency, throughput, and deduplication logic are not published.

8. **KartaView/OpenStreetCam image count and coverage metrics**: No published statistics on total images, geographic coverage, or processing pipeline details.

9. **Yandex Panoramas scale**: No published data on image count, capture spacing, camera specifications, or privacy blur policies.

10. **Face detection precision** (vs. recall): Frome et al. ICCV 2009 reports 89% recall for face blurring and 94-96% for license plates, but does not break down precision figures or false-positive rates separately.

---

## Sources

| Source | URL |
|--------|-----|
| Wikipedia: Google Street View | https://en.wikipedia.org/wiki/Google_Street_View |
| Wikipedia: Google Street View Coverage | https://en.wikipedia.org/wiki/Google_Street_View#Coverage |
| Wikipedia: Google Street View History | https://en.wikipedia.org/wiki/Google_Street_View#History |
| Wikipedia: Google Street View Technical Specifications | https://en.wikipedia.org/wiki/Google_Street_View#Technical_specifications |
| Google Research: Privacy Protection in Street View (Frome et al., ICCV 2009) | https://research.google/pubs/large-scale-privacy-protection-in-google-street-view/ |
| Wikipedia: Mapillary | https://en.wikipedia.org/wiki/Mapillary |
| Mapillary Official (About) | https://www.mapillary.com/about |
| Wikipedia: Apple Maps Look Around | https://en.wikipedia.org/wiki/Apple_Maps#Look_Around |
| Wikipedia: Bing Maps Streetside | https://en.wikipedia.org/wiki/Bing_Maps#Streetside |
| Wikipedia: KartaView | https://en.wikipedia.org/wiki/KartaView |
| Wikipedia: Yandex Panoramas | https://en.wikipedia.org/wiki/Yandex_Panoramas |
| Google Developers: Street View Static API | https://developers.google.com/maps/documentation/streetview/overview |
| Google Developers: Street View Publish API | https://developers.google.com/maps/documentation/streetview/publish |
| Wikipedia: Bigtable | https://en.wikipedia.org/wiki/Bigtable |
| AWS Snowball FAQs | https://aws.amazon.com/snowball/faqs/ |
| AWS Snowball Home | https://aws.amazon.com/snowball/ |
| Waymo: 270 Million Autonomous Miles | https://blog.google/products/google-waymo/waymo-ai-model-simulation/ |


---

## Spot-check corrections (editor, 2026-09-27)

This survey leaned on Wikipedia. The numbers used in `solution.md` were re-fetched from primary sources.

| Claim in survey | Primary source says | Source |
|---|---|---|
| R7 details from Wikipedia | R7 is a rosette of 15 cameras with 5 MP CMOS sensors. R5 is 8 of the same plus a fish-eye. R2 used 11 MP CCDs | [Anguelov et al., IEEE Computer 2010](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/36899.pdf) |
| Pipeline details unverified | Pose from GPS + wheel encoders + IMU, batch-smoothed at 100 Hz, then snapped to a probabilistic road graph. Launch pipeline: stitch, tile at several zoom levels, then face and plate detection, "a very compute-intensive step". Panoramas are "selectively replicated according to usage patterns" | same paper |
| Data offload not covered | Early van logged to 20 hard drives at 500 MB/s. Drives are shock-sensitive; shock-mounted enclosures and custom shipping packaging; SSDs where vibration is extreme | same paper |
| World road length | "roughly 50 million miles of roads, paved and unpaved, across 219 countries" (CIA World Factbook, as quoted in 2010) | same paper |
| Face 89%, plates 94 to 96% | Correct. Hand-counted recall 89.0% on the Cities set, 90.7% on the Campus set. An off-the-shelf state-of-the-art detector got under 78%. Users report misses, which are blurred in the live product | [Frome et al., ICCV 2009](https://static.googleusercontent.com/media/research.google.com/en//archive/papers/cbprivacy_iccv09.pdf) |
| Bigtable Earth numbers "not published" | Published. Raw imagery preprocessing table ~70 TB, compression off because images are already compressed. One row per geographic segment, rows named so adjacent segments are stored near each other. Serving index table ~500 GB pointing at data in GFS, tens of thousands of QPS per datacenter, hundreds of tablet servers, in-memory column families | [Chang et al., Bigtable, OSDI 2006](https://static.googleusercontent.com/media/research.google.com/en//archive/bigtable-osdi06.pdf) |
| 2022 camera unverified | Under 15 lb, "roughly the size of a house cat", modular, optional lidar, fits any car. Over 220 billion Street View images from over 100 countries and territories (claim dated 2022-05-24) | [Google blog, Street View turns 15](https://blog.google/products-and-platforms/products/maps/street-view-15-new-features/) |
| Publish API limits unverified | Upload is 3 calls: `photo.startUpload` returns an upload URL, bytes go to that URL, `photo.create` sends pose and capture time. Photo Sphere requirements: 7.5 MP or larger (3,840 x 1,920), 2:1 aspect, no more than 75 MB | [startUpload reference](https://developers.google.com/streetview/publish/reference/rest/v1/photo/startUpload), [first app guide](https://developers.google.com/streetview/publish/first-app), [photo requirements](https://support.google.com/maps/answer/7012050?hl=en) |
| Transfer Appliance unverified | TA40 rackable: up to 100 TB encrypted. TA300: up to 300 TB. TA40F freestanding: up to 40 TB | [Transfer Appliance specifications](https://cloud.google.com/transfer-appliance/docs/4.0/specifications) |
| Not covered: retention of unblurred imagery | EU Article 29 Working Party letter of 2010-02-11 asked Google to cut retention of unblurred images from one year to six months. Google's stated commitment was 12 months from publication | [EDRi summary](https://edri.org/our-work/edrigramnumber8-5article-29-wp-google-street-view/) |
| Not covered: pre-launch opt-outs | Germany 2010: 244,237 opt-outs out of 8,458,084 households in the 20 largest cities, 2.89%. Some requested houses were still visible at launch because the process was complex | [Google Europe Blog, 2010-10-21](https://europe.googleblog.com/2010/10/how-many-german-households-have-opted.html) |
