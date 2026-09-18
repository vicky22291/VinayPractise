# How Daikin Applied Americas builds consistent data pipelines at scale with Genie Code

*Using reusable skills, medallion patterns and shared definitions to deliver consistent, production-ready pipelines faster.*

- Source: https://www.databricks.com/blog/how-daikin-applied-americas-builds-consistent-data-pipelines-scale-genie-code
- Published: 2026-06-24
- Authors: Trent Lezer, James VanGordon
- Categories: platform, solutions, engineering, solution-accelerators, industries, manufacturing, data-strategy, industry-insights, company, customers
- Images: 0 total, 0 extracted as architecture

**Key takeaways**

- Daikin Applied Americas redesigned its data engineering operating model to support growing enterprise analytics and AI demands.
- The team standardized pipeline development using reusable MECE skills, medallion architecture and shared business definitions.
- This approach enables faster delivery, greater consistency and scalability governance across teams.

## Agentic data engineering is changing how pipelines are built

Daikin Applied Americas (DAA) manufactures and services commercial HVAC systems across North America. That means managing large volumes of operational, manufacturing and service data across systems, from equipment telemetry and supply chain data to field service records.

The data team supports analytics and AI use cases across engineering, operations and customer service, all of which depend on reliable, well-structured pipelines.

As those demands grew, so did the pressure on the data team, including more pipelines, more use cases and more coordination across teams. To address this, the team defined a more structured operating model for how pipelines are designed, built and governed, and used [Databricks Genie Code](https://www.databricks.com/product/genie/code) to accelerate execution within that model.

The team leveraged Genie Code as an AI-assisted approach to data engineering. Working directly against governed data in [Unity Catalog](https://www.databricks.com/product/unity-catalog) can help plan and generate multi-step pipelines across the workflow. This allows engineers to move from an idea to a working pipeline much faster, without switching tools or manually stitching components together.

That speed fundamentally changed how the team worked. Pipelines that previously took days to prototype could be generated in minutes. Iteration cycles were shortened, and engineers spent less time writing boilerplate and more time refining logic and outcomes.

At the same time, operating in a large, shared data environment requires consistency. Pipelines must follow common architectural patterns, use shared definitions and behave predictably across teams.

Large language models introduce a structural challenge in this context. When teams rely on varied prompts or loosely defined instructions, the same request can yield inconsistent outputs and lead to architectural drift over time.

To address this, the DAA team focused on defining how AI should operate within a governed enterprise environment, rather than relying solely on prompt engineering.

As Trent Lezer, Sr. Director, Data & Analytics at Daikin Applied Americas, puts it: “Genie Code works best when treated like a junior engineer who works fast but must respect the same architectural constraints as everyone else, no special exemptions ‘because it’s AI.’”

## Scaling data engineering through reusable skills

Early usage of Genie Code followed a familiar pattern: long prompts that attempted to encode architecture rules, naming standards, transformation logic and documentation requirements in a single block of text.

This approach did not scale. Instructions varied across teams, prompts became difficult to maintain and similar tasks produced inconsistent outputs.

To address this, the team introduced a MECE (Mutually Exclusive, Collectively Exhaustive) skill framework. As Trent explains: “We implemented a MECE skill framework, each skill defines one coherent competency, skills are non-overlapping and the full set covers the entire lifecycle of data engineering work.”

Each skill defines a specific capability in the data engineering lifecycle. Together, the skills are non-overlapping and cover the full workflow. These skills include medallion architecture design, source readiness and grain definition, transformation patterns, canonical alignment and governance standards.

Instead of embedding rules inside prompts, the team structured the environment so Genie Code loads the appropriate skills at runtime and applies them during planning and execution. This shifts behavior from interpreting ad hoc instructions to operating within a defined execution model.

From a governance perspective, this also changes how standards are enforced. As James VanGordon, Solutions Architect at Databricks, notes: “The pattern I keep seeing with Genie Code is pretty simple: prompts get you started, but they are a bad place to enforce team standards. If the same rule matters more than once, it should live in the workspace as a skill, where Genie Code can actually use it.”

He also emphasizes embedding standards directly into the execution environment: “That is what makes this real instead of wishful thinking. The skills, Unity Catalog context and Genie Code are working in the same place. The guidance sits where the work is being created, not off to the side in a review process someone has to remember later.”

## Using the medallion architecture to guide pipeline development

The team also strengthened the role of the medallion architecture as both a governance and reasoning framework. Bronze, Silver and Gold layers already existed, but the shift was making them explicit decision boundaries during pipeline generation, not just storage tiers.

Bronze represents raw source truth. Silver represents cleaned and conformed data. Gold represents business-ready analytics.

To operationalize this structure, the team introduced checkpoints between layers. Before data advances, requirements such as source grain definition, join validation and data stability checks must be satisfied.

These checkpoints are enforced within the development workflow itself, not as downstream review steps. Genie Code operates within these constraints as pipelines are generated and modified.

This ensures consistency across teams while reducing the risk of architectural shortcuts during rapid development.

## Connecting pipelines to business concepts

A recurring challenge in enterprise data engineering is aligning technical models with business language.

At DAA, stakeholders think in terms of equipment, customers, service events and contracts, not tables, joins or transformations.

To address this, the team anchored pipeline design in stable business entities. Rather than starting with technical structures, engineers begin by identifying what the data represents and how it behaves over time.

This shift improves downstream efforts and reduces ambiguity when datasets are reused across domains.

Over time, Silver-layer models and Gold datasets become more consistent because they are grounded in shared business concepts rather than isolated technical decisions.

## What changed for the team

With this operating model in place and AI embedded, the team saw a clear shift in how work was executed.

Pipeline development accelerated, particularly during early exploration and iteration. Engineers spent less time writing boilerplate code and more time refining business logic.

Outputs also became more consistent across teams. Similar use cases followed similar structural patterns, improving maintainability and reuse.

Importantly, trust in generated outputs increased. Engineers spent less time validating structural correctness and could iterate more quickly.

### Standardizing decision-making within the development workflow

To make these gains repeatable, the team standardized key decisions within the development process.

Rather than relying on implicit knowledge, definitions were made explicit, including what qualifies as Bronze, Silver and Gold data, how source grain is defined, which transformation patterns are reusable and how business entities are represented. This structure was critical for scale. It ensures AI operates within a consistent framework across teams, even as use cases evolve.

## The payoff: what this unlocked at scale

The result of this operating model was not just faster pipelines. It was the ability to scale data engineering in a governed enterprise environment.

### Faster delivery with fewer corrections

Engineers spend less time fixing structurally incorrect pipelines and more time refining logic and business outcomes.

### Reduced architectural drift across teams

Consistent application of skills and governance checkpoints prevents divergence across teams working on similar data challenges.

### Stronger alignment between engineering and business

Grounding pipelines in business concepts improves clarity and reduces downstream rework.

### Scalable governance without manual overhead

Guardrails are embedded directly into the system, reducing reliance on manual enforcement.

### Increased trust in AI-generated outputs

Because defined skills and checkpoints constrain outputs, AI operates reliably within production workflows.

As Trent summarizes: “The goal isn’t to make AI follow more rules. It’s to make the right rules impossible to ignore.”

## Conclusion

At Daikin Applied Americas, combining a structured operating model with AI-assisted development allowed the data team to scale faster while maintaining consistency, clarity and control.

By defining how pipelines should be built and embedding those rules directly into the development environment, the team created a system in which speed and governance reinforce each other rather than compete.

**Learn more about **[**Genie Code**](https://www.databricks.com/product/genie/code)**.**
