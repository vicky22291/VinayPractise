# Operationalizing AI for public sector fraud prevention

- Source: https://www.databricks.com/blog/operationalizing-ai-public-sector-fraud-prevention
- Published: 2026-04-28
- Authors: Johnathan Tafoya, Kacey Hertan
- Categories: platform, solutions, engineering, data-science-machine-learning, databricks-ai, industries, public-sector, data-strategy, best-practices
- Images: 9 total, 0 extracted as architecture

**Key takeaways**

- Why AI-powered fraud is growing fast — and why government agencies need a smarter, scalable way to catch it
- How clean data, smart automation, and real-time insights team up to spot and investigate fraud risks
- What it takes to bring AI into everyday workflows to make faster, clearer, better decisions

## Operationalizing AI for public sector fraud prevention

Public sector agencies are at a pivotal crossroads. Governments are embracing artificial intelligence (AI) not only to modernize core operations and improve citizen services. At the same time, the rise of AI is also reshaping the threat landscape. Criminals now deploy synthetic identities, deepfake-enhanced documentation and hyper-personalized social engineering campaigns are forcing agencies to rethink legacy risk controls that were never designed for this scale or sophistication. For example:

- **Benefits:** Fraud offenses have [increased 242%](https://www.ussc.gov/research/quick-facts/government-benefits-fraud) since 2020.
- **Taxes:** There was [$4.5 billion](https://www.irs.gov/newsroom/irs-ci-issues-fiscal-year-2025-annual-report-showcasing-banner-investigative-results) in tax fraud uncovered in 2025 (up 111.8% YoY)
- **Patents:** single foreign actor was tied to [over 52,000](https://www.uspto.gov/about-us/news-updates/uspto-has-terminated-more-52000-fraudulently-filed-trademark-applications-and) fraudulent trademark filings

AI holds enormous promise, but only when grounded in trusted data and strong governance. Modernization isn’t about a single model; it’s about building a secure, end-to-end system that connects data, intelligence and workflows. This blog illustrates how to modernize fraud prevention with Databricks through a fictional agency called the Services Bureau.

## A New Operating Model for Fraud Investigation

Before exploring how this modernization works, it helps to understand how fraud investigations often happen today at the Services Bureau. Analysts must jump between multiple systems to gather the data needed for a single case. They export files from one system, download spreadsheets from another and receive additional information through email attachments or shared folders. They then combine those sources manually, running macros or rules to flag suspicious rows and performing deeper searches in other systems to validate the findings. The process is time consuming, fragmented and difficult to scale.

Now imagine a modern workflow where a single application visualizes 17 prioritized cases, each with supporting evidence and clear explanations tied to policies or fraud signals. AI surfaces the most urgent risks, while the analyst makes the final call. What once took weeks can now be done in a day, allowing them to move faster and with greater confidence.

## Embedding Intelligence into Operational Workflows with Databricks Apps

Data and insights deliver the most value when embedded directly into daily workflows.

Using [Databricks Apps](https://www.databricks.com/product/databricks-apps)powered by [Lakebase](https://www.databricks.com/product/lakebase), the Services Bureau brings governance, agents and dashboards into a single fraud operations application tailored to its mission.

A senior fraud analyst logs into the application and sees assigned cases. When opening a case, the analyst can review supporting documents stored in Unity Catalog volumes and third-party verification data.

Meanwhile, an embedded agent evaluates the case in the background and provides recommendations with supporting rationale.

Case detail view with embedded agent recommendation panel.

If the analyst agrees, they can approve the case. If not, they can override the recommendation and escalate it for investigation. Human judgment remains central.

Executives use the same application to view dashboards and interact with Genie without logging into multiple tools. Leadership and analysts operate within a unified environment that connects governance, intelligence and action.

[*Embedded executive dashboard and Genie interface within the app.*](https://www.databricks.com/sites/default/files/inline-images/embeded-executive-dashboard.gif)

This is what operationalized AI looks like in practice. Insights are not isolated in analytics platforms. They are embedded into mission workflows where decisions are made.

Teams can process far more cases with the same workforce, all while reducing the likelihood that suspicious activity slips through the cracks. Investigators gain visibility into patterns across programs and leadership gains confidence that every flagged activity is being evaluated systematically and consistently.

## Governed Data and Secure Collaboration with Unity Catalog + Delta Sharing

The fictional Services Bureau processes grants, contracts, benefits, tax returns and patents, which requires strong governance. Thousands of applications stream in daily through external systems and land in Delta tables within the lakehouse. Machine learning models and business rules flag suspicious cases for fraud analysts across the country.

Within [Unity Catalog](https://www.databricks.com/product/unity-catalog), the agency manages its fraud investigation tables with attribute-based access control (ABAC). Sensitive columns such as Personally Identifiable Information (PII) are governed by tags that automatically enforce masking policies for specific user groups.

For example, junior fraud analysts can view case details needed for review but never see masked PII fields. Senior analysts and approved investigators can access additional context based on role and policy.

*Unity Catalog table view showing governed tags and masked PII columns for a junior analyst role.*

Governance extends beyond access controls. Full lineage is available at the table and column level. Analysts and compliance teams can see exactly where a data element originated and where it flows downstream. If a regulator asks where a field came from, the answer is available in seconds.

[*Column-level lineage graph within Unity Catalog.*](https://www.databricks.com/sites/default/files/inline-images/column-level-lineage.gif)

## Coordinating Intelligence with Agent Bricks

Once data is governed and accessible, the next challenge is prioritization. Executives need to understand risk trends. Fraud leaders must align operational decisions with policy guidance and emerging external threats.

The Services Bureau uses [Agent Bricks](https://www.databricks.com/product/artificial-intelligence/agent-bricks), a multi-agent supervisor, to coordinate three capabilities:

- **Genie:** Pulls live stats within a workspace that queries data in the lakehouse.
- **Knowledge Assistant:** Adds procedures with an agent grounded in agency policies.
- **Web:** Brings trends via an external Model Context Protocol (MCP) server that scans for emerging fraud patterns.

Within the Databricks Data + AI Platform, Agent Bricks is configured by defining its role and specifying which agents it can orchestrate. From there, executives can ask natural language questions such as: ***“As of December 1st, what should we prioritize next? Where are our top risk areas and how are we performing?”***

[*Agent Bricks configuration panel showing connected agents.*](https://www.databricks.com/sites/default/files/inline-images/agent-bricks-configuration-panel_0.gif)

Behind the scenes, Agent Bricks calls Genie to run SQL queries against live fraud tables. It invokes the knowledge agent to surface relevant policy citations with direct references to source documents, then retrieves external signals about emerging fraud schemes.

The supervisor synthesizes these inputs into a clear response with recommended actions and supporting reasoning.

[*Agent response includes citations and external references.*](https://www.databricks.com/sites/default/files/inline-images/agent-response.gif)

This is not a generic LLM response. It is AI grounded in enterprise data, aligned to policy and enriched with real-time context. The agent recommends where the Fraud Investigation Unit should spend its time in the next 24–48 hours, armed with the context that they are currently in a “critical” backlog situation of nearly 53,000 cases.

For executives, this means actionable guidance delivered in plain language. And for operational teams, it means faster alignment around risk.

Feedback loops are built-in. Through labeling sessions, users can rate responses and provide guidance to refine outputs over time.

[*Labeling session interface for agent feedback.*](https://www.databricks.com/sites/default/files/inline-images/labeling-session-interface-for-agent-feedback.gif)

This approach brings AI into production as a coordinated system rather than a standalone model.

Equally important is AI governance. Every recommendation produced by the agent is grounded in traceable data sources, policy references and documented reasoning. Analysts remain in the loop and can review the supporting evidence before accepting or overriding the recommendation. This transparency helps agencies maintain trust in AI-assisted decisions while ensuring compliance with regulatory and oversight requirements.

## Turning Questions into Actionable Insight with AI/BI Genie

Operational leaders also need visibility into workload distribution and performance metrics.

Within an executive dashboard built on [AI/BI Genie](https://www.databricks.com/product/business-intelligence/ai-bi-genie), the Services Bureau tracks key performance indicators across its fraud program. The interface is interactive. Selecting an individual examiner automatically updates related charts to reveal workload, overdue cases and case mix.

[*Executive dashboard with interactive filtering applied to a single examiner, Jennifer.*](https://www.databricks.com/sites/default/files/inline-images/Executive-dashboard-with-interactive-filtering.gif)

Suppose leadership notices that senior examiners are carrying a disproportionate share of overdue cases. To investigate further, they can ask Genie directly: ***“What is the breakdown of cases by examiner level?”***

Genie generates the SQL query against the gold fraud table, returns a structured table and produces a visualization automatically. The SQL remains visible for transparency and validation.

[*Genie response showing generated SQL and accompanying visualization.*](https://www.databricks.com/sites/default/files/inline-images/genie-response-showing-generated-sql.gif)

With this insight, leadership can rebalance workloads or accelerate training for junior examiners. Analysts and executives alike can move from question to evidence without waiting on technical teams.

AI/BI Genie transforms analytics from static reporting into conversational, transparent and actionable intelligence.

## Conclusion

Modern public sector agencies cannot afford fragmented systems where data governance lives in one tool, analytics in another and operational workflows somewhere else entirely.

By unifying data, AI and governance within the Databricks platform, agencies can build secure foundations, coordinate intelligent agents and embed insights directly into mission-critical applications.

With models being built on trusted, context-aware data:

- Fraud detection becomes faster.
- Collaboration becomes more secure.
- Decisions become more transparent and defensible.

To learn how your agency can modernize fraud prevention and other mission critical programs, [connect with our public sector team](https://www.databricks.com/company/contact?itm_source=www&amp%3Bitm_category=solutions&amp%3Bitm_page=public-sector&amp%3Bitm_location=body&amp%3Bitm_component=large-header&amp%3Bitm_offer=contact).
