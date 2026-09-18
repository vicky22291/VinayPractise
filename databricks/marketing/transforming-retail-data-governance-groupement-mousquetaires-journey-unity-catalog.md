# Transforming Retail Data Governance: Groupement Mousquetaires' Journey with Unity Catalog

- Source: https://www.databricks.com/blog/transforming-retail-data-governance-groupement-mousquetaires-journey-unity-catalog
- Published: 2025-05-05
- Authors: Yannick BURLURAUX
- Categories: platform, announcements, engineering, open-source, industries, energy, data-strategy, industry-insights, company, news
- Images: 0 total, 0 extracted as architecture

**Key takeaways**

- Groupement Mousquetaires, supported by its IT arm La Stime, adopted Unity Catalog within Databricks to centralize data governance, streamline access, and improve compliance across a highly decentralized environment with 700+ workspaces.
- By standardizing data architecture, engaging Databricks Professional Services, and empowering cross-functional squads with a clear migration playbook, they ensured a smooth and efficient rollout of Unity Catalog.
- Unity Catalog has enabled secure, collaborative, and agile data operations, positioning Groupement Mousquetaires for smarter decisions, innovation, and long-term growth across its diverse retail brands.

With more than 4,300 stores across France, Belgium, Portugal, and Poland, Groupement Mousquetaires is one of France’s leading retail groups, with a diverse portfolio that includes grocery chains, home improvement stores, and automotive service centers.

La Stime, our Information Systems Department, is critical in supporting every step of the customer journey—from store operations and logistics to supplier performance. Within La Stime, the DataLab team drives our data strategy and implementation, turning information into actionable insights that inform key business decisions.

As early adopters of data-driven decision-making, we launched our centralized DataHub in 2019. This initiative aimed to unify customer data into a 360° view, enable cross-brand research and development, and power smarter operations and decisions.

At the core of DataHub is Databricks. Its comprehensive Data + AI Platform has strengthened data governance across our evolving ecosystem. With Unity Catalog, our teams can now unlock the full value of our data, driving revenue and innovation.

## The challenges of decentralized data

Before adopting Unity Catalog, we faced significant challenges managing data at scale. With nearly 700 Databricks workspaces, our complex environment required manual management of user access and permissions in each workspace—a time-consuming process that was unsustainable in the long run.

This decentralized approach made it difficult to offer self-service access to trusted “gold data” without sacrificing oversight or slowing teams down. Finding the right data, applying consistent security policies, and enabling cross-team collaboration became increasingly difficult. Without a unified governance framework, data usage varied widely and was hard to control.

Complying with data protection standards, like Règlement Général sur la Protection (RGPD)—the French equivalent of the GDPR—was particularly challenging during development and testing, where the lack of centralized controls introduced compliance risks.

Although we had already adopted Unity Catalog for new data products, we quickly realized that migrating our existing workloads was essential. It felt like a massive undertaking, but it promised to streamline access, improve governance and position us for sustainable growth.

## Rebuilding data governance with a trusted partnership

In retail, timing is everything. Think about it — targeted promotions, inventory updates, social media marketing trends and customer sentiment. Everything can change in the blink of an eye. That’s why retailers need reliable, accessible data. Ultimately, this necessity drove us to rethink how we manage and govern data across Groupement Mousquetaires’ family of brands.

We started by taking stock of where we were—a deep dive into our existing architecture. With hundreds of Databricks workspaces in use across brands, countries and teams, our data landscape became increasingly complex and difficult to oversee and manage. From our store operators and supply chain analysts to our e-commerce team, everyone needed access to data. Yet, getting that access securely and consistently was a major roadblock.

## Standardizing the foundation and building the plan

So, we went back to the basics. Once we mapped our current architecture and used that to define a set of standards, including how data would be named for catalogs, schemas and tables, we were able to structure and share it. Next, we partnered closely with Databricks’ Professional Services team to design a technical strategy for migrating our data and bringing our most critical data products into Unity Catalog.

From there, our IT team led an internal initiative to update all ingestion and processing pipelines, ensuring data was published directly into Unity Catalog—creating a single, reliable entry point for access.

Our business squads—comprising data engineers, DevOps, and product owners—took ownership of migrating the data products they managed. With clear guidance and support from IT, each squad’s migration became a trackable milestone in a larger rollout campaign.

## Pilots, playbooks and progress

To ensure success, we ran three pilot migrations while keeping in close collaboration with our Databricks Delivery Solutions Architect. Their deep expertise helped us set critical benchmarks and best practices for our teams. We also connected with other large organizations undertaking similar migrations, exchanging insights that helped us refine our approach.

From these early efforts, we built a practical, no-fluff migration playbook. It became the backbone of our planning sessions, helping squads prioritize their efforts with the broader roadmap in mind. Together with the Databricks team—including Field Engineering experts—we developed a strategic rollout plan that focused on technical readiness and prioritized active development pipelines where integration would be most impactful.

To reduce risk, we avoided coupling migrations with critical business initiatives. Most importantly, we deprioritized any data products likely to be phased out within six months.

Thanks to this collaborative, methodical approach, we streamlined migrations and scaled more efficiently than we could have on our own. With a strong foundation, clear business value from early wins, and continued alignment across teams, we’re now on track to reach 100% Unity Catalog adoption across all Databricks workloads by 2025.

## The Results of better data unity and governance

Adopting Unity Catalog has fundamentally transformed data governance at Groupement Mousquetaires. We've created a centralized, secure, and collaborative data environment that empowers smarter, faster decision-making across the business. But for us, Unity Catalog is more than just a governance tool—it’s a strategic enabler. It unlocks seamless data sharing, enhances operational agility, and lays the groundwork for future data monetization.

Looking ahead, we see this as a critical differentiator in the European retail landscape—one that will help us evolve each brand into a more data-driven, responsive, and competitive force.
