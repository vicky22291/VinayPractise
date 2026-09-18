# Southern Company’s SCOUT: Completing the Storm Intelligence Story

- Source: https://www.databricks.com/blog/southern-companys-scout-completing-storm-intelligence-story
- Published: 2026-09-02
- Authors: David Boyd, Blake Moore, Salome Abekhe
- Categories: platform, product, engineering, data-engineering, industries, energy, data-strategy, industry-insights, company, customers
- Images: 1 total, 0 extracted as architecture

**Key takeaways**

- Southern Company completed its end-to-end storm intelligence strategy by adding SCOUT, a real-time storm operations application, to complement SPEAR and RAMP on the Databricks Data + AI Platform.
- SCOUT extends operational visibility beyond the control room by bringing outage, customer, terrain and crew-planning intelligence together into a single real-time restoration experience. The platform has been adopted by 1,139 employees, including more than 250 who used it during a single peak storm day in June.
- Built on a unified lakehouse with Unity Catalog, Delta Lake and collaborative notebooks to support analytics and application development, SCOUT combines near-real-time data ingestion with governed analytics. Databricks Genie Code also helped accelerate the development of the custom data pipelines behind views such as the restoration effort chart.

## Completing the storm intelligence story

[In an earlier post](https://www.databricks.com/blog/alabama-power-leverages-databricks-outage-and-storm-modeling), we explored how Southern Company used Databricks to power SPEAR, which helps teams anticipate storm impact before an event, and RAMP, which supports post-storm reliability analysis after restoration. Together, those applications strengthened planning before a storm and analysis after it. However, Southern Company still saw an opportunity to make real-time storm operations more broadly accessible during the event itself.

SCOUT closes that gap.

SCOUT is Southern Company’s real-time storm operations application, built on the same Databricks lakehouse foundation as SPEAR and RAMP. Its architecture combines [Delta Lake](https://www.databricks.com/product/lakehouse-storage)for resilient storage, [Databricks Lakehouse](https://www.databricks.com/product/data-lakehouse) warehouses for real-time application queries, [Unity Catalog](https://www.databricks.com/product/unity-catalog) for centralized governance and collaborative notebooks to support analytics and application development — giving dispatchers, storm center leadership and field teams a live, data-rich picture of outages across the system, large and small, so they can move faster, deploy smarter and communicate more effectively with customers.

In February, SCOUT earned the 2025 S.E.E. Industry Excellence Award for transforming the way outage information is accessed. By bringing outage, customer and reliability data into a single real-time platform, SCOUT provides a consistent source of truth for customer-facing and operational teams. The industry recognition highlights SCO's impact across Southern Company's operating businesses.

## Connecting every phase of the storm lifecycle

Southern Company's Power Delivery Data Analytics team treats data as a strategic asset. Better data leads to better decisions around reliability, customer satisfaction, power quality and operating costs.

Each application now serves a distinct purpose:

- **SPEAR** predicts where severe weather will impact the grid, helping crews and resources move into position before outages begin.
- **SCOUT** provides a live operational view of active outages, restoration progress and customer impact throughout the event.
- **RAMP** analyzes outage performance after the storm to improve reliability planning and future investments.

Instead of moving between legacy applications and manual workflows, employees now work from a unified cloud-based environment that delivers the right operational data when they need it. This cloud-first approach, supported by modern technology, also enables employees to securely access and act on data insights remotely using smartphones and tablets.

## Delivering real-time operational intelligence

Before SCOUT, Southern Company had already established outage management capabilities. But the richest operational picture was often concentrated with operators at DCC desks. At the same time, field and support teams had to move across multiple systems to piece together outage analytics, customer restoration times, feeder maps, driving directions and other situational context. During a fast-moving storm, that meant critical intelligence existed, but it was not synthesized into a single, mobile-friendly experience for everyone who needed it. SCOUT changes that by bringing those views together into a single application built on the Databricks Platform.

Today, SCOUT reads directly from curated data stored in the lakehouse, giving storm leaders near real-time visibility into:

- Active outages
- Customer impact
- Crew requirements
- Damage assessments
- Operational maps and charts
- Driving directions
- Historical outage insights and comments
- Customer ETR (estimated time to restore)

With this consolidated view, dispatchers and operations leaders can quickly answer critical questions such as:

- What is the estimated restoration time for this event?
- How will this outage affect overall system reliability?
- Should crews be reassigned to speed restoration?

SCOUT provides fast, mobile-friendly access to outage information across Southern Company's operating companies, helping teams make confident decisions under rapidly changing conditions.

SCOUT is used across Southern Company’s operating businesses, with approved users at Georgia Power, Alabama Power, Southern Company Services, Mississippi Power and Southern LINC. The platform has been adopted by 1,139 employees, including more than 250 who used it during a single peak storm day in June to support restoration operations.

## Matching the right crews to every outage

One of SCOUT's most valuable capabilities is its ability to incorporate accessibility and terrain intelligence into restoration planning.

For every outage, SCOUT identifies conditions such as:

- Rear-lot locations that require climbing crews instead of bucket trucks
- Mountainous or difficult terrain that limits vehicle access
- Equipment requirements based on location characteristics

This additional operational context helps dispatchers assign the right crew with the right equipment the first time, reducing unnecessary trips and accelerating ticket assignment and restoration.

SCOUT combines this intelligence with historical outage management capabilities, creating a hybrid restoration platform that improves both operational efficiency and worker safety.

## Improving collaboration and customer service

SCOUT also streamlines mutual assistance during large restoration efforts.

Using only an email address, dispatchers can send detailed incident worksheets directly to external crews, giving them immediate access to outage information before they arrive on site. The result is faster communication, fewer manual handoffs and visiting crews that operate with the same situational awareness as Southern Company employees.

The platform also improves customer support by bringing estimated restoration times (ETRs), outage details and customer information into one place. Combined with the forecasting capabilities of SPEAR and the reliability insights from RAMP, Southern Company can communicate proactively with customers, set more accurate restoration expectations and continuously improve service after each event.

> "SCOUT consolidates highly complex and disparate outage data sources into a single, live application, giving our teams fast access to a consistent and reliable view of restoration activity across the system. By pulling together operational, geospatial and customer-impact data within Databricks, we're able to process and deliver information at the speed and scale required to support real-time decision-making."—Shane Powell, Senior Director, Power Delivery Data & Analytics, Southern Company

## Building SCOUT on the Databricks Platform

Southern Company built SCOUT on a unified lakehouse that centralizes outage, customer, GIS, weather, terrain and operational data.

The architecture combines:

- [Delta Lake](https://docs.databricks.com/aws/en/delta) for resilient data storage
- [Databricks Lakehouse](https://www.databricks.com/product/data-lakehouse) warehouses for real-time application queries
- [Unity Catalog](https://www.databricks.com/product/unity-catalog) for centralized governance
- [Genie Code](https://www.databricks.com/product/genie/code)** **and collaborative notebooks for analytics, data pipeline development and application development

SCOUT queries a dedicated Databricks Lakehouse warehouse every minute, ensuring dispatchers always have access to the latest operational information.

Unity Catalog provides secure, governed access through service principals, allowing SCOUT to surface only the data required while maintaining centralized security controls.

That governed access model also makes the platform more operationally useful. Because of the outage, customer, GIS, weather, terrain and hierarchy data are unified in the lakehouse, Southern Company can reuse the same current, trusted foundation across SCOUT, analytics and ad hoc operational questions without first stitching together separate systems. The payoff is both speed and flexibility: when Southern Company needed to identify every customer operating a car wash, the transformers serving those facilities and related infrastructure details, the team completed the request in approximately two hours because the relevant data was already unified in the lakehouse.

## Looking ahead with AI-assisted dispatching and autonomous drones

Southern Company is exploring how AI could further improve restoration operations over time.

Rather than fully automating dispatch, the team is evaluating an AI assistant that recommends the best next assignment for an available crew based on:

- Current crew location
- Travel time
- Required equipment
- Specialized skills
- Work already completed
- Safety and fatigue policies

This approach keeps dispatchers in control while giving them AI-powered recommendations that improve restoration speed, efficiency and safety.

Southern Company is also exploring a partnership with Skydio, a U.S.-based leader in autonomous drone technology. By integrating Skydio’s autonomous drones with SCOUT and the Databricks Platform, Southern Company could establish a connected ecosystem where outage information is shared in near real time. This capability would enable drones to be remotely launched and autonomously navigate directly to affected assets, initiating patrols without manual intervention.

As a drone inspects a line, live video and imagery could stream into SCOUT, giving operators and engineers immediate situational awareness. Advanced AI capabilities could analyze the footage in real time to identify potential equipment damage, hazards or failure points, then deliver actionable insights to operations personnel. By providing field crews with a detailed understanding of site conditions before they arrive, this integrated solution has the potential to accelerate restoration efforts, improve safety and increase operational efficiency.

## A complete view of storm operations

With SPEAR, SCOUT and RAMP, Southern Company now has a complete view of the storm lifecycle.

- **Before a storm, **SPEAR forecasts impact and stages resources.
- **During the event, **SCOUT provides real-time operational intelligence that helps dispatchers deploy crews and communicate with customers.
- **After restoration,** RAMP measures performance and supports long-term reliability improvements.
- **For capital investment**, PRISM is an AI-enabled decision-support platform that helps identify system risks, prioritize capital investments and quantify the business value of reliability improvement initiatives.

Together, these applications demonstrate how a unified data foundation on the Databricks Platform can transform utility operations. By connecting every phase of the storm lifecycle, Southern Company is creating a scalable blueprint for modern, AI-ready grid operations.

[Build and deploy a quality AI agent system](https://www.databricks.com/product/artificial-intelligence)
