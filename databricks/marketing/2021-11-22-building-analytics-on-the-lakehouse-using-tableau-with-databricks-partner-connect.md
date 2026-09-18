# Building Analytics on the Lakehouse Using Tableau With Databricks Partner Connect

- Source: https://www.databricks.com/blog/2021/11/22/building-analytics-on-the-lakehouse-using-tableau-with-databricks-partner-connect.html
- Published: 2021-11-22
- Authors: Madeleine Corneli
- Categories: platform, partners, data-warehousing
- Images: 6 total, 1 extracted as architecture

This is a guest authored post by Madeleine Corneli, Sr. Product Manager, Tableau.

On November 18, Databricks announced [Partner Connect](https://www.databricks.com/blog/2021/11/18/now-generally-available-introducing-databricks-partner-connect-to-discover-and-connect-popular-data-and-ai-tools-to-the-lakehouse.html), an ecosystem of pre-integrated partners that allows customers to discover and connect data, analytics and AI tools to their lakehouse. Tableau is excited to be among a set of launch partners to be featured in Partner Connect, helping users visualize all the data in their data lakehouse.

“For every data-driven organization, a robust data visualization and analytics solution, like Tableau, ensures that people can easily access, analyze and understand the data that’s driving their business forward. Databricks Partner Connect eliminates the complexity of connecting Tableau to a customers’ lakehouse to uncover data-driven insights even faster. We’re excited to be partnered even more closely with Tableau to bring this speed and agility to our customers together,” said Adam Conway, SVP of Products at Databricks.

## Databricks Partner Connect: Analytics for your Lakehouse

Tableau on Databricks Partner Connect helps customers get to insights faster, improving the time to value for big data and data science investments. Within seconds, users can move seamlessly from the Databricks UI to Tableau Desktop to stay in the flow of their analysis.

The promise of the lakehouse is to bring all the data to every user in the tools they know and love. Using Tableau with Databricks helps unlock the full value of your lakehouse by allowing you to create a comprehensive picture of your organization’s data through visual analytics. With comprehensive analytics and faster insights, customers like [Wehkamp](https://www.databricks.com/customers/wehkamp)use Tableau and Databricks together to make data-driven decisions and eliminate bottlenecks between analysts and data stewards.

Tableau in Partner Connect allows your users to easily access and analyze relevant data in a secure and governed environment. Tableau offers numerous ways to explore your data visually as well as with smart analytics features like Ask and Explain Data. You can [read more here](https://www.tableau.com/about/blog/2021/6/how-databricks-and-tableau-customers-are-fueling-innovation-data-lakehouse) to learn more about how Tableau and Databricks work together to bring value to your organization.

**Summary:** The diagram shows a five-step workflow for connecting a BI partner to a Databricks cluster through Databricks Partner Connect and querying lakehouse data.

**Components:**

- Databricks Partner Connect: BI integration workflow
- BI partner selection: BI tool marketplace
- Databricks endpoint: Connection endpoint
- Connection file: Downloadable connection configuration
- Partner BI tool: External visualization technology
- Databricks cluster: Compute connected to the BI tool
- Lakehouse: Governed data queried and visualized

**Flows:**

- BI partner selection -> Databricks endpoint: Select an endpoint
- Databricks endpoint -> Connection file: Download the connection file
- Connection file -> Partner BI tool: Open the connection file
- Partner BI tool -> Databricks cluster: Enter credentials and connect
- Databricks cluster -> Lakehouse: Query and visualize data

**Numbers:** 1, 2, 3, 4, 5

```mermaid
%% Shows the Databricks Partner Connect BI integration workflow
flowchart LR
    A[Select a BI partner] -->|1 Select partner| B[Databricks Partner Connect]
    B -->|2 Select endpoint| C[Databricks endpoint]
    C -->|Download| D[Connection file]
    D -->|3 Open file| E[Partner BI tool]
    E -->|4 Enter credentials| F[Databricks cluster]
    F -->|5 Query and visualize| G[Lakehouse]

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111

    class A client
    class B,C,D service
    class E external
    class F service
    class G store
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2021/11/partner-connect-blog-img-4-new.png</sub>

Tableau on Databricks Partner Connect streamlines the data connection process by:

- Simplifying the user journey
- Keeping users in the flow of their analysis
- Programatically creating a Tableau data source ready for immediate analysis

## How to Launch Tableau via Databricks Partner Connect

1. In Databricks Partner Connect, select Tableau under BI and visualization.

2. Select your compute endpoint and download the connection file.

3. Once you open the connection file, enter the credentials to connect to the Databricks cluster from your Tableau desktop.

4. Start your analysis.

To learn more about Partner Connect, click [here](https://www.databricks.com/partnerconnect).
