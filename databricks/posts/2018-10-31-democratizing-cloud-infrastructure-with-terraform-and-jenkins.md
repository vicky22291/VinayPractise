# Democratizing Cloud Infrastructure with Terraform and Jenkins

- Source: https://www.databricks.com/blog/2018/10/31/democratizing-cloud-infrastructure-with-terraform-and-jenkins.html
- Published: 2018-10-31
- Authors: Ziheng Liao
- Categories: platform, solutions, engineering
- Images: 2 total, 0 extracted as architecture

*This blog post is part of our series of internal engineering blogs on the Databricks platform, infrastructure management, integration, tooling, monitoring, and provisioning.*

This summer at Databricks I designed and implemented a service for coordinating and deploying cloud provider infrastructure resources that significantly improved the velocity of operations on our self-managed cloud platform. The service is called the "Terraform Deploy Pipeline", and I worked with both the Cloud and Observability teams to make it possible.

In this blog, I explain how we enhanced the existing workflows that use Terraform, and addressed pain points to drastically reduce operational burden and the risk of mistakes. I will summarize its impact on engineering velocity, and my overall internship experience at Databricks.

## Introduction

At Databricks, engineers interact with various cloud providers' (i.e., AWS, Azure) managed resources on a daily basis. To ease provisioning, we leverage [Terraform](https://www.terraform.io/), a cloud agnostic, open source resource provisioning tool. Combined with Databricks’ [jsonnet-based templating system](https://www.databricks.com/blog/2017/06/26/declarative-infrastructure-jsonnet-templating-language.html), engineers can declaratively specify required resources, and provision those resources across multiple regions and cloud providers. One missing piece in achieving operational efficiency is deployment [orchestration](https://www.databricks.com/glossary/orchestration) of templates to provision their respective resources.

## Terraform: Infrastructure as Code

For readers not familiar with Terraform, we briefly describe how we use Terraform to manage cloud resources. In order to provision cloud infrastructure using Terraform, a user defines their resources in a template file, typically using JSON, or the [Hashicorp Configuration Language](https://github.com/hashicorp/hcl) (HCL) (a configuration language built by the creators of Terraform). An example JSON template to provision an Azure keyvault would look as follows:

When a template is applied by Terraform, an output tfstate file is generated. The [tfstate](https://www.terraform.io/docs/state/) file describes the current state of the cloud resources provisioned by the corresponding terraform template. Such files are critical for Terraform to perform subsequent resource updates on already deployed resources, since Terraform computes the diff of the desired state from the existing baseline state from the tfstate files, and performs updates accordingly to achieve a desired final state of cloud resources.

To change or destroy existing resources, the user simply changes the template and re-applies it using Terraform. If the corresponding tfstate file is present, Terraform will correctly modify the resources and generate a new tfstate file to replace the old one. If tfstate files are missing, Terraform will treat all the resources specified in the template as new. [State management](https://www.terraform.io/language/state/purpose) is a tricky piece to manage, but necessary for Terraform to efficiently migrate resources to the desired state. Unexpected application behaviors can occur when Terraform leverages with a tfstate file mismatched to the current cloud resource state.

## Existing Pain Points

Terraform is an incredibly powerful tool, and it has dramatically improved the efficiency of Databricks when leveraging cloud resources. However, managing thousands of templates and cloud resources across production environments brings many new challenges for Databricks engineering. Some of the most critical issues include:

1. **Operation bottlenecks for deploying production resources** - At Databricks, a limited number of people have privileged access to deploy resources into our production environment. For an engineer to deploy their resources, they need to make a request to the infrastructure team to approve the request and deploy the production change. This is even true for seemingly lightweight changes such as updating production database parameters. Completing the request could take hours or even days from the time of the initial engineering request.
2. **Lack of enforced tfstate consistency** - Databricks stores tfstate files in Git, which provides niceties such as version control (especially change tracking). However, since Git allows users to view code at different points in time by design, two users can be working with conflicting views of tfstate files. As the system scales, it becomes impossible to prevent users on different branches from deploying the same resource, overwriting existing resources, or entering inconsistent states.
3. **Lack of support for deploying resources with sensitive information** - An extremely common use case for Terraform at Databricks is deploying per-service databases. At deployment time, an initial set of credentials needs to be specified. If simply added to the template, the credentials would be visible in Git, both in the template and the materialized tfstate file, which is a clear breach of security. As a workaround, the templates contain placeholders for credentials, and tfstate files are sanitized by redacting credentials post-hoc. The placeholders are especially problematic, as engineers need to remember to manually remove the real credentials before committing.

## Terraform Deploy Pipeline: Resource Provisioning Made Simple and Secure

To address the problems mentioned in the previous section, we designed the Terraform Deploy Pipeline, a self-service resource provisioning tool. The pipeline is powered by Jenkins and presents a simple user interface to deploy Terraform templates:

Figure 1: The Terraform Deploy Pipeline UI.

To provision resources on the cloud, an engineer needs to construct a Terraform template, input the path as a parameter to the job, and deploy the job. The pipeline will resolve the template, leverage the respective cloud provider credentials, and apply the template using Terraform. To ensure that the deployment was intentional, the pipeline will pause briefly to display the proposed change of resources and prompt the user for confirmation. After confirming, the resources are deployed seamlessly!

Figure 2: An example diff showed when deploying a Terraform template (in this case, an Azure KeyVault).

If any resource targets a production environment, the pipeline enforces approval from our infrastructure team before it can proceed. Though intervention is still required for security purposes, the workflow is significantly simpler, since the infrastructure team only needs to approve the request and allow the pipeline to handle automated delivery. Alternatively, the pipeline supports two-person authorization for production resource changes that have gone through the code review process (which includes getting infrastructure team approval), and are merged into our master branch. In this case, the pipeline generates a link for the requesting engineer to send to another engineer for approval.

After the approver reviews and accepts the request, the pipeline proceeds and applies the Terraform templates. These workflows minimize the effort necessary to update production resources while preventing unauthorized deployment to production.

After the pipeline finishes applying the Terraform template, the generated tfstate file will be uploaded to a distributed tfstate service (backed by Azure blob store) instead of being committed to version control. This design ensures that tfstate files are consistent, and eliminates the risk of users applying Terraform templates from tfstates representing the state at different points in history.

## Deploying Secrets

To allow deploying cloud resources with sensitive credentials, we integrated the pipeline with our central credential management system backed by Hashicorp Vault. In a Terraform resource template, a user can specify a reference to the credentials needed to bootstrap the resource. At runtime, the pipeline will fetch the referenced credentials from Vault and seamlessly inject them into Terraform via runtime parameters. Credentials are passed between services without any manual user intervention. By leveraging credential injection and post-hoc tfstate redaction, users can safely provision cloud resources without worrying about leaking credentials.

## Conclusion

The Terraform Deploy Pipeline aims to improve efficiency and security of cloud resource provisioning at Databricks. It was released internally in August 2018 and has become the standard pipeline for resource deployment to Microsoft Azure ever since. We’ve seen a drastic reduction in the time taken to bootstrap new cloud resources, and increased adoption thanks to newly unlocked workflows. Typically, production resource provisioning tasks will now finish in minutes. Additionally, these workflows are now more secure thanks to credential injection.

My internship experience at Databricks was phenomenal. I’ve interned at multiple companies, and the Databricks’ internship was something different -- From the very beginning of the internship, I never felt like I was treated as an intern, but instead I was part of the team and the company. I was given the opportunity to have an impact and create value almost immediately. Databricks engineers were humble and supportive, always open to feedback despite having more industry experience. Most importantly, I've been able to grow and learn tremendously, both technically and non-technically, from a variety of experiences you wouldn't get at other companies: chatting 1-on-1 with co-founders, attending Spark and AI Summit, the biggest conference on Spark, listening to CEO re-present his board presentation, attending lunch sessions with VPs across the company, and shadowing the Databricks interview process.

Finally, I'd also like to thank everyone in the company, especially my teammates from the Cloud and Observability team, for being a part of my wonderful summer internship experience. It deeply informed my mindset when I approach designing and building scalable cloud infrastructure.

## Read More

Find out what our engineering interns have worked on:

- [Introducing Cluster-scoped Init Scripts](https://www.databricks.com/blog/2018/08/30/introducing-cluster-scoped-init-scripts.html)
- [Introducing mlflow-apps: A Repository of Sample Applications for MLflow](https://www.databricks.com/blog/2018/08/16/introducing-mlflow-apps-a-repository-of-sample-applications-for-mlflow.html)
- [Databricks Engineering Interns & Impact in Summer 2018](https://www.databricks.com/blog/2018/10/10/databricks-engineering-interns-impact-in-summer-2018.html)

Related internal engineering blog series:

- [Writing a Faster Jsonnet Compiler](https://www.databricks.com/blog/2018/10/12/writing-a-faster-jsonnet-compiler.html)
- [Declarative Infrastructure with the Jsonnet Templating Language](https://www.databricks.com/blog/2017/06/26/declarative-infrastructure-jsonnet-templating-language.html)
