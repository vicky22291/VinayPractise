# Integrating Entra ID, Azure DevOps and Databricks for Better Security in CI/CD

- Source: https://www.databricks.com/blog/integrating-entra-id-azure-devops-and-databricks-better-security-cicd
- Published: 2024-09-11
- Authors: Erik Baumert, Nicole Jingting Lu
- Categories: engineering, data-science-machine-learning
- Images: 5 total, 0 extracted as architecture

Personal Access Tokens (PATs) are a convenient way to access services like Azure Databricks or Azure DevOps without logging in with your password. Today, many customers use Azure DevOps PAT tokens as Git credentials for remote repositories in Databricks Git folders (formerly Repos). Unfortunately, the use of PAT tokens comes with some downsides. In Azure DevOps, PAT tokens cannot be issued to service principals and managed identities, which means that customers resort to a service account or even a user’s identity. Additionally, the maximum lifespan of PAT tokens is often days, weeks, or even months. While their rotation (the process of refreshing the tokens such that older ones can no longer be used) can be [governed](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/manage-pats-with-policies-for-administrators?view=azure-devops#set-maximum-lifespan-for-new-pats), this means that a leaked token with a long lifespan may pose a significant risk. A more secure alternative is to access Azure DevOps resources using a Microsoft Entra ID (formerly Azure Active Directory) access token.

 

From the Microsoft Docs: 

*As PATs are simply bearer tokens, meaning token strings that represent a user’s username and password, they're incredibly risky to use as they can easily fall into the wrong person’s hands. Microsoft Entra tokens expire every hour […], which limits the overall risk factor when leaked.[*[*1*](https://learn.microsoft.com/en-us/azure/devops/integrate/get-started/authentication/service-principal-managed-identity?view=azure-devops#q-why-should-i-use-a-service-principal-or-a-managed-identity-instead-of-a-pat)*] *When considering access to the Azure DevOps Git repositories linked to your Databricks Git folders, you no longer need to rely on PATs. Now, you can use Microsoft Entra ID access tokens, which have tighter controls around token rotation and expiry.

In this blog, we will learn how to use an Entra ID access token as a Git credential in Databricks Git folders to strengthen the security posture when pulling repositories hosted in Azure DevOps.

 

### Prerequisites | Create Service Principal

To start, you need a managed identity or service principal. If you do not have one, follow this document: [Register a Microsoft Entra app and create a service principal](https://learn.microsoft.com/en-us/entra/identity-platform/howto-create-service-principal-portal#prerequisites). At the end of it, you will have a service principal you can use. Note that in this scenario no redirect URI is required, so you can leave that form element blank. Make sure to create a secret and note it down, together with the service principal ID. (The following steps show how you use a service principal as the mechanism for authentication, but the same steps also apply to a managed identity.)

This process assumes that you have an Azure DevOps project set up with a Git repository you would like to link to a Databricks Git folder.

 

### Step 1 | Grant your service principal Reader permissions in your project

UnderAzure DevOps **Project settings** > **Permissions** > **Readers** add your service principal. 

Ensure the access level is sufficient for the required operation under **Organization settings** > **Users**.

### Step 2 | Grant service principal required permissions in Databricks

If you use Unity Catalog, open another browser tab and go to your Databricks account console, and then add the service principal to your account. 

Now, generate an OAuth secret to authenticate against the Databricks API (using the CLI) and copy it down somewhere secure.

Finally, grant the service principal user permissions on your workspace. 

### Step 3 | Use the CLI to create Entra ID Token and store it in Databricks Git credential

You’ll use the Azure and Databricks CLI for this step. To authenticate against Databricks, you need a [configuration profile](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/profiles) (.databrickscfg) configured with the OAuth token we just created, your workspace URL, and a service principal ID. Your update to  .databrickscfg should look something like this:

To log the service principal with the AzureCLI we use the secret we have created earlier. The script requests an Entra ID access token scoped to Azure DevOps (indicated by the UUID 499b84ac-1321-427f-aa17-267ca6975798), then configures a Git credential with the Databricks CLI and uses it to set up our new Git folder: 

 

### Summary | What’s next?

You’ve now learned how to generate Microsoft Entra ID access tokens scoped to Azure DevOps and then store them as a Databricks Git credential instead of as a DevOps PAT token. As the MS Entra ID access token is short-lived, your pipeline must update the Git credential using Databricks git-credentials update, and can then trigger a pull by calling Databricks repos update. As this process just showcases the credential setup, additional security measures are usually required in a production setting, like storing the service principal client secret and the Databricks OAuth token in a secure secret store like Azure Key Vault.

See [Use Azure Key Vault secrets in Azure Pipelines](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/azure-key-vault?view=azure-devops&tabs=yaml) and [Secret scopes](https://learn.microsoft.com/en-us/azure/databricks/security/secrets/secret-scopes#--create-an-azure-key-vault-backed-secret-scope) for further details.
