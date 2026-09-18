# Admin Isolation on Shared Clusters

- Source: https://www.databricks.com/blog/admin-isolation-shared-clusters
- Published: 2022-10-10
- Authors: David Meyer, Joosua Santasalo
- Categories: engineering, security-and-trust
- Images: 4 total, 0 extracted as architecture

*This blog was co-authored by David Meyer, SVP Product Management at Databricks and Joosua Santasalo, a security researcher with Secureworks.*

 

At Databricks, we know the security of the data processed in our platform is essential to our customers. Our[Security & Trust Center](https://www.databricks.com/trust) chronicles investments in internal policies and processes (like vulnerability management and a secure SDLC) along with security features (like customer-managed keys and PrivateLink).

Some of our best security investments have been in our[bug bounty](https://hackerone.com/databricks) and relationship-building with security researchers. Working together, we uncover and remediate vulnerabilities or misconfigurations, improve documentation, and collaborate to make Databricks the best place to securely solve the world’s toughest data problems.

Today we would like to showcase how a bug bounty report can make a product better. We would like to thank [Joosua Santasalo](https://securecloud.blog/) for his constructive feedback, well-documented reports, and collaborative spirit while working on this coordinated blog and disclosure.

## **Intro**

Recently, Databricks received a report from security researcher Joosua Santasalo about a potential privilege escalation risk for Databricks admins when operating on “No Isolation Shared” access mode clusters, formerly known as “Standard” mode clusters ([AWS](https://docs.databricks.com/clusters/configure.html#cluster-mode) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/clusters/configure#cluster-mode) | [GCP](https://docs.gcp.databricks.com/clusters/configure.html#cluster-mode)). The reported issue does not affect any other cluster types that use Databricks' data access control features, such as Databricks SQL warehouses and either Shared or Single User access mode clusters, and — for users of the older in in the older Cluster UI — there is no impact to High Concurrency clusters with table access control (Table ACLs) or Credential Passthrough. 

Joosua’s finding allowed someone with a valid, authenticated, and non-privileged Databricks account to gain admin privileges within the boundary of the same workspace and the same organization. Exploitation of this issue required the admin to interact with the cluster in question. Databricks has not found evidence of such escalations occurring in practice.

We have previously recommended using the “No Isolation Shared” cluster mode only for single-user use cases or situations in which user isolation is not a strong requirement, such as small teams that share the same access. Joosua’s report presented opportunities to further harden the use of this cluster type. To this end, we are improving several things:

- We are notifying Databricks admins that still use “No Isolation Shared” clusters to recommend they switch to more secure alternatives. As mentioned before, Databricks SQL warehouses and clusters using Shared or Single User access modes are not affected, along with High Concurrency clusters with either table access control (Table ACLs) or Credential Passthrough.
- We recommend that Databricks admins either use “Single User” or “Shared” clusters when running notebooks or tasks, or enable the new Admin Protection feature ([AWS](https://docs.databricks.com/administration-guide/account-settings/no-isolation-shared.html), [Azure](https://learn.microsoft.com/azure/databricks/administration-guide/account-settings/no-isolation-shared), [GCP](https://docs.gcp.databricks.com/administration-guide/account-settings/no-isolation-shared.html)) for “No Isolation Shared” clusters from within their [Account Feature Enablement Settings](https://accounts.cloud.databricks.com/settings/feature-enablement).
- We are making a more secure cluster option the default, and we are deploying additional features to enable users to take on a more stringent security posture.
- We have updated our UI ([AWS](https://docs.databricks.com/clusters/cluster-ui-preview.html) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/clusters/create-cluster#--what-is-cluster-access-mode) | [GCP](https://docs.gcp.databricks.com/clusters/create-cluster.html#what-is-cluster-access-mode)), documentation on cluster types ([AWS](https://docs.databricks.com/clusters/configure.html#standard-clusters) | [Azure](https://learn.microsoft.com/azure/databricks/clusters/cluster-ui-preview) | [GCP](https://docs.gcp.databricks.com/clusters/cluster-ui-preview.html)) and [security best practices](https://www.databricks.com/trust#security-features) to make sure the security implications are clear

Below is the researcher’s description of his findings in his own words, followed by Databricks’ response and recommendations to customers. While the research described below was conducted and tested with Azure Databricks as example, the finding affects “No Isolation Shared” clusters on any other cloud provider. 

## **Researching Databrick Default Cluster Internals**

**by Joosua Santasalo**

A while back I was researching another avenue of attacks on Databricks. In that process I ended up with a “side quest” discovery; this discovery was a strange set of default behavior, which most of the organizations would end up using when they followed the default provisioning wizard and who would ever use the defaults. The finding was not specific to Azure as cloud provider, but was initially researched by me via Azure, as that is the platform I use most often for security research - In other words, this finding was related to the product, not to the cloud provider.

After disclosing these findings, I was introduced to Databricks security team, who made a very high impression on me. To this day I have not met a more proactive or knowledgeable product security team. We agreed on a ~90 days disclosure timeline to give adequate time for mitigations and changes to the product.

The attack enabled non-privileged users to gain full access of a privileged user to the Databricks workspace, by intercepting the control plane traffic of privileged users. Depending on the cluster use, the compromised access would contain various privileged permissions and items that were bound to the particular Databricks instance.

Before Databricks deployed mitigations you could simply use the following tcpdump and grep pattern to get tokens of more privileged users running on the same default cluster. 

⚠️ This pattern still works for any previously provisioned default (standard) clusters, luckily mitigations are available described below under “ Protection Flags “

Based on these findings Databricks made changes in three categories:

    

| **New Provisioning workflow** | The new provisioning workflow defaults to single user cluster which prevents the behavior highlighted described in ‘Attack’ |
|---|---|
| **UX changes and more secure defaults** | The former standard (default) cluster is now called “No isolation Shared” cluster. Documentation now discourages the use of the previously default cluster mode. To create the previously default cluster mode you have to deliberately remove a bunch of "guardrails" by confirming options in UX. |
| **Protection flags** | Perhaps the biggest change is to mitigate this malicious behavior in existing and new clusters. Enabling this flag will detect that there is an admin user interacting with the cluster, and shall thus prevent leakage of the API token on a shared channel with possibly malicious users interacting on the same cluster. |

Timeline of disclosure:

- June - Initial submission shortly after meeting with MSRC 
- July - September - Various comms and testing proposed mitigations 
- October - Mitigations deployed 

*Researcher credits/shout-out: Secureworks, MSRC & MS Adversary Tradecraft Group - Nixu, DataBlinc*

## **Databricks’ response and recommendations**

As Joosua pointed out, this finding affects your workspace if you use “No Isolation Shared” clusters and require strong isolation between admin and non-admin roles. As mentioned previously, Databricks SQL warehouses and Shared or Single User access mode clusters are not affected. If you are using the older cluster UI ([AWS](https://docs.databricks.com/clusters/configure.html#cluster-mode) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/clusters/configure#cluster-mode) | [GCP](https://docs.gcp.databricks.com/clusters/configure.html#cluster-mode)), there is no impact to High Concurrency clusters with table access control (Table ACLs) or Credential Passthrough. This research documents a method valid on “No Isolation Shared” access mode clusters where an authenticated user could obtain secrets of another user operating on the same cluster. This could potentially allow the non-privileged user to access privileges of another user on that cluster.

We want to explain why this issue is possible, what Databricks has done and is doing in response, and a few steps that customers may want to consider taking. The most important step is to move workloads **off of** No Isolation Shared clusters if possible.

- **Why is it possible?** No Isolation Shared clusters run arbitrary code from multiple users in the same shared environment by design, similarly to what happens on a cloud Virtual Machine shared across multiple users. Consequently, data or credentials provisioned to that environment may be accessible to any code running within that environment. In order to call Databricks APIs for normal operations, access tokens are provisioned on behalf of users to these clusters. When a higher-privileged user, such as a workspace administrator, runs commands on a cluster, their higher-privileged token will be visible in the same environment. As mentioned earlier, this finding affects “No Isolation Shared” clusters on any cloud provider.

 No Isolation Shared clusters are useful for cases in which all users share the same level of access (e.g., one cloud IAM role) and need a flexible environment to collaborate in. Under these conditions, with multiple users sharing the same level of access by choice, privilege escalation is not flagged as a risk and No Isolation Shared mode can be a strategic setup. However, when a stronger security boundary between regular users and administrators is required, Single User or Shared access modes offer more secure user isolation.
  

- **What are we doing?** We have created an account-wide security control for account administrators to enable Admin Protection for “No Isolation Shared” clusters from within their Account Feature Enablement Settings ([AWS](https://docs.databricks.com/administration-guide/account-settings/no-isolation-shared.html), [Azure](https://learn.microsoft.com/azure/databricks/administration-guide/account-settings/no-isolation-shared), [GCP](https://docs.gcp.databricks.com/administration-guide/account-settings/no-isolation-shared.html)). This opt-in setting will prevent admin credentials from being provisioned to No Isolation Shared clusters. We are also offering an additional “Enforce User Isolation" workspace flag ([AWS](https://docs.databricks.com/security/enforce-user-isolation.html), [Azure](https://learn.microsoft.com/en-us/azure/databricks/security/enforce-user-isolation), [GCP](https://docs.gcp.databricks.com/security/enforce-user-isolation.html)), which allows admins to disable “No Isolation Shared” clusters across a workspace.

 Finally, we’re helping our customers make informed choices by ensuring that our documentation, UI, and security best practices sufficiently explain the risks and tradeoffs.
  

- **What should our customers do?** We’ve enumerated best practices in the final section of this post, but in short: admins should use more secure cluster types, use only non-admin accounts on No Isolation Shared Clusters, and enable the new Admin Protection feature ([AWS](https://docs.databricks.com/administration-guide/account-settings/no-isolation-shared.html), [Azure](https://learn.microsoft.com/azure/databricks/administration-guide/account-settings/no-isolation-shared), [GCP](https://docs.gcp.databricks.com/administration-guide/account-settings/no-isolation-shared.html)) as a precaution.

## **Hardening your Databricks cluster**

Customers can increase the security for their Databricks deployments through the following recommendations. 

1. **Use cluster types that support user isolation wherever possible.** Customers commonly enforce user isolation and avoid these issues by using Databricks SQL warehouses, clusters with Shared or Single User access mode, or High Concurrency clusters with table access control (Table ACLs) or credential passthrough.
2. Enable **Admin Protection** ([AWS](https://docs.databricks.com/administration-guide/account-settings/no-isolation-shared.html), [Azure](https://learn.microsoft.com/azure/databricks/administration-guide/account-settings/no-isolation-shared), [GCP](https://docs.gcp.databricks.com/administration-guide/account-settings/no-isolation-shared.html)) for “No Isolation Shared” clusters from within [Account Feature Enablement Settings](https://accounts.cloud.databricks.com/settings/feature-enablement). This new setting will prevent admin credentials from being provisioned to “No Isolation Shared” clusters and it’s suggested for customers who can’t move to different cluster types in the short-term.
  
3. You can disallow No Isolation Shared clusters ([AWS](https://docs.databricks.com/administration-guide/clusters/policies.html#cluster-policy-examples), [Azure](https://learn.microsoft.com/en-us/azure/databricks/administration-guide/clusters/policies), [GCP](https://docs.gcp.databricks.com/administration-guide/clusters/policies.html)) from being created within a workspace or only allow a limited set of users to create No Isolation Shared clusters. You can use Cluster ACLs that control what users are able to attach notebooks to those clusters. Alternatively, the new "Enforce User Isolation" workspace flag ([AWS](https://docs.databricks.com/security/enforce-user-isolation.html), [Azure](https://learn.microsoft.com/en-us/azure/databricks/security/enforce-user-isolation), [GCP](https://docs.gcp.databricks.com/security/enforce-user-isolation.html)) will disable “No Isolation Clusters” for a specific workspace.
  
4. Users who need to administer the workspace should use separate, non-admin accounts for regular usage, and use admin accounts only for administrative activities.

## **User isolation clusters: conclusions and going forward**

To meet the evolving needs of our customers and data teams, Databricks has been gradually moving away from “No Isolation Shared” clusters. The release of Unity Catalog is part of the model we're working towards in which all users operate on secured clusters that enforce user isolation; Unity Catalog data simply cannot be accessed from No Isolation clusters by design, preventing any risk of misconfiguration errors. More and more users are configuring Shared access mode clusters or High Concurrency clusters with table access control (Table ACLs) (or Databricks SQL warehouses), which support improved security models designed to mitigate the class of issues reported by security researchers like Joosua.

Thank you again to Joosua Santasalo, and all of the security researchers who are working with us to make Databricks more secure every day. If you are a security researcher, we will see you at [hackerone.com/databricks](https://hackerone.com/databricks).
