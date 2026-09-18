# Securely Accessing External Data Sources from Databricks for AWS

- Source: https://www.databricks.com/blog/2019/03/08/securely-accessing-external-data-sources-from-databricks-for-aws.html
- Published: 2019-03-08
- Authors: Itai Weiss
- Categories: product, engineering
- Images: 2 total, 2 extracted as architecture

Databricks Unified Analytics Platform, built by the original creators of Apache SparkTM, brings Data Engineers, Data Scientists and Business Analysts together with data on a single platform. It allows them to collaborate and create the next generation of innovative products and services. In order to create the analytics needed to power these next-gen products, Data Scientists and Engineers need access to various sources of data. Apart from data in the cloud block storage such as S3, this data that they need is often located on services such as databases or even come from streaming data sources located in disparate VPCs.

### Securely connecting to “non-S3” external Data Sources

For security purposes, Databricks Apache Spark clusters are deployed in an isolated VPC dedicated to Databricks within the customer's account. In order to run their data workloads, there is a need to have secure connectivity between the Databricks Spark Clusters and the above data sources.

It is straightforward for Databricks clusters located within the Databricks VPC to access data from AWS S3 which is not a VPC specific service. However, we need a different solution to access data from sources deployed in other VPCs such as AWS Redshift, RDS databases, streaming data from Kinesis or Kafka. This blog will walk you through some of the options you have available to access data from these sources securely and their cost considerations for deployments on AWS. In order to establish a secure connection to these data sources, we will have to configure the Databricks VPC with either one of the following two available options :

### Option 1: VPC Peering

A secure connection between the Databricks cluster and the other non-S3 external data sources can be established by using VPC peering. AWS defines VPC peering as “a networking connection between two VPCs that enables you to route traffic between them using private IPv4 addresses or IPv6 addresses”. For more details see AWS documentation [here](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html).

*A VPC peering link*

**Summary:** The diagram shows Databricks Spark clusters in one AWS VPC accessing database and Apache Kafka resources in a shared data VPC through AWS VPC peering.

**Components:**

- AWS account containing the Databricks VPC
- Databricks VPC
- Spark clusters
- Databricks security group
- AWS VPC peering
- AWS account containing the shared data VPC
- Shared data VPC
- Database resource
- Apache Kafka
- External security groups

**Flows:**

- Databricks VPC -> Shared data VPC: Private network traffic through AWS VPC peering
- Shared data VPC -> Databricks VPC: Private network traffic through AWS VPC peering
- Spark clusters -> Database resource: Data access
- Spark clusters -> Apache Kafka: Data access

**Numbers:** 10.126.0.0/16, 172.78.0.0/16

```mermaid
%% Databricks VPC access to shared data resources through AWS VPC peering
flowchart LR
    subgraph DA[AWS account]
        DV[Databricks VPC]
        SG1[Security group]
        SC[Spark clusters]
        DV --- SG1
        SG1 --- SC
    end

    P[AWS VPC peering]

    subgraph SA[AWS account]
        SV[Shared data VPC]
        DB[Database]
        K[Apache Kafka]
        SG2[Security groups]
        SV --- SG2
        SG2 --- DB
        SG2 --- K
    end

    DV <--> |Private network traffic| P
    P <--> |Private network traffic| SV
    SC --> |Data access| DB
    SC --> |Data access| K

    class DA,SA external
    class DV,SV service
    class SC service
    class DB store
    class K queue
    class SG1,SG2 critical
    class P service

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
``

<sub>source image: https://www.databricks.com/wp-content/uploads/2019/03/VPC-Page-1.png</sub>

A VPC peering link

When the VPC peering option is chosen, one has to take the following factors into consideration:

- VPC Peering is easier and more appropriate when there are several resources that should communicate between the peered VPCs . When there is a high degree of inter VPC communication, VPC peering would be the recommended option.
- The VPC hosting the other “non-S3 data sources” must have a [CIDR](https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing) range distinct from the CIDR range of the Databricks VPC or any other CIDR range included as a destination in the Databricks VPC’s main [route table](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html)
- VPC peering has scale limitations. Please check [AWS documentation](https://docs.aws.amazon.com/vpc/latest/peering/vpc-peering-basics.html#vpc-peering-limitations) for the latest.
- Pricing considerations:
  - Same region pricing: If the VPCs in the VPC peering connection are within the same region, the charges for transferring data over the VPC peering connection are the same as the charges for transferring data across Availability Zones.
  - Different regions pricing: If the VPCs are in different regions, inter-region data transfer costs apply.
  - For accurate and latest pricing, please refer [AWS documentation](https://aws.amazon.com/vpc/pricing/).

Here is an example of a situation where VPC peering option would be ideal - You are tasked with creating a data table that will pull the data from a Kafka cluster and store the aggregated results on Aurora database both located on the same VPC external to the Databricks VPC. Assuming no other security limitations, you can use VPC peering connection between the Databricks VPC and the external VPC where the data sources are located and then connect to both sources.

### Option 2: AWS Privatelink

The second option available to connect with the non-S3 data sources would be to use an AWS Privatelink. AWS defines [PrivateLink](https://aws.amazon.com/privatelink/) as a service that “provides private connectivity between VPCs, AWS services, and on-premises applications, securely on the Amazon network. AWS PrivateLink simplifies the security of data shared with cloud-based applications by eliminating the exposure of data to the public Internet.”

*AWS PrivateLink*

**Summary:** The diagram shows Databricks Spark clusters in a Databricks VPC accessing a shared data process through AWS PrivateLink within the same region.

**Components:**

- AWS Region
- Databricks VPC
- Databricks security group
- Spark clusters
- Shared Data VPC
- Apache Kafka process
- Shared data process
- Shared data security group
- AWS PrivateLink

**Flows:**

- Spark clusters -> Shared data process: PrivateLink data access

**Numbers:** none

```mermaid
%% Shows Databricks Spark clusters accessing shared data through AWS PrivateLink
flowchart LR
    subgraph AWSRegion[AWS Region]
        subgraph DatabricksVPC[Databricks VPC]
            Spark[Spark clusters]
            DBSG[Databricks security group]
        end

        subgraph SharedVPC[Shared Data VPC]
            Kafka[Apache Kafka process]
            Data[Shared data process]
            SharedSG[Shared data security group]
        end

        Spark -->|PrivateLink| Data
    end

    class Spark client
    class DBSG critical
    class Kafka queue
    class Data store
    class SharedSG critical
    class AWSRegion,DatabricksVPC,SharedVPC external

    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2019/03/VPC-Page-2.png</sub>

AWS PrivateLink

One has to take the following considerations into account while choosing the Privatelink option:

- Privatelinks are overall easier to setup and more suited for VPC relationships that have the following security requirements:
  - Each Privatelink will connect only to one single service
  - It is easy to find out which services/ports are open to the Databricks service
  - Each service accessed can be controlled separately
- AWS Privatelink supports overlapping CIDR ranges by applying source [NAT](https://en.wikipedia.org/wiki/Network_address_translation) from the consumer to the provider of the AWS Privatelink
- Although, AWS Privatelink can scale to thousands of consumers per VPC,  at any time only one Privatelink can be configured
- AWS Privatelink only allows the data consumer to originate connections to the data provider. If bidirectional communication is needed, VPC Peering or a reciprocal AWS Privatelink between the consumer and provider may be required.
- AWS Privatelink inherits the design consideration of Network Load Balancers ([NLB](https://en.wikipedia.org/wiki/Network_Load_Balancing)). For example, NLBs only support TCP and connections from the consumer to provider go through source NAT which may prevent applications from identifying the consumer IP address.
- Pricing Consideration:
  - Data processing charges apply for each Gigabyte processed through the VPC endpoint regardless of the traffic’s source or destination
  - Data transferred between availability zones, or between your Endpoint and your premises via Direct Connect will also incur the usual EC2 Regional and Direct Connect data transfer charges. See [AWS PrivateLink pricing](https://aws.amazon.com/privatelink/pricing/).

Here is an example of when you would use a AWS privatelink. You have a production VPC with many data sources such as Redshift, Aurora and MySQL. The business would like to query the data from the MySQL database, but not expose confidential data stored in Redshift or Aurora. Using privatelink, you can open a connection from Databricks clusters to MySQL, allowing your users to access MySql securely while restricting connectivity to Redshift and Aurora.

### The Configuration

Manual or programmatic VPC peering: [https://docs.databricks.com/administration-guide/cloud-configurations/aws/vpc-peering.html](https://docs.databricks.com/administration-guide/cloud-configurations/aws/vpc-peering.html)

Manual Privatelink setup: [https://docs.aws.amazon.com/vpc/latest/privatelink/endpoint-services-overview.html](https://docs.aws.amazon.com/vpc/latest/privatelink/endpoint-services-overview.html)

Databricks resources on connecting to data sources

- [Kafka connection example](https://docs.databricks.com/spark/latest/structured-streaming/kafka.html#structured-streaming-kafka)
- [Connecting to various Data Sources](https://docs.databricks.com/data/data-sources/index.html)

## Final Steps

Once a network connection via VPC Peering or Privatelink is established, authentication with the specific data source or service can then be setup. Please access Databricks on AWS documentation for the [specific data sources](https://docs.databricks.com/data/data-sources/index.html) that you need access to. Wherever possible consider using [secrets](https://docs.databricks.com/security/secrets/index.html#secrets-user-guide) to keep your connection secure.  Using the correct connection options based on your needs reduces overall complexity and helps Data Scientist and Data Engineers have access to the data they need in a secure manner.

### **Try It!**

- [Call us](https://www.databricks.com/company/contact) to find out how Databricks can improve your security posture.
- Learn more by downloading our [security e-book Protecting Enterprise Data on Apache Spark](https://pages.databricks.com/Protecting-Enterprise-Data-Spark.html).
