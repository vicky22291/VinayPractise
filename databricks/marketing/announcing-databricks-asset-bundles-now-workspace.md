# Announcing Declarative Automation Bundles now in the Workspace

*Collaborate, version, and deploy with Git folders—no CLI required*

- Source: https://www.databricks.com/blog/announcing-databricks-asset-bundles-now-workspace
- Published: 2025-06-13
- Authors: Fabian Jakobs, Lennart Kats, Saad Ansari
- Categories: engineering
- Images: 2 total, 0 extracted as architecture

**Key takeaways**

- Declarative Automation Bundles in the workspace allows teams to collaboratively build, version-control, and deploy projects from Git folders within the workspace UI.
- Work with structured, source-controlled projects without needing the CLI. Supports modular development, Git integration, and multi-environment deployments.
- Enables analysts, data scientists, and engineers to contribute to production workflows with a clear deploy step and built-in CI/CD readiness.

Today, we’re introducing the Public Preview of Declarative Automation Bundles in the workspace. This will make it easier for data scientists, analysts, and data or AI engineers to work interactively in the workspace with best practices such as version control, testing, and CI/CD. Team members can collaborate directly using Git folders in the workspace UI and don't need to use a CLI.

## Familiar Tools, Working Together

Managing structure, version control, and safe deployment are key to any reliable data engineering workflow. [Declarative Automation Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/) make this easier by letting you define jobs, pipelines, notebooks, and configurations as code—deployable across environments and ready for CI/CD integration.

Thousands of data engineering teams already use bundles to productionize their workflows, apply best practices, and collaborate through Git. But one consistent request stood out:

*"Can I use this directly in the workspace, without needing the CLI or VS Code?"*

Today, we’re delivering on that request.

This update extends tools that many teams already know: **the workspace, Git folders,** and **asset bundles**. Now, you can develop and deploy bundles entirely within Databricks: just open a Git folder, define your bundle, and deploy it with a click. The clear **Deploy** step ensures that promoting changes from dev to production is intentional, whether triggered by a workspace user or through CI/CD.

In total, you can:

- **Clone a Git repo** containing a bundle into your workspace
- Create bundles from a **pre-defined templates**
- Define jobs and pipelines in the **UI**
- Click **Deploy** to apply changes
- Manage deployments in the **visual panel**
- **Commit** changes back to Git

This streamlines the development process within Git folders. It brings structure to how work progresses from development to production, aligning with standard software practices and making the process accessible to a broader range of users.

## Instant Feedback, No Sync Needed

When working in a Git folder, users can iterate quickly on uncommitted changes. Development jobs, pipelines, and other resources defined in the bundle automatically reference the latest files — no manual sync needed. This behavior is powered by `source_linked_deployment`, which is enabled by default in [development mode](https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes#development-mode) enabling faster iteration and feedback.

## Looking Ahead

We’re continuing to improve the experience. Future updates will:

- Support importing existing jobs and pipelines into bundles
- Integrate bundle authoring more deeply with Lakeflow pipeline development
- Improve parameter handling and deployment visibility

Whether you're building data pipelines, training models, or creating dashboards, asset bundles in Git folders offer a collaborative and structured path to move from idea to production — all from within the Databricks workspace.

## How to Get Started

- Navigate to a **Git Folder** in the workspace
- Click **Create → Asset Bundle**
- Use a **template** to scaffold your project
- Click **Deploy** to apply changes to your environment
- Use the **Deployments panel** (🚀) to view, manage, or roll back deployments

Alternatively you can clone an existing repo with existing bundles or examples such as [https://github.com/databricks/bundle-examples](https://github.com/databricks/bundle-examples).

**Note:** Make sure the preview is enabled for use (see below)

Learn more: [documentation](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace).
