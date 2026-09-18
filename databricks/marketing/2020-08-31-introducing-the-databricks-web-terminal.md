# Introducing the Databricks Web Terminal

- Source: https://www.databricks.com/blog/2020/08/31/introducing-the-databricks-web-terminal.html
- Published: 2020-08-31
- Authors: Hossein Falaki, Kasey Uhlenhuth
- Categories: engineering, data-science-machine-learning
- Images: 3 total, 0 extracted as architecture

## Introduction

We're excited to introduce the **public preview** of the Databricks Web Terminal in the 3.25 platform release. Any user with "Can Attach To" cluster permissions can now use the Web Terminal to interactively run Bash commands on the driver node of their cluster.

The new Databricks web terminal provides a fully interactive shell that supports virtually all command-line programs. The terminal is not intended for running Apache Spark jobs; however, it is a convenient environment for installing native libraries, debugging package management issues, or simply editing a system file inside the container.

## Motivation

Running shell commands has been possible through %sh magic commands in Databricks Notebooks. In addition, in some environments, cluster creators can set up SSH keys at cluster launch time and SSH into the driver container of their cluster. Both these features had limitations for power users. The new web terminal feature is more convenient and powerful than both these existing methods and is now our recommended way of running shell commands on the driver.

We heard from our users that they want a highly interactive shell environment which supports any command-line tools, including popular editors such as Vim or Emacs. They asked for interactive terminal sessions to install arbitrary Linux packages or download files. These were not convenient or possible with %sh magic commands.

SSH would offer an interactive shell, but it is limited to a single user, whose keys are registered on the cluster. Many users share clusters and most of them want the convenience of the interactive shell. In addition, system administrators and security teams are not comfortable with opening the SSH port to their virtual private networks. The web terminal addresses all these limitations. As a user, you do not need to setup SSH keys to get an interactive terminal on a cluster.

## How to get started

Web terminal is in Public Preview ([AWS](https://docs.databricks.com/release-notes/release-types.html)|[Azure](https://docs.microsoft.com/en-us/azure/databricks/release-notes/release-types)) and disabled by default. Workspace admins can enable the feature ([AWS](https://docs.databricks.com/administration-guide/clusters/web-terminal.html?_gl=1*z1ovo2*_gcl_aw*R0NMLjE1OTIyNjY4NTEuRUFJYUlRb2JDaE1JdzhIZ25ZaUY2Z0lWV1ItdEJoMTBxUUxHRUFBWUFTQUFFZ0lkRl9EX0J3RQ)|[Azure](https://docs.microsoft.com/en-us/azure/databricks/administration-guide/clusters/web-terminal)) through the Advanced tab. After this step, users can launch web terminal sessions on any clusters running Databricks Runtime 7.0 or above if they have “Can Attach To” permission.

There are two ways to open a web terminal on a cluster. You can go to the Apps tab under a cluster’s details page and click on the web terminal button.

Or when inside a notebook, you can click on the Cluster dropdown menu and click the “Terminal” shortcut.

If you are launching a cluster and you wish to restrict web terminal access on your cluster, you can do so by setting DISABLE_WEB_TERMINAL=true environment variable. Also note that high concurrency clusters ([AWS](https://docs.databricks.com/clusters/configure.html#high-concurrency-clusters)|[Azure](https://docs.microsoft.com/en-us/azure/databricks/clusters/configure)) with table ACLs ([AWS](https://docs.databricks.com/delta/delta-utility.html#table-acls)|[Azure](https://docs.microsoft.com/en-us/azure/databricks/delta/delta-utility)) or credential passthrough ([AWS](https://docs.databricks.com/security/credential-passthrough/index.html#credential-passthrough)|[Azure](https://docs.microsoft.com/en-us/azure/databricks/clusters/web-terminal)) do not allow web terminal access.

Please see our user guide ([AWS](https://docs.databricks.com/clusters/web-terminal.html)|[Azure](https://docs.microsoft.com/en-us/azure/databricks/clusters/web-terminal)) for more details about using the web terminal on Databricks.

## Limitations & Future Plans

When a web terminal session is not actively in use for several minutes, it will time out which leads to a new Bash process being created. This can result in losing your active shell session. To avoid this, we recommend managing your sessions with tools like [tmux](https://man7.org/linux/man-pages/man1/tmux.1.html).

High concurrency clusters that have either table access control or credential passthrough enabled, do not support web terminal.

When a user logs out of Databricks or his/her permission is removed from a cluster, their active web terminal sessions are not terminated. Please refer to these security considerations ([AWS](https://docs.databricks.com/administration-guide/clusters/web-terminal.html#security-considerations)|[Azure](https://docs.microsoft.com/en-us/azure/databricks/administration-guide/clusters/web-terminal)) for more details. We are working on addressing these issues before the feature is generally available.
