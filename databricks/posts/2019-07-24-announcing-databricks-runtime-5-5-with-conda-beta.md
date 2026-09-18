# Announcing Databricks Runtime 5.5 with Conda (Beta)

- Source: https://www.databricks.com/blog/2019/07/24/announcing-databricks-runtime-5-5-with-conda-beta.html
- Published: 2019-07-24
- Authors: Yifan Cao
- Categories: company, product, engineering, data-science-machine-learning, platform, solutions
- Images: 0 total, 0 extracted as architecture

Databricks is pleased to announce the release of Databricks Runtime 5.5 with Conda (Beta).  We [introduced](https://www.databricks.com/blog/2019/06/04/introducing-databricks-runtime-5-4-with-conda-beta.html) Databricks Runtime 5.4 with Conda (Beta), with the goal of making Python library and environment management very easy.  This release includes several important improvements and bug fixes as noted in the latest release notes [[Azure](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.5conda)|[AWS](https://docs.databricks.com/release-notes/runtime/5.5conda.html)].  We recommend all users upgrade to take advantage of this new runtime release.  This blog post gives a brief overview of some of the new features on Databricks Runtime 5.5 with Conda (Beta).

### Major package upgrades

We upgraded a number of packages on Databricks Runtime with Conda (Beta) to match Anaconda Distribution 2019.03. Some of the major package upgrades include:

| **Package** | **Updated Version** |
|---|---|
| pandas | 0.24.2 |
| numpy | 1.16.2 |
| matplotlib | 3.0.3 |
| ipython | 7.4.0 |

To view a complete list of packages and their versions installed on Databricks Runtime with Conda, visit the release notes [[Azure](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/5.5conda)|[AWS](https://docs.databricks.com/release-notes/runtime/5.5conda.html)].

### Improved UX and Performance

In this release, we also improved user experience and performance of Databricks Runtime with Conda (Beta).

In Databricks Runtime 5.4 with Conda (beta), you can use Databricks Library Utilities [[Azure](https://docs.microsoft.com/en-us/azure/databricks/runtime/conda#notebook-scoped-libraries)|[AWS](https://docs.databricks.com/runtime/conda.html#notebook-scoped-libraries)] to create a Python environment scoped to a notebook session. This popular feature allows you to easily create an isolated environment with required libraries on a shared cluster. In Databricks Runtime 5.5 with Conda (beta), we have improved the isolation among environments scoped to notebook sessions, further mitigating library conflicts.

We added support for YAML files when using Databricks Library Utilities to customize Python environments. Databricks Runtime 5.4 with Conda (Beta) provided a way of using a requirements.txt file [[Azure](https://docs.microsoft.com/en-us/azure/databricks/runtime/conda#requirements-files)|[AWS](https://docs.databricks.com/runtime/conda.html#requirements-files)] to install a list of packages, with each package’s version specified. This helps you customize the environment without needing to installing packages one by one. In Databricks Runtime 5.5 with Conda (Beta), we have added support for installing packages using YAML files, the declarative file format used by Conda. For more details on how to install packages using YAML files, refer to the User Guide for Databricks Library Utilities [[Azure](https://docs.microsoft.com/en-us/azure/databricks/runtime/conda#notebook-scoped-libraries)|[AWS](https://docs.databricks.com/runtime/conda.html#notebook-scoped-libraries)].

We have made it easier to use `%sh conda install`. When you use `conda install` to install new packages on the driver node, you no longer need to pass the easily-forgotten `-y` flag.

To improve environment isolation between notebooks, process isolation and credential passthrough [[Azure](https://docs.microsoft.com/en-us/azure/databricks/security/credential-passthrough/adls-passthrough#enabling-azure-ad-credential-passthrough-to-adls)] is now enabled in Databricks Runtime 5.5 with Conda (Beta).  **Note: **Credential passthrough on AWS is in private preview.

Finally, we improved startup performance of notebook-scoped environments. Running the first command in a new notebook is now significantly faster.
