# Building a soccer coaching app on Databricks

*Coach's Corner turns 51 million rows of match tracking data into a sub-second 2D/3D bench app for coaches, spanning the entire Databricks platform from Lakeflow ingestion to Genie scouting and agentic opponent dossiers.*

- Source: https://www.databricks.com/blog/building-soccer-coaching-app-databricks
- Published: 2026-07-17
- Authors: Samwel Emmanuel, Sheridan Harris, Andrew Helmreich, Kush Patel, Nick Ragonese
- Categories: platform, solutions, engineering, solution-accelerators, industries, media-and-entertainment, data-strategy, industry-insights, company, customers
- Images: 4 total, 0 extracted as architecture

**Key takeaways**

- Coach’s Corner is a Databricks App that turns 25 fps match tracking data into a sub-second 2D/3D tactical bench with replays, event analytics, a scout chat, and an opponent-dossier agent.
- It runs on one platform, powered by Databricks end-to-end. Lakeflow pipelines refine 51 million rows through bronze, silver, and gold, DBSQL queries them in 1 to 3 seconds, and Lakebase serves them to the app in milliseconds.
- The AI layer is grounded in the same governed data, including a Genie space to answer scouting questions, Vector Search to find similar players, and an agentic dossier that calls an LLM served through the Unity AI Gateway, with every step traced in MLflow.

Tracking data is now the richest signal in sport, but the real gap is turning the data into something a coach can actually use.

A modern match is captured at 25 frames per second (fps) from 19 separate feeds: every player, the ball, and every event, many times a second. For one tournament, that is 339 matches and 51 million rows of tracking data. Yet almost none of it is usable by the person who needs it most. A coach on the bench cannot read a 51-million-row table. Coach's Corner closes that gap, entirely on one platform.

The challenge is not just scale, but timing and cognition. Coaches make decisions in seconds, not minutes, and traditional analytics workflows assume the opposite: batch processing, offline dashboards, and post-match review. Even when insights exist, they are buried behind tooling that requires an analyst to interpret and relay them. This creates a structural bottleneck in which the data is rich, and the models are sophisticated, but the decision-maker is effectively blind at the moment that matters.

## Meet Coach’s Corner, “La Pizarra”

La Pizarra (“the chalkboard”) is a national-team technical bench that runs as a Databricks App. A coach picks a match and replays it in 2D or 3D, swinging the camera from a broadcast angle to a top-down tactical view and scrubbing at up to 8x speed. Layered on the replay are the analytics that matter: shot and xG maps, pass networks, heatmaps, set pieces, team shape, pitch control, ball trails, and player paths. Integrated with the replay features are several advanced tools: a comprehensive standings view, event-driven analytics, a unique Scout style-signature for evaluating any team, and a Tactical Agent capable of generating on-demand dossiers for upcoming opponents.

The bench view places the entire match in the coach's hands, enabling seamless transitions between broadcast and tactical top-down perspectives. With 8x scrubbing and automated overlays for passing lanes and heatmaps, tactical elements like pitch control and team shape become tangible patterns on the field rather than distant metrics.

The technical foundation of Coach's Corner was dictated by a single guiding principle: the interface had to function as an extension of a coach's natural instinct rather than a complex analytical instrument. This required a design that reduced interaction overhead, favored spatial context over traditional graphing, and presented every metric as a dynamic element of the game. By anchoring insights directly to the field of play, the application eliminates the need for manual data interpretation and delivers critical analytics precisely when they are most relevant.

## One platform, every hop

The core data engineering happens under the hood. Raw tracking feeds land as NDJSON in a Unity Catalog Volume, where Auto Loader ingests them incrementally using the Lakeflow Connect pattern. From there, Spark Declarative Pipelines process the data through bronze, silver, and gold tiers, running entirely serverless on Photon with 46 named data quality expectations enforced. The final gold tables, including a 51-million-row frame table, leverage liquid clustering to enable 1-3-second query response times via DBSQL running on a small warehouse. By consolidating all volumes, tables, models, and indexes into a single Unity Catalog, the architecture eliminates vendor glue code and secondary governance systems.

The architecture deliberately avoided fragmentation by resisting the shift toward specialized microservices. Rather than splitting ingestion, transformation, serving, and AI orchestration into isolated, locally optimized stacks, the system stayed unified on a single platform. Keeping everything inside Databricks traded some theoretical flexibility for operational coherence: a single governance layer, consistent lineage, and no impedance mismatch between systems. This becomes especially important when AI is introduced, because the cost of ungoverned or inconsistent data compounds quickly.

Spark Declarative Pipelines redefine reliability by shifting from an imperative model to an explicit one. Instead of relying on rigid jobs with embedded assumptions, the system treats data quality as a first-class concern by enforcing formal expectations. This suite of 46 expectations serves a dual purpose: it safeguards the pipeline in real-time and establishes data “correctness” for downstream consumers, including replay, analytics, and AI agents..

The diagram below is the architecture powering the bench view. At the top sit the experiences a coach touches: replay, analysis, scout, standings, and agents. In the middle, each of those experiences is backed by governed layers: Unity Catalog for data and models, Lakehouse and Lakebase for analytical and transactional serving, and Vector Search for similarity. At the bottom sits the raw reality it all starts from: 25 fps tracking feeds, match events, player profiles, and lineups, all landing into an open lake.

## Optimized serving paths for speed and scale

To ensure peak performance, the application utilizes two distinct architectural paths for data retrieval. High-speed tracking replays are powered by Lakebase, which synchronizes gold tables to Postgres to enable millisecond-level windowed frame reads. By allowing the browser clock to pull only essential frames rather than scanning entire matches, the system maintains a fluid interactive experience. Conversely, heavy event analytics are routed through the Statement Execution API to the SQL warehouse, keeping intensive computational queries separate from the responsive 3D replay.

This deliberate bifurcation between Lakebase and DBSQL addresses differing access patterns rather than just raw speed. Replay functions demand sequential, latency-sensitive reads over specific data segments, whereas analytical workloads are often exploratory and require broad dataset scans. By isolating these paths, each workload operates within its ideal environment, preventing analytical spikes from degrading the replay experience or requiring unnecessary overprovisioning.

The separation between Lakebase and DBSQL is not just about performance, but about access patterns. Replay workloads are highly sequential and latency sensitive, requiring predictable millisecond reads over narrow slices of data. Analytical queries, on the other hand, are bursty and exploratory, often scanning larger portions of the dataset. Trying to unify these into a single serving layer would either slow down replay or overprovision analytics. Splitting the paths allows each workload to operate in its ideal environment without compromise.

## An AI scouting layer, grounded in governed data

Intelligence sits on the same governed data, never beside it. The Scout chat is backed by a real Genie space that converts a coach’s natural-language question into governed SQL. Vector Search powers “similar players” over a player profile index. The opponent dossier is an agent: an Agent Bricks supervisor orchestrates Genie, Vector Search, and a Unity Catalog registered xG model, and calls Claude on Model Serving through the Unity AI Gateway for governed, observable LLM calls. Every step is traced in MLflow, and the agent always has a deterministic scripted fallback, so it never dead ends in front of an audience. Because it reads the same catalog the coach sees on the board, the answers stay consistent with the data.

In the scout view below, the coach is not writing queries; they are asking questions the way they would in the locker room. Genie takes “Ask about xG vs xBA” and quietly turns it into governed SQL, using the same tracking and event data that powers the bench. The answer is not a generic LLM response; it is grounded in the exact tables and models registered in Unity Catalog, so the scout’s narrative matches the numbers the analyst would see.

One of the hardest problems in applied AI is not generating answers, but ensuring they are traceable and defensible. In a coaching context, a wrong or unverifiable insight is worse than no insight at all. By grounding every AI interaction in Unity Catalog and routing all model calls through the Unity AI Gateway, every response is tied back to governed data and observable execution paths. This allows coaches and analysts to trust not just the output, but the process behind it.

The agent architecture also reflects a bias toward determinism. While the LLM provides synthesis and narrative, critical steps such as data retrieval, metric computation, and similarity search are handled by structured systems like Genie and Vector Search. This hybrid approach avoids the brittleness of fully generative systems while still enabling flexible, natural interaction.

## Why it matters

While Coach’s Corner is rooted in sports, its architecture addresses a universal challenge: the "usability gap" in high-frequency data. Most organizations possess massive data volumes that remain operationally silent because they lack a system to translate raw inputs into immediate decisions. This project proves that by unifying ingestion, transformation, and AI within a single governance framework, the friction between data and action is eliminated.

The implication is not just faster dashboards, but a shift in how decisions are made. When insights can be generated, validated, and delivered within the same system in seconds, the role of data evolves from retrospective analysis to active participation in decision-making. That is the difference between observing the game and influencing it.

The agents view below is that pattern fully expressed: starting from tracking data and match events, the supervisor agent pulls a team’s style signature, searches similar matches, calls an xG model, and then asks an LLM to synthesize all of it into a dossier. The coach does not see any of that orchestration; they see a button labeled “Generate dossier for Brazil,” a reasoning trace they can inspect if they want, and a saved report that becomes part of their game plan.

Initially conceived as a sports-focused application, Coach’s Corner has evolved into a definitive blueprint for modern data and AI systems within the live entertainment sector. By landing raw data once and refining it through dependable pipelines, the system ensures information is served via the optimal path for each specific workload. This process transforms raw inputs into governed, actionable intelligence available at the precise moment of decision. The primary takeaway from this initiative is clear: when data management, serving, and AI are unified on a single platform, insights are converted into immediate action.

Want to build something like this? Explore the Databricks Apps documentation to ship your own full-stack data app, see how Lakebase brings millisecond Postgres serving to the lakehouse, and learn how Genie and Agent Bricks add governed, natural language intelligence on top of your data, all under one Unity Catalog.
