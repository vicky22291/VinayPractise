# Extending Delta Sharing to Google Cloud Storage

- Source: https://www.databricks.com/blog/2022/03/16/extending-delta-sharing-to-google-cloud-storage.html
- Published: 2022-03-16
- Authors: Will Girten, Ryan Zhu, Denny Lee
- Categories: engineering, open-source
- Images: 2 total, 2 extracted as architecture

> This blog article has been cross-posted from the [Delta.io blog](https://delta.io/blog/2022-03-11-delta-sharing-0-4-0-released/).

We are excited for the [release](https://github.com/delta-io/delta-sharing/releases/tag/v0.4.0) of Delta Sharing 0.4.0 for the open-source data lake project Delta Lake. The latest release introduces several key enhancements and bug fixes, including the following features:

- **Delta Sharing is now available for Google Cloud Storage** - You can now share Delta Tables on the Google Cloud Platform ([#81](https://github.com/delta-io/delta-sharing/pull/81), [#105](https://github.com/delta-io/delta-sharing/pull/105))
- **A new API for getting the metadata of a Delta Share** - a new GetShare REST API has been added for querying a Share by its name ([#95](https://github.com/delta-io/delta-sharing/pull/97), [#97](https://github.com/delta-io/delta-sharing/pull/97))
- **Delta Sharing Protocol and REST API enhancements** - the Delta Sharing protocol has been extended to include the Share Id and Table Ids, as well improved response codes and error codes ([#85](https://github.com/delta-io/delta-sharing/pull/85), [#89](https://github.com/delta-io/delta-sharing/pull/89), [#93](https://github.com/delta-io/delta-sharing/pull/93), [#98](https://github.com/delta-io/delta-sharing/pull/98))
- **Customize a recipient sharing profile in the Apache Spark™ connector** - a new Delta Sharing Profile Provider has been added to the Spark connector to enable easier access of the sharing profile ([#99](https://github.com/delta-io/delta-sharing/pull/99), [#107](https://github.com/delta-io/delta-sharing/pull/107))

In this blog post, we will go through each of the improvements in this release.

## Delta Sharing on Google Cloud Storage

New to this release, you can now share Delta Tables in Google Cloud Storage using the reference implementation of a Delta Sharing Server.

*With Delta Sharing 0.4.0, you can now share Delta Tables stored on Google Cloud Storage.*

**Summary:** Shows Delta Sharing between a data provider’s Delta Lake Table on Google Cloud Storage and data recipients using sharing clients.

**Components:**

- Data Provider
- Delta Lake Table
- Delta Sharing Server
- Access permissions
- Delta Sharing Protocol
- Data Recipient
- Power BI
- Apache Spark
- pandas
- Tableau
- Any Sharing Client
- Google Cloud Storage

**Flows:**

- Delta Lake Table -> Delta Sharing Server: table data and sharing metadata
- Delta Sharing Server -> Delta Lake Table: table access
- Delta Sharing Server -> Delta Sharing Protocol: access permissions
- Delta Sharing Protocol -> Any Sharing Client: shared table access
- Google Cloud Storage -> Delta Lake Table: table storage

**Numbers:** none

```mermaid
%% Shows Delta Sharing between Google Cloud Storage tables and recipient clients
flowchart LR
    subgraph Provider[Data Provider]
        GCS[Google Cloud Storage]:::store
        Table[Delta Lake Table]:::store
        Server[Delta Sharing Server]:::service
        Perms[Access permissions]:::decision
        GCS --> Table
        Table <--> |table access| Server
        Server --> |permissions| Perms
    end

    Protocol[Delta Sharing Protocol]:::service

    subgraph Recipient[Data Recipient]
        PowerBI[Power BI]:::client
        Spark[Apache Spark]:::client
        Pandas[pandas]:::client
        Tableau[Tableau]:::client
        AnyClient[Any Sharing Client]:::client
    end

    Perms --> Protocol
    Protocol --> |shared table access| AnyClient
    AnyClient --> PowerBI
    AnyClient --> Spark
    AnyClient --> Pandas
    AnyClient --> Tableau

    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2022/03/db-104-blog-img-1.png</sub>

 With Delta Sharing 0.4.0, you can now share Delta Tables stored on Google Cloud Storage.

### Delta Sharing on Google Cloud Storage example

Sharing Delta Tables on Google Cloud Storage is easier than ever! For example, to share a Delta Table called “time”, you can simply update the Delta Sharing server configuration with the location of the Delta table on [Google Cloud Storage](https://cloud.google.com/storage):

*Delta Sharing Server configuration file containing the location to a Delta table on Google Cloud Storage.*

The Delta Sharing server will automatically process the data on Google Cloud Storage for a Delta Sharing query.

### Authenticating with Google Cloud Storage

The Delta Sharing Server acts as a gatekeeper to the underlying data in a Delta Share. When a recipient queries a Delta table in a Delta Share, the Delta Sharing Server first checks the permissions to make sure the data recipient has access to data. Next, if access is permitted, the Delta Sharing Server will look at the file objects that make up the Delta table and smartly filter down the files if a predicate is included in the query, for example. Finally, the Delta Sharing Server will generate short-lived, pre-signed URLs that allow the data recipient to access the files, or subset of files, from the Delta Sharing Client directly from cloud storage rather than streaming the data through the Delta Sharing Server.

*The Delta Sharing Server acts as a gatekeeper to the underlying data in a Delta Share.*

**Summary:** The diagram shows the Delta Sharing Server mediating access between a Delta Lake table and data recipients through permission checks and short-lived URLs.

**Components:**

- Data Provider
- Delta Lake Table
- Delta Sharing Server
- Data Recipient
- Delta Sharing Client
- Tableau, Spark, and pandas client technologies
- Recipient user

**Flows:**

- Delta Lake Table -> Delta Sharing Server: table metadata and data access
- Delta Sharing Server -> Delta Lake Table: reads underlying table files
- Delta Sharing Client -> Delta Sharing Server: request to read table sales
- Delta Sharing Server -> Delta Sharing Client: short-lived URLs to read permitted files
- Delta Lake Table -> Delta Sharing Client: direct file access using short-lived URLs

**Numbers:** none

```mermaid
%% Shows Delta Sharing access mediation and direct cloud storage file reads
flowchart LR
    DP[Data Provider]
    T[Delta Lake Table]
    S[Delta Sharing Server]
    R[Data Recipient]
    C[Delta Sharing Client]
    U[Tableau Spark pandas]
    P[Recipient User]

    DP -.-> S
    T <--> S
    C -->|Request to read table sales| S
    S -->|Short lived URLs to read| C
    T -.->|Underlying files| C
    R --> C
    C --> U
    U --> P

    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111

    class DP,R,P external
    class T store
    class S critical
    class C,U client
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2022/03/db-104-blog-img-2.jpg</sub>

 The Delta Sharing Server acts as a gatekeeper to the underlying data in a Delta Share.

In order to generate the short-lived file URLs, the Delta Sharing Server uses a [Service Account](https://cloud.google.com/iam/docs/service-accounts) to read Delta tables from Google Cloud Storage. To configure the Service Account credentials, you can set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` before starting the Delta Sharing Server.

## New API for getting a Delta Share

Sometimes, it might be helpful for a recipient to check if they still have access to a Delta Share. This release adds a new REST API, `GetShare,` so that users can quickly test if a Delta Share has exceeded its expiration time.

For example, to check if you still have access to a Delta Share you can simply send a GET request to the `/shares/{share_name}` endpoint on the sharing server:

*Example GET request sent to the sharing server that enables recipients to check whether or not they still have access to a Delta Share.*

*Example response received from the GetShare REST API that is new to the Delta Sharing 0.4.0 release.*

If the Delta Share has exceeded its expiration, the Sharing server will respond with a 403 HTTP error code.

## Delta Sharing protocol enhancements

Included in this release are improved error codes and error messages in the Delta Sharing protocol definition. For example, if a Delta Share is not located on the Delta Sharing Server, an error code and error message containing the details of the error is now included in this release.

*Example GET request for a Share that does not exist on the Delta Sharing Server.*

*Example response containing an improved error code and details about the error that is new to the Delta Sharing 0.4.0 release.*

Furthermore, this release extends the Delta Sharing Protocol to respond with the unique Delta Share and Table Ids. Unique Ids help the data recipient disambiguate the name of datasets as time passes. This is especially useful when the data recipient is a large organization and wants to apply access control on the shared dataset within their organization

## Customizing a recipient Sharing profile

The Delta Sharing profile file is a JSON configuration file that contains the information for a recipient to access shared data on a Delta Sharing server. A new provider has been added in this release that enables easier access to the Delta Sharing profile for data recipients.

*The Delta Sharing profile file is a JSON configuration file that contains the information for a recipient to access shared data on a Delta Sharing server.*

## What’s next

We are already gearing up for many new features in the next release of Delta Sharing. You can track all the upcoming releases and planned features in [GitHub milestones](https://github.com/delta-io/delta-sharing/milestones).

---

**Credits**
 We’d like to extend a special thanks for the contributions to this release to Denny Lee, Lin Zhou, Shixiong Zhu, William Chau, Xiaotong Sun, Kohei Toshimitsu.
