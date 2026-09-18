# Machine Learning-based Item Matching for Retailers and Brands

- Source: https://www.databricks.com/blog/2021/05/24/machine-learning-based-item-matching-for-retailers-and-brands.html
- Published: 2021-05-24
- Authors: Luke Bilbro, Bryan Smith, Rob Saker
- Categories: platform, engineering, solution-accelerators, data-science-machine-learning, data-engineering
- Images: 2 total, 1 extracted as architecture

Item matching is a core function in online marketplaces. To ensure an optimized customer experience, retailers compare new and updated product information against existing listings to ensure consistency and avoid duplication.  Online retailers may also compare their listings with those of their competitors to identify differences in price and inventory.  Suppliers making products available across multiple sites may examine how their goods are presented to ensure consistency with their own standards.

The need for effective item matching is certainly not limited to online commerce. For decades, Demand Signal Repositories (DSRs) promised consumer goods manufacturers the ability to combine replenishment order data with retailer point-of-sale and syndicated market data to develop a more holistic picture of demand. However, the value of the DSR is limited by the degree to which the manufacturer can resolve differences between their product definitions and those product descriptions across dozens of retail partners.

The challenge of bringing these types of data together has been in the manual effort required to match disparate data sets. We are fortunate to have universal keys in some areas that enable direct linkage between data sets, but in most scenarios this is not the case - we’re forced to use expert knowledge to determine which items are likely pairs and which are distinct. It is for this reason that matching items across disparate data sets is often the lengthiest of steps in any complex data project, a step which must be repeated on an on-going basis as new products are added.

Numerous and on-going attempts at standardizing product codes dating back to the 1970s highlight the universality of this challenge but also its recalcitrance. Rules-based and probabilistic (fuzzy) matching techniques have demonstrated the potential of software to perform reasonably effective product matching on imperfect data, but often these tools are limited in terms of the data they support, their ability to be customized and their ability to scale.  With the advent of Machine Learning, Big Data platforms and the cloud, we have the potential to evolve these techniques and overcome these challenges.

## Calculating product similarities

To illustrate how this might be done, let’s first examine how product information might be used to match two items. Here, we have two listings, one from *abt.com* and another from *buy.com,* as captured in the Abt-Buy dataset, for what has been determined to be the same product:

As consumers, wecan look at the name and determine the sites are describing similar products. The slight differences in codes, i.e. FDB130WH and FBD130RGS, might cause some confusion, but we could review the product descriptions, technical specs, etc. on the websites to determine these are the same appliances. But how might we instruct a computer to do this same work?

First, we might split the name into individual words, standardize word case, remove any punctuation, and drop any safely ignored words like the, and, and for before treating the remaining elements as an unsequenced collection (bag) of words. Here, we have done this for our matched products, sorting the words solely for easier visual comparison:

We can see that most of the words are the same. The only variations are found in the product codes, and even then, it’s a variation that occurs in the last two or three characters. If we break these words down into character sequences, (*i.e.* character-based [n-grams](https://en.wikipedia.org/wiki/N-gram)), we can more easily compare the words in detail:

abt: [ fri, rig, igi, gid, ida, dai, air, ire, re, fdb, db1, b13, 130, 30w, 0wh, wh, ... ]
 buy: [ fri, rig, igi, gid, ida, dai, air, ire, re, fdb, db1, b13, 130, 30r, rgs, gs, ... ]

Each sequence is then scored by their frequency of occurrence within the name and their overall occurrence across all product names with non-represented sequences being scored as zeros:

fri, rig, igi, gid, ida, dai, air, ire, re, fdb, db1, b13, 130, 30w, 30r, 0wh, wh, rgs, gs, ...
 abt: 0.17, 0.19, 0.17, 0.13, 0.13, 0.17, 0.18, 0.20, 0.12, 0.14, 0.17, 0.18, 0.19, 0.02, 0.00, 0.13, 0.18, 0.00, 0.00, ...
 buy: 0.17, 0.19, 0.17, 0.13, 0.13, 0.17, 0.18, 0.20, 0.12, 0.14, 0.17, 0.18, 0.19, 0.00, 0.03, 0.00, 0.00, 0.15, 0.17, ...

Known as [TF-IDF scoring](https://en.wikipedia.org/wiki/Tf%E2%80%93idf), this natural language processing (NLP) technique allows us to convert our string-comparison problem into a mathematical problem. The similarity between these two strings can now be calculated as the sum of the squared differences between the aligned values, approximately 0.359 for these two strings. When compared to other potential matches for these products, this value should be among the lowest, indicating the likelihood of an actual match.

The series of steps presented for product names is by no means exhaustive. Knowledge of specific patterns in a particular domain may encourage the use of other, more sophisticated, means of data preparation, but the simplest techniques often are surprisingly effective.

For longer sequences of text such as product descriptions, word-based n-grams with TF-IDF scoring and [text embeddings](https://machinelearningmastery.com/what-are-word-embeddings/) that analyze blocks of text for word associations may offer better scoring approaches. For image data, a similar approach of [embedding](https://medium.com/pinterest-engineering/detecting-image-similarity-using-spark-lsh-and-tensorflow-618636afc939) may also be applied, allowing even more information to be brought into consideration. As retailers such as [Walmart](https://medium.com/walmartglobaltech/product-matching-in-ecommerce-4f19b6aebaca) have demonstrated, any information that is useful in determining product similarity may be employed. It’s simply a matter of converting that information into a numerical representation from which distance or related measures of similarity can be derived.

## Dealing with data explosion

With a basis for determining similarities established, our next challenge is to efficiently compare individual products to one another. To understand the scale of this challenge, consider comparing a relatively small dataset of 10,000 products t against a different set of 10,000. An exhaustive comparison would require evaluating 100-million product pairs. While not an impossible challenge  (especially given the availability of cloud resources),  a more efficient shortcut allows us to focus our attention on those pairs more similar to one another.

[Locality-Sensitive Hashing](https://en.wikipedia.org/wiki/Locality-sensitive_hashing) (LSH) provides a fast and efficient method for doing just that. The LSH process works by randomly subdividing products in such a way that products with similar numerical scores are likely to reside in the same groups. The random nature of the subdivisions means that two very similar products may find themselves in different groups, but by repeating the process multiple times, we increase the odds that two very similar items will land in the same group at least once. And that’s all we need to consider them as candidates for further evaluation.

## Identifying matches

With our focus centered on products most likely to be matches, we turn to the actual match determination. Leveraging similarity scores derived for each product attribute considered, we now seek to translate those scores into a match probability.

It’s not a simple process of applying a known formula and weighing each attribute to arrive at a singular prediction. Instead, we must rely on a ML algorithm to learn from expert-matched pairs and identify how these scores should be combined to arrive at a probability. A typical model development exercise starts with a limited set of products that are manually evaluated for matches, the generation of candidate pairs for the products employed in this exercise, and then the iterative training of any number of [binary classification algorithms](https://en.wikipedia.org/wiki/Binary_classification#Statistical_binary_classification) until a reasonable result is obtained.

*Figure 1. A sample product matching workflow*

**Summary:** The image shows a left-to-right workflow with seven unlabeled stages connected by six arrows.

**Components:** None visible.

**Flows:**

- Unlabeled stage 1 -> Unlabeled stage 2: unlabeled flow
- Unlabeled stage 2 -> Unlabeled stage 3: unlabeled flow
- Unlabeled stage 3 -> Unlabeled stage 4: unlabeled flow
- Unlabeled stage 4 -> Unlabeled stage 5: unlabeled flow
- Unlabeled stage 5 -> Unlabeled stage 6: unlabeled flow
- Unlabeled stage 6 -> Unlabeled stage 7: unlabeled flow

**Numbers:** none

```mermaid
%% Left-to-right workflow with seven unlabeled stages
flowchart LR
    A[Unlabeled stage 1] -->|unlabeled flow| B[Unlabeled stage 2]
    B -->|unlabeled flow| C[Unlabeled stage 3]
    C -->|unlabeled flow| D[Unlabeled stage 4]
    D -->|unlabeled flow| E[Unlabeled stage 5]
    E -->|unlabeled flow| F[Unlabeled stage 6]
    F -->|unlabeled flow| G[Unlabeled stage 7]

    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111

    class A,B,C,D,E,F,G service
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2021/05/Machine-Learning-based-Item-Matching-for-Retailers-Brands-blog-img-1.png</sub>

Figure 1. A sample product matching workflow

The model is then used as part of a larger pipeline to score more products. Predictions with the highest and the lowest match probabilities are largely accepted while experts continue to evaluate those scored in the middle. Those expert-identified matches are recorded and added into the next cycle of model training to whittle away at the number of potential matches requiring on-going human assessment.

## Leveraging Databricks for product matching

Databricks is an ideal platform for developing scalable product matching capabilities. With support for a [wide range](https://docs.databricks.com/data/data-sources/index.html) of data formats and a [rich and extensible](https://docs.databricks.com/applications/machine-learning/index.html) set of data transformation and ML capabilities, Databricks provides an environment where data scientists and data engineers can explore many different techniques, such as computer vision, NLP and other deep learning strategies, for extracting product features.

With [MLflow](https://docs.databricks.com/applications/mlflow/index.html), a machine learning model management platform integrated with Databricks, engineers can operationalize the multi-stage feature generation, product-pair generation and match prediction workflow associated with this process.

With the rapid provisioning and deprovisioning of cloud resources, those workflows can be [cost-effectively](https://docs.databricks.com/clusters/cluster-config-best-practices.html) allocated resources-as-needed. And with integration into the broader [cloud service ecosystem](https://www.databricks.com/product/enterprise-cloud-service), organizations can build a complete product matching system for use within their environment.

To see how Databricks may be used to deliver product matching capabilities, check out our [Solution Accelerator for Product Matching with Machine Learning](https://www.databricks.com/solutions/accelerators/product-matching-with-ml).
