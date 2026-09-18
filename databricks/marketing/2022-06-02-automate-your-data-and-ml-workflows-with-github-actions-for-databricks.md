# Automate Your Data and ML Workflows With GitHub Actions for Databricks

- Source: https://www.databricks.com/blog/2022/06/02/automate-your-data-and-ml-workflows-with-github-actions-for-databricks.html
- Published: 2022-06-02
- Authors: Ahmed Bilal, Sid Murching, Mohamad Arabi, Xiangrui Meng
- Categories: engineering
- Images: 0 total, 0 extracted as architecture

As demand for data and machine learning (ML) applications grows, businesses are adopting continuous integration and deployment practices to ensure they can deploy reliable data and AI workflows at scale. Today we are announcing the first set of [GitHub Actions for Databricks](https://docs.databricks.com/dev-tools/ci-cd/ci-cd-github.html), which make it easy to automate the testing and deployment of data and ML workflows from your preferred CI/CD provider. For example, you can run integration tests on pull requests, or you can run an ML training pipeline on pushes to main. By automating your workflows, you can improve developer productivity, accelerate deployment and create more value for your end-users and organization.

## GitHub Actions for Databricks simplify CI/CD workflows

Today, teams spend significant time setting up CI/CD pipelines for their data and AI workloads. Crafting these CI/CD pipelines can be a painstaking process and requires stitching together multiple APIs, creating custom plugins, and then maintaining these plugins. GitHub Actions for Databricks are first-party actions that provide a simple and easy way to run Databricks notebooks from GitHub Actions workflows. With the release of these actions, you can now easily create and manage automation workflows for Databricks.

## What can you do with GitHub Actions for Databricks?

We are launching two new GitHub Actions in the [GitHub marketplace](https://github.com/marketplace?query=databricks+publisher%3Adatabricks+) that will help data engineers and scientists run notebooks directly from GitHub.

You can use the actions to run notebooks from your repo in a variety of ways. For example, you can use them to perform the following tasks:

- Run a notebook on Databricks from the current repo and await its completion
- Run a notebook using library dependencies in the current repo and on PyPI
- Run an existing notebook in the Databricks Workspace
- Run notebooks against different workspaces - for example, run a notebook against a staging workspace and then run it against a production workspace
- Run multiple notebooks in series, including passing the output of a notebook as the input to another notebook

Below is an example of how to use the newly introduced action to run a notebook in Databricks from GitHub Actions workflows.

## Get started with the GitHub Actions for Databricks

Ready to get started or try it out for yourself? You can read more about GitHub Actions for Databricks and how to use them in our documentation: [Continuous integration and delivery on Databricks using GitHub Actions](https://docs.databricks.com/dev-tools/ci-cd/ci-cd-github.html).
