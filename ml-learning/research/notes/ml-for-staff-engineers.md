# Machine learning for Staff software engineers: research notes

Status: 17 October 2026. Scope: production ML and ML system design interviews, for a Staff software engineer who is not an ML specialist.

How to read these notes
- Every factual or numeric claim has an inline link. Dates appear in the text and in the Sources table.
- [unverified] means I could not open a primary page for the claim. Do not use it as fact.
- [pre-2020] marks older sources. They are kept because they are foundational. Check their numbers against newer work before you quote them as current.
- Method: about 70 search, fetch and download calls on 17 Oct 2026. Pages were read directly where possible. JS-heavy pages were read through the r.jina.ai reader. Uber posts that returned 406 to curl were read from the Wayback Machine. Empty fetches are listed under Gaps.
- Company numbers are company-reported. I did not check them independently.

## Key question 1: Which companies run ML system design interviews, and for which roles?

### Takeaway
Public evidence is thin. Meta publishes an ML onsite prep page, but its text does not name a system design round. Stripe's public process guide describes rubrics and does not mention system design. The most explicit public source is Hello Interview's ML System Design guide. It says ML design rounds are most common at senior level. Anything more specific is unverified.

### Cited findings
- Meta: "The full loop interview will consist of up to six 45-minute conversations with our engineers. To help you prepare, Machine Learning engineers at Meta have created this comprehensive guide." ([Meta ML onsite prep](https://www.metacareers.com/ML-prep-onsite/), undated, read 17 Oct 2026).
- Meta hiring process: [Meta hiring process](https://www.metacareers.com/hiring-process/) returned no readable text in my fetch.
- Stripe: "We standardise questions using written rubrics that define exactly how to run each interview." ([Stripe, Scaling engineering organisations](https://stripe.com/guides/atlas/scaling-eng), undated). The guide describes a "Bug Squash" interview. My search of the guide for "system design" found nothing.
- Hello Interview: "Entry-level ML roles are rare (unless you have an advanced degree), and they usually exclude an ML system design component. By mid-level, ML system design interviews become more common, and at the senior level they are the norm." ([Hello Interview, ML System Design](https://www.hellointerview.com/learn/ml-system-design), undated, labelled "early access", read via reader proxy).
- Hello Interview: "Machine Learning System Design is the wild west of interviews: the field is new and growing rapidly, yet consistency amongst companies and interviewers is low." (same page).
- Hello Interview names three interview types in its text: Applied ML System Design, AI/ML Research and AI/ML Research Engineering. It says its guide is "partly" useful for ML Infra Design interviews (same page).
- Hello Interview on scoring: "Model design is the heart of ML system design interviews." and "First, interviewers want to see whether you can frame a vague business goal as a measurable ML problem." (same page).
- Hello Interview's free harmful-content breakdown sets the constraints. It gives "50k examples, 50% harmful and 50% benign" for initial training, "< 1% of posts are harmful", and "95% precision is a threshold for automated deletion" ([Hello Interview, harmful content](https://www.hellointerview.com/learn/ml-system-design/problem-breakdowns/harmful-content), undated, read via reader; no paywall text in the extract).
- Question bank: the ByteByteGo course lists 11 chapters. Chapter 01 is an overview and the rest are case studies: 01 Introduction and Overview; 02 Visual Search System; 03 Google Street View Blurring System; 04 YouTube Video Search; 05 Harmful Content Detection; 06 Video Recommendation System; 07 Event Recommendation System; 08 Ad Click Prediction on Social Platforms; 09 Similar Listings on Vacation Rental Platforms; 10 Personalized News Feed; 11 People You May Know ([ByteByteGo course](https://bytebytego.com/courses/machine-learning-system-design-interview), date not shown).
- Uber: a careers blog post on interviews exists ([Navigating interviews](https://www.uber.com/blog/navigating-uber-engineering-interviews/)), but my copy had no readable text.
- Google: [How we hire](https://www.google.com/about/careers/applications/how-we-hire/) had no ML-specific text in static HTML or in the reader copy.

Company summary (what I could confirm):

| Company | Official page read | ML design round confirmed? | Gap note |
|---|---|---|---|
| Meta | [ML onsite prep](https://www.metacareers.com/ML-prep-onsite/) | No. The page confirms six 45-minute conversations only | Hiring-process page had no text |
| Google | [How we hire](https://www.google.com/about/careers/applications/how-we-hire/) | No | No ML text in static or reader copy |
| Stripe | [Scaling engineering organisations](https://stripe.com/guides/atlas/scaling-eng) | No. Rubrics and Bug Squash only | Guide undated |
| Uber | [Navigating interviews](https://www.uber.com/blog/navigating-uber-engineering-interviews/) | Unverified | No readable text |
| Airbnb | None found | Unknown | Gap |
| LinkedIn | None found | Unknown | Gap |
| Pinterest | None found | Unknown | Gap |
| Netflix | None found | Unknown | Gap |

Strong-answer coverage map, using the sources above:
- Problem framing: [Rules of ML #2](https://developers.google.com/machine-learning/guides/rules-of-ml) and the Hello Interview scoring note.
- Offline and online metrics: [Airbnb](https://arxiv.org/pdf/1810.09591) and Rules #12 and #39.
- Data and labels: [Stripe disputes](https://docs.stripe.com/disputes/how-disputes-work.md) and Rules #33.
- Features: [Feast](https://docs.feast.dev/getting-started/concepts/point-in-time-joins) and [Uber 2018](https://www.uber.com/blog/scaling-michelangelo/).
- Model choice: [YouTube two-stage design](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/45530.pdf) and [LiRank](https://arxiv.org/abs/2402.06859).
- Training: Rules #30 and #33.
- Serving: the YouTube latency budget and the [DLRM memory limit](https://arxiv.org/pdf/1906.00091).
- Evaluation: [Guo et al. on calibration](http://arxiv.org/abs/1706.04599) and [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html).
- A/B testing: [SRE canary](https://sre.google/workbook/canarying-releases/) and [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.power.NormalIndPower.html).
- Monitoring: [ML Test Score](https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/) and [Uber 2018](https://www.uber.com/blog/scaling-michelangelo/).

### Inferences
- Role level matters more than company. The public signal puts ML design at senior level, which fits a Staff candidate.
- The ML Infra Design type may suit a distributed-systems Staff engineer better than applied modelling. This is my inference from Hello Interview's scope note.
- Across the sources, the question bank repeats the same families: feed and recommendations, ads CTR, search, fraud, harmful content, people you may know, and ETA.

### Gaps
- No official Google, Stripe, Uber, Airbnb, LinkedIn, Pinterest or Netflix page describing an ML design round was found. One search for Airbnb, LinkedIn, Pinterest and Netflix returned only LinkedIn posts.
- No primary source says whether software engineer and ML engineer loops differ at any company.
- Round length, scoring and prompts at Meta, Stripe and Google are unverified. The Meta page gives only the loop size.
- Third-party guides (Interview Kickstart, Codemia, System Design Handbook, Blind threads) are anecdotal. They are not used as facts here.
- Hello Interview premium sections are paywalled. I did not read them.

## Key question 2: Books, guides and pattern lists

### Takeaway
The lists below come from primary repos and course pages. The O'Reilly tables of contents did not open. Book years are shown where a repo gives them, and [unverified] otherwise.

### Cited findings
- Huyen, Designing Machine Learning Systems. The repo says "Designing Machine Learning Systems (Chip Huyen 2022)" ([README](https://raw.githubusercontent.com/chiphuyen/dmls-book/main/README.md)). Chapters ([summary](https://raw.githubusercontent.com/chiphuyen/dmls-book/main/summary.md)): 1 Overview of Machine Learning Systems; 2 Introduction to Machine Learning Systems Design; 3 Data Engineering Fundamentals; 4 Training Data; 5 Feature Engineering; 6 Model Development and Offline Evaluation; 7 Model Deployment and Prediction Service; 8 Data Distribution Shifts and Monitoring; 9 Continual Learning and Test in Production; 10 Infrastructure and Tooling for MLOps; 11 The Human Side of Machine Learning.
- Huyen, AI Engineering. Its README asks: "How do I evaluate my application? Can I use AI to evaluate AI outputs?", "Why does RAG work? What are the strategies for doing RAG?", "What's an agent? How do I build and evaluate an agent?" and "When to finetune a model? When not to finetune a model?" ([aie-book](https://github.com/chiphuyen/aie-book); edition date [unverified]).
- Lakshmanan, Robinson and Munn, Machine Learning Design Patterns. The repo lists 30 patterns ([ml-design-patterns](https://github.com/GoogleCloudPlatform/ml-design-patterns)): #1 Hashed Feature, #2 Embedding, #3 Feature Cross, #4 Multimodal Input, #5 Reframing, #6 Multilabel, #7 Ensemble, #8 Cascade, #9 Neutral Class, #10 Rebalancing, #11 Useful Overfitting, #12 Checkpoints, #13 Transfer Learning, #14 Distribution Strategy, #15 Hyperparameter Tuning, #16 Stateless Serving Function, #17 Batch Serving, #18 Continuous Model Evaluation, #19 Two Phase Predictions, #20 Keyed Predictions, #21 Transform, #22 Repeatable Sampling, #23 Bridged Schema, #24 Windowed Inference, #25 Workflow Pipeline, #26 Feature Store, #27 Model Versioning, #28 Heuristic Benchmark, #29 Explainable Predictions, #30 Fairness Lens. Book year [unverified].
- Zinkevich, Rules of Machine Learning ([Google developers](https://developers.google.com/machine-learning/guides/rules-of-ml)). The page says "Last updated 2025-08-25 UTC". The original year is not shown. Rules used in these notes:
  - #2 "First, design and implement metrics."
  - #4 "Keep the first model simple and get the infrastructure right."
  - #8 "Know the freshness requirements of your system."
  - #12 "Don't overthink which objective you choose to directly optimize."
  - #15 "Separate Spam Filtering and Quality Ranking in a Policy Layer."
  - #29 "...save the set of features used at serving time, and then pipe those features to a log..."
  - #30 "Importance-weight sampled data, don't arbitrarily drop it!"
  - #31 "Beware that if you join data from a table at training and serving time, the data in the table may change."
  - #33 "If you produce a model based on the data until January 5th, test the model on the data from January 6th and after."
  - #36 "Avoid feedback loops with positional features."
  - #37 "Measure Training/Serving Skew."
  - #39 "Launch decisions are a proxy for long-term product goals."
- Sculley et al., Hidden Technical Debt in Machine Learning Systems. NIPS 2015 ([PDF](https://papers.nips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf)). Sections include 3 Data Dependencies Cost More than Code Dependencies, 4 Feedback Loops, 5 ML-System Anti-Patterns, 6 Configuration Debt and 7 Dealing with Changes in the External World. Quote: "a mature system might end up being (at most) 5% machine learning code and (at least) 95% glue code". Quote: "A more difficult case is hidden feedback loops, in which two systems influence each other indirectly through the world." [pre-2020]
- Shankar et al., Operationalizing Machine Learning: An Interview Study ([arXiv 2209.09125](http://arxiv.org/abs/2209.09125), 16 Sep 2022). The authors interviewed 18 MLEs. Their success variables are "Velocity, Validation, and Versioning."
- Breck et al., The ML Test Score ([Google research](https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/), IEEE Big Data 2017). Quote: "we present 28 specific tests and monitoring needs". [pre-2020]
- Breck et al., Data Validation for Machine Learning ([Google research](https://research.google/pubs/data-validation-for-machine-learning/), SysML 2019, listed as "to appear"). The abstract names "training/serving skew" among its main challenges. [pre-2020]

### Inferences
- Huyen's chapters 5, 7, 8 and 9 cover features, deployment, drift and monitoring. Those are the production topics in Key question 3.
- Rules of ML works as a Staff-level checklist. The NIPS paper supplies the vocabulary: glue code, feedback loops and boundary erosion.

### Gaps
- The O'Reilly tables of contents for Huyen (2022) and Lakshmanan (2020) did not open. Those book years are [unverified].
- ByteByteGo's book edition, date and chapter count are not verified. The course page may not match the book.

## Key question 3: Production concepts, one primary source each

Definitions are in my own words. The evidence follows each one.

### Takeaway
Most concepts have a primary source above. Three gaps remain: retraining cadence, research on shadow deployment, and a formal cold-start source.

### Cited findings

**Data and labels**
- Training-serving skew: features differ between training and serving. Rules #37 says: "If you apply a model to an example in the training data and the same example at serving, it should give you exactly the same result." Uber built its feature store so that it "ensur[es] consistency between online and offline versions" ([Uber, 2 Nov 2018](https://www.uber.com/blog/scaling-michelangelo/)). [pre-2020]
- Feature store: shares features and runs their offline and online pipelines. Uber's Palette "hosts more than 20,000 features" ([Uber, 2 May 2024](https://www.uber.com/en-GB/blog/from-predictive-to-generative-ai)).
- Point-in-time correct join: each training row sees only the feature values that existed at its own timestamp. Feast says it can "reproduce the state of features at a specific point in the past" and adds a created-timestamp rule "to keep backfilled values from leaking into training data" ([Feast docs](https://docs.feast.dev/getting-started/concepts/point-in-time-joins), undated).
- Label leakage: "Data leakage occurs when information that would not be available at prediction time is used when building the model." ([scikit-learn, common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html), undated). The recommender case: "Many collaborative filtering systems implicitly choose the labels and context by holding out a random item and predicting it from other items in the user's history." The paper says this leaks future information ([Covington et al., RecSys 2016](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/45530.pdf), 15-19 Sep 2016). [pre-2020]
- Time-based split: train on the past and test on the future. Rules #33 (above). The YouTube paper predicts "the user's next watch, rather than predicting a randomly held-out watch" (same PDF).
- Class imbalance: positives are rare, as in fraud. "Downsampling the majority class and upweighting it can improve model performance by balancing class representation and reducing prediction bias" ([Google crash course, imbalanced datasets](https://developers.google.com/machine-learning/crash-course/overfitting/imbalanced-datasets), undated). Rules #30 gives the weight rule: sample at 30% and give the example a weight of "10/3". Stripe's 2018 post mentions tweaking "how we handle class imbalance" ([Stripe Radar 2.0](https://stripe.com/en-in/blog/radar-2018), 18 Apr 2018). [pre-2020]
- Delayed labels (chargebacks): "Card networks typically allow cardholders to initiate disputes within 120 days of the original payment." The response to the issuer is "usually 7-21 days" and the issuer decision is "usually 60-75 days" ([Stripe disputes](https://docs.stripe.com/disputes/how-disputes-work.md), undated). Early fraud warnings are an earlier label. "about 40% of Visa and Mastercard EFWs become fraud disputes" if the charge is not refunded (same page). That makes them a noisy proxy label (my inference).

**Drift, metrics and calibration**
- Data drift vs concept drift. My definition: data drift is a change in the inputs. Concept drift is a change in the link from inputs to label. The shift paper names "covariate shift q(x, y) = q(x)p(y|x)" and "label shift q(x, y) = q(y)p(x|y)" ([Rabanser et al., arXiv 1810.11953](http://arxiv.org/abs/1810.11953), 29 Oct 2018; NeurIPS 2019). Concept drift is "unforeseeable changes in the underlying distribution of streaming data over time" ([Lu et al., arXiv 2004.05785](https://arxiv.org/abs/2004.05785), 13 Apr 2020). The best detector in the shift study was "a two-sample-testing-based approach, using pre-trained classifiers for dimensionality reduction" (Rabanser et al.). Uber says "Models can degrade over time because the world is always changing" (Uber, 2 Nov 2018).
- Offline vs online metrics: Airbnb says "The real test is of course online performance of the model." One change gave "about 1%" offline NDCG but "failed to get any statistically significant improvement in online performance" ([Haldar et al., arXiv 1810.09591](https://arxiv.org/pdf/1810.09591), v2 24 Oct 2018). Rules #39 says the same in other words.
- Calibration: predicted probability matches observed frequency. Guo et al. (ICML 2017) say modern networks "are poorly calibrated" and temperature scaling is "surprisingly effective" ([arXiv 1706.04599](http://arxiv.org/abs/1706.04599), 14 Jun 2017). [pre-2020] scikit-learn says "Well calibrated classifiers are probabilistic classifiers for which the output of the predict_proba method can be directly interpreted as a confidence level" ([calibration docs](https://scikit-learn.org/stable/modules/calibration.html), undated). For ads, McMahan et al. write "we can use a calibration layer to match predicted CTRs to observed click-through rates" ([KDD 2013](https://research.google.com/pubs/archive/41159.pdf), 11-14 Aug 2013). [pre-2020]
- Model monitoring: the ML Test Score lists monitoring needs (above). Uber's 2018 post says production predictions should be logged and joined with outcomes to monitor them (Uber, 2 Nov 2018).
- Retraining cadence: no sourced number. Rules #8 covers freshness requirements. Stripe says it engages in "rapidly retraining our models" ([Stripe, 15 May 2025](https://stripe.com/blog/using-ai-optimize-payments-performance-payments-intelligence-suite)).
- Shadow deployment: a copy of live traffic goes to the new model, but its answers are not served. AWS says the variant is deployed "in shadow mode and routes a copy of the inference requests to it in real time." You can "discard or log the responses of the shadow variant for offline comparison" ([SageMaker shadow tests](https://docs.aws.amazon.com/sagemaker/latest/dg/shadow-tests.html), undated, vendor docs).
- Canary and A/B: Google SRE says "We define canarying as a partial and time-limited deployment of a change in a service and its evaluation... Canarying is effectively an A/B testing process" ([SRE Workbook, ch. 16](https://sre.google/workbook/canarying-releases/), undated). For sample sizes, the [statsmodels NormalIndPower.solve_power docs](https://www.statsmodels.org/stable/generated/statsmodels.stats.power.NormalIndPower.html) are the reference (undated). Kohavi et al., "Online Controlled Experiments at Large Scale" (KDD 2013) is cited in search results, but I did not read the abstract [unverified].

**Retrieval, ranking and serving**
- Two-stage retrieval then ranking: "two-stage information retrieval dichotomy: first, we detail a deep candidate generation model and then describe a separate deep ranking model" (Covington et al., 2016). [pre-2020]
- Embeddings and ANN search: items become vectors, and ANN finds close ones fast, with some loss of recall. FAISS: a design "that operates at up to 55% of theoretical peak performance" ([Johnson et al., arXiv 1702.08734](http://arxiv.org/abs/1702.08734), 28 Feb 2017). [pre-2020] ScaNN: "Quantization based techniques are the current state-of-the-art for scaling maximum inner product search to massive databases" ([arXiv 1908.10396](http://arxiv.org/abs/1908.10396), 27 Aug 2019). [pre-2020] HNSW: "approximate K-nearest neighbor search based on navigable small world graphs" ([arXiv 1603.09320](https://arxiv.org/abs/1603.09320); the ID implies 2016, but the API did not return the date).
- Latency budget: "Scoring millions of items under a strict serving latency of tens of milliseconds requires an approximate scoring scheme sublinear in the number of classes" (Covington et al., 2016). [pre-2020]
- Memory is often the bottleneck: DLRM embedding tables need "in excess of multiple GBs of memory", so "this memory constraint necessitates the distribution of the model across multiple devices" ([Naumov et al., arXiv 1906.00091](https://arxiv.org/pdf/1906.00091), 31 May 2019). [pre-2020]
- Serving compression: LiRank will "train and compress models using quantization and vocabulary compression" ([LiRank, arXiv 2402.06859](https://arxiv.org/abs/2402.06859), 10 Feb 2024).
- Feedback loops: "These systems are often evaluated or trained with data from users already exposed to algorithmic recommendations; this creates a pernicious feedback loop." A simulation shows this "homogenizes user behavior without increasing utility" ([Chaney et al., arXiv 1710.11214](http://arxiv.org/abs/1710.11214), 30 Oct 2017). Sculley et al. describe hidden loops "in which two systems influence each other indirectly through the world." Rules #36: "Avoid feedback loops with positional features." [pre-2020]
- Cold start: no formal primary source was read. Netflix frames the problem: "What can we say about a new and unfamiliar title that will pique your interest?" ([Netflix, Artwork Personalization](https://netflixtechblog.com/artwork-personalization-c589f074ad76), page dated 7 Dec 2017, read via Wayback). [pre-2020]

**LLM production concerns**
- Evals: LLM-generated evaluators "simply inherit all the problems of the LLMs they evaluate, requiring further human validation" ([Shankar et al., arXiv 2404.12272](https://arxiv.org/abs/2404.12272), 18 Apr 2024; EvalGen).
- Guardrails and cost: Uber lists "Cost guardrails and attribution" and "Safety & Policy Guardrails: Ensuring LLM usage complies with our internal guidelines" ([Uber, 2 May 2024](https://www.uber.com/en-GB/blog/from-predictive-to-generative-ai)).
- Cost per request: no sourced figure. Provider pricing pages were not read.

### Inferences
- Skew, leakage, label delay, calibration and two-stage retrieval carry the most weight in interviews. Each has a primary source above.
- Shadow, canary and A/B are different tools. Use the AWS and SRE definitions above, not the names interchangeably.

### Gaps
- Retraining cadence: no primary number.
- Shadow deployment: vendor docs only. No research paper read.
- Cold start: no formal primary source.
- LLM cost per request: none sourced.

## Key question 4: Case studies with numbers

### Takeaway
Uber, Stripe and DoorDash give the most recent numbers, all company-reported. The Airbnb, YouTube and PinSage papers give the clearest hardest-problem statements. Stripe does not publish how it matures fraud labels for training.

### Cited findings

**Uber Michelangelo (scale and evolution)**
- 2 Nov 2018 ([Scaling Michelangelo](https://www.uber.com/blog/scaling-michelangelo/)): "hundreds of use cases representing thousands of models are deployed in production on the platform. Millions of predictions are made every second." The named hardest problem: "Data is the hardest part of ML and the most important piece to get right." Also "Real-time ML is challenging to get right." The post dates its launch article to September 2017 (not read). [pre-2020]
- 2 May 2024 ([From Predictive to Generative](https://www.uber.com/en-GB/blog/from-predictive-to-generative-ai)): "approximately 400 active ML projects are managed on Michelangelo, with over 20K model training jobs monthly. There are more than 5K models in production, serving 10 million real-time predictions per second at peak." DeepETA "has more than one hundred million parameters and was trained over one billion trips." The platform has a control plane and offline and online data planes. Deep learning reached "more than 60%" of tier-1 projects.
- 9 Jan 2025 ([Ray post](https://www.uber.com/en-SA/blog/how-uber-uses-ray-to-optimize-the-rides-business), read via Wayback): "performance improvements of up to 40 times"; "about a 40-time improvement for our budget allocation optimizer." Each city optimization "takes about 1-2 seconds to finish."
- Conflict: ZenML summaries say "60 million peak predictions per second" and "150 million monthly active users" ([ZenML summary](https://www.zenml.io/mlops-database/uber-michelangelo-modernization-ray-on-kubernetes-michelangelo-modernization-evolving-an-end-to-end-ml-platform-from-tre)). Uber's 2024 post says 10 million and 137 million. Use Uber's post.

**Stripe Radar**
- 18 Apr 2018 ([Radar 2.0](https://stripe.com/en-in/blog/radar-2018)): "Hundreds of new signals for improved accuracy." Some signals "process hundreds of billions of historical events." "In early testing, the upgraded machine learning models helped reduce fraud by over 25% compared to previous models, without increasing the false positive rate." A card new to a business has "an 89% chance it's been seen before on the Stripe network." [pre-2020]
- Latency: Stripe's guide says Radar "analyses hundreds of signals per transaction ... and produces a risk score in milliseconds" ([Stripe guide](https://stripe.com/resources/more/ai-for-fraud-detection), undated). This is a guide, not an SLO.
- Score scale: "a score of 65 or above indicates elevated risk, while a score of 75 or above indicates high risk." Scores run 0 to 99 ([Radar risk evaluation](https://docs.stripe.com/radar/risk-evaluation), undated).
- 15 May 2025 ([Payments Intelligence Suite](https://stripe.com/blog/using-ai-optimize-payments-performance-payments-intelligence-suite)): the Payments Foundation Model is "trained on tens of billions of transactions" and "distills almost everything about each payment on Stripe down to a single, versatile embedding." Card-testing attacks "are down 80% on Stripe." "By classifying sequences of embeddings, our detection rate for attacks on large users significantly increased from 59% to 97% overnight." (Dashes removed from the quote.) The named hard problem: "novel attack types that fraudulent actors sprinkle across the volumes of the world's biggest companies." These are vendor-reported figures.
- Label delay: the dispute windows above. No Stripe page I read explains how Radar matures labels for training.

**Airbnb search ranking** (arXiv v2, 24 Oct 2018; KDD 2019 per a secondary index)
- "Much of the initial gains were driven by a gradient boosted decision tree model. The gains, however, plateaued over time." ([Haldar et al., arXiv 1810.09591](https://arxiv.org/pdf/1810.09591))
- Scale: no QPS number in my extraction. The named problem is label sparsity: "Even the most popular listing can be booked at most 365 times in an entire year. Typical bookings per listing are much fewer."
- Latency: the paper describes a "strict latency" constraint. No number was extracted.

**YouTube recommendations** (RecSys 2016, 15-19 Sep 2016)
- Scale: "helping more than a billion users." The models "learn approximately one billion parameters and are trained on hundreds of billions of examples" ([Covington et al.](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/45530.pdf)).
- Pipeline: candidate generation picks "hundreds of videos" from millions. Ranking uses "hundreds of features."
- Named problem: "We rarely obtain the ground truth of user satisfaction and instead model noisy implicit feedback signals."
- Latency: "tens of milliseconds" (above).

**Pinterest PinSage** (arXiv 6 Jun 2018; KDD 2018 per arXiv comment)
- Scale: "billions of items and hundreds of millions of users"; the system was "developed and deployed at Pinterest" ([Ying et al., arXiv 1806.01973](http://arxiv.org/abs/1806.01973)).
- Model: graph convolution with random walks, trained on "harder-and-harder training examples." The named problem is making GCNs "practical and scalable to web-scale recommendation tasks." Latency is not in the abstract.

**Meta: EBR and DLRM**
- EBR: "Embedding-based Retrieval in Facebook Search" (arXiv 20 Jun 2020; "to be published in KDD '20"). Facebook search "was still mainly based on a Boolean matching model." The system serves EBR "based on an inverted index," with "ANN parameter tuning" ([Huang et al., arXiv 2006.11632](http://arxiv.org/abs/2006.11632)).
- DLRM: the named problem is embedding memory (above). Scale is not in the abstract.

**LinkedIn LiRank** (arXiv 10 Feb 2024)
- Feed, Jobs and Ads CTR. Relative A/B results: "+0.5% member sessions in the Feed, +1.76% qualified job applications ..., and +4.3% for Ads CTR" ([arXiv 2402.06859](https://arxiv.org/abs/2402.06859)). Calibration is one of the named techniques.

**DoorDash ETA** (1 Oct 2024, [DoorDash](https://careersatdoordash.com/blog/deep-learning-for-smarter-eta-predictions/))
- "At DoorDash, where we handle over 2 billion orders annually." The model is an "MLP-gated mixture of experts" with "DeepNet, CrossNet, and transformer" encoders, plus multitask learning and probabilistic forecasts.
- "A remarkable 20% relative improvement in ETA accuracy." "When the Delivery network is extremely busy, the relative accuracy improvement soars to around 20%."
- The March 2024 post ([Improving ETAs](https://careersatdoordash.com/blog/improving-etas-with-multi-task-models-deep-learning-and-probabilistic-forecasts/)) returned an empty body in my fetch. Not read.

**Netflix artwork** (page dated 7 Dec 2017)
- "a diverse member base spanning over a hundred million accounts." Contextual bandits pick artwork per member. The named problem is that one best image per title does not fit diverse tastes. [pre-2020]

**Classic ads CTR**
- McMahan et al. (KDD 2013): calibration layer, quoted above. [pre-2020]
- He et al., "Practical Lessons from Predicting Clicks on Ads at Facebook" (ADKDD 2014, 24-27 Aug 2014). The main metrics are "Normalized Entropy (NE) and calibration". "well-calibrated prediction of CTR is essential to the success of online bidding and auction." Data freshness is named as a key lesson ([He et al. PDF](https://quinonero.net/Publications/predicting-clicks-facebook.pdf)). [pre-2020]

### Inferences
- Uber's 2024 post gives the most concrete recent scale numbers. Use Uber's own post, not secondary summaries.
- Stripe's public latency language is "milliseconds" with no SLO. Expect an interviewer to push on the authorization window.

### Gaps
- Airbnb QPS and latency numbers. Stripe p99 or SLO. Netflix recommendation posts after 2017. Uber's 2017 original Michelangelo post. The DoorDash March 2024 post.

## Relevance to payments and risk (learner profile)

This section is inference, except where a source is linked. These are the topics most likely in a Stripe or payments-risk loop, roughly in order.
1. Delayed labels. Chargebacks take months. Early fraud warnings arrive sooner, but only about 40% of Visa and Mastercard EFWs become disputes ([Stripe disputes](https://docs.stripe.com/disputes/how-disputes-work.md)). That makes them a noisy proxy label (my inference).
2. Time-based splits and leakage. Rules #33 applies directly to fraud data ([Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml)).
3. Class imbalance and precision guardrails. Hello Interview's harmful-content case uses a 95% precision guardrail ([Hello Interview](https://www.hellointerview.com/learn/ml-system-design/problem-breakdowns/harmful-content)). A fraud decline threshold has the same shape.
4. Calibration and thresholds. Stripe's 0 to 99 score uses cutoffs at 65 and 75 ([Radar risk evaluation](https://docs.stripe.com/radar/risk-evaluation)). A calibrated score makes those cutoffs meaningful.
5. Point-in-time features. Velocity and history features must be as of the transaction time ([Feast docs](https://docs.feast.dev/getting-started/concepts/point-in-time-joins)).
6. Feedback loops. Declines change which transactions get labelled ([Chaney et al.](http://arxiv.org/abs/1710.11214); [NIPS 2015](https://papers.nips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf)).
7. Adversarial drift. Card testing shifts quickly ([Stripe, 15 May 2025](https://stripe.com/blog/using-ai-optimize-payments-performance-payments-intelligence-suite)). Drift tests and shadow runs matter.
8. Latency budget. Stripe's guide uses "milliseconds" and a "card authorization window" ([Stripe guide](https://stripe.com/resources/more/ai-for-fraud-detection)). No public Stripe SLO.
9. Policy layer. Rules #15 ("Separate Spam Filtering and Quality Ranking in a Policy Layer") matches a risk team that combines rules and models. This is close to a ride-sharing risk background.

## Lab ideas from this topic

Each lab fits in about one hour. Check each dataset's license before reuse.

1. **Random split vs time split (label leakage).** Concept: time-based split and leakage (Rules #33; Covington et al. 2016). Dataset: [MovieLens 32M](https://grouplens.org/datasets/movielens/32m/), 32 million ratings, 87,585 movies and 200,948 users, released 05/2024. Check the README for the timestamp column and license ([GroupLens](https://grouplens.org/datasets/movielens/)). Outcome: a random split gives a visibly higher hit@10 or NDCG@10 than a time split. The gap is the leakage.
2. **Training-serving skew replay.** Concept: skew (Rules #29 and #37). Dataset: [NYC TLC trip records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), monthly Parquet files. Compute one feature, such as trips per zone in the last hour, two ways: a batch version and a serving version with a different window boundary or timezone. Outcome: count the rows where the values differ, and measure the AUC change on each version.
3. **As-of join vs latest-value join.** Concept: point-in-time joins ([Feast docs](https://docs.feast.dev/getting-started/concepts/point-in-time-joins)). Dataset: MovieLens 32M. Feature: a movie's mean rating. Version A uses only ratings before each row's timestamp. Version B uses the final mean. Outcome: version B gives an inflated offline AUC. Explain why in one paragraph.
4. **Two-stage retrieval plus re-ranker.** Concept: two-stage design (Covington et al. 2016; LiRank). Dataset: MovieLens 32M. Build candidates with embeddings and an ANN index ([FAISS](http://arxiv.org/abs/1702.08734) or [HNSW](https://arxiv.org/abs/1603.09320)). Re-rank 100 candidates with a gradient-boosted model. Outcome: recall@100 of the candidate stage, NDCG@10 after re-ranking, and p50 and p99 latency per request.
5. **ANN recall vs latency.** Concept: ANN trade-offs ([FAISS](http://arxiv.org/abs/1702.08734), [HNSW](https://arxiv.org/abs/1603.09320), [ScaNN](http://arxiv.org/abs/1908.10396)). Dataset: 1 million synthetic vectors, or the item embeddings from lab 4. Outcome: a recall@10 vs p99 latency curve, with the knee marked. Compare exact search with the ANN index.
6. **Calibration and threshold.** Concept: calibration ([Guo et al.](http://arxiv.org/abs/1706.04599); [scikit-learn](https://scikit-learn.org/stable/modules/calibration.html)). Dataset: [ULB credit card fraud on Kaggle](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud). Read the description first, because my counts for it are [unverified]. Outcome: a reliability curve, and a lower Brier score on held-out data after temperature or isotonic calibration.
7. **Imbalance and precision guardrail.** Concept: downsampling and upweighting ([Google crash course](https://developers.google.com/machine-learning/crash-course/overfitting/imbalanced-datasets); Rules #30). Dataset: same as lab 6. Train with no weighting, class weights, and downsampling with upweighting. Outcome: recall at a fixed 95% precision, and how calibration shifts after downsampling.
8. **Drift detection on shifted months.** Concept: covariate shift (Rabanser et al. 2018). Dataset: NYC TLC, two months far apart, such as a winter and a summer month. Run a KS test per feature and a domain classifier. Outcome: real shift is flagged, and a control split of the same month is not. Record the false alarm rate.
9. **Delayed-label maturity.** Concept: delayed labels ([Stripe disputes](https://docs.stripe.com/disputes/how-disputes-work.md), 120-day window). Dataset: lab 6 data, with simulated label delays of 30, 60 and 120 days. Train on mature labels only, then with immature negatives counted as negatives. Outcome: recall on the most recent cohort drops when immature rows are used as negatives.
10. **A/B power and A/A test.** Concept: A/B tests and canaries ([SRE Workbook](https://sre.google/workbook/canarying-releases/); [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.power.NormalIndPower.html)). Dataset: none, synthetic. Compute sample size for a 2% baseline and a 5% relative lift. Then run 1,000 simulated A/A tests. Outcome: sample size per arm, and an A/A false positive rate near 5%. Show that a smaller test is underpowered.
11. **Latency budget with shadow traffic.** Concept: shadow deployment ([SageMaker shadow tests](https://docs.aws.amazon.com/sagemaker/latest/dg/shadow-tests.html)) and latency budgets ([Covington et al.](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/45530.pdf), "tens of milliseconds"). Dataset: any tabular model from lab 6. Serve a champion and a shadow challenger in one process. Outcome: p50 and p99 per request, the latency the shadow call adds, and the disagreement rate between the two models.
12. **LLM judge agreement.** Concept: LLM evals ([Shankar et al. 2024](https://arxiv.org/abs/2404.12272)). Dataset: 50 model outputs that you label yourself. Measure agreement between an LLM judge and your labels for two judge prompts. Outcome: agreement rate per prompt, and tokens per judged item. Keep the disagreements and read them.

## Sources

| URL | What it supports | Date |
|---|---|---|
| https://www.metacareers.com/ML-prep-onsite/ | Meta loop of up to six 45-minute conversations | Undated (read 17 Oct 2026) |
| https://www.metacareers.com/hiring-process/ | Fetched, no readable text (gap) | Undated |
| https://stripe.com/guides/atlas/scaling-eng | Stripe rubrics and Bug Squash; no system design text | Undated (footer 2026) |
| https://www.uber.com/blog/navigating-uber-engineering-interviews/ | Exists; no readable text (gap) | Undated |
| https://www.google.com/about/careers/applications/how-we-hire/ | Exists; no ML text in my copy (gap) | Undated |
| https://www.hellointerview.com/learn/ml-system-design | Senior-level claim; interview types; evaluation areas | Undated (early access) |
| https://www.hellointerview.com/learn/ml-system-design/problem-breakdowns/harmful-content | Harmful content constraints: 50k labels, under 1% positives, 95% precision | Undated |
| https://bytebytego.com/courses/machine-learning-system-design-interview | 11 case-study chapters | Undated |
| https://raw.githubusercontent.com/chiphuyen/dmls-book/main/README.md | Designing ML Systems, 2022 | 2022 (README) |
| https://raw.githubusercontent.com/chiphuyen/dmls-book/main/summary.md | Designing ML Systems chapter names | Undated |
| https://github.com/chiphuyen/aie-book | AI Engineering chapter questions | Undated (edition not verified) |
| https://github.com/GoogleCloudPlatform/ml-design-patterns | 30 ML design patterns | Undated (book year not verified) |
| https://developers.google.com/machine-learning/guides/rules-of-ml | Rules of ML, 43 rules | Last updated 25 Aug 2025 |
| https://papers.nips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf | Hidden technical debt, glue code, feedback loops | NIPS 2015 |
| http://arxiv.org/abs/2209.09125 | Operationalizing ML, 18 MLE interviews | 16 Sep 2022 |
| https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/ | 28 tests and monitoring needs | IEEE Big Data 2017 |
| https://research.google/pubs/data-validation-for-machine-learning/ | Training-serving skew as a challenge | SysML 2019 (to appear) |
| https://docs.feast.dev/getting-started/concepts/point-in-time-joins | Point-in-time correct joins | Undated |
| https://scikit-learn.org/stable/common_pitfalls.html | Data leakage definition | Undated (current docs) |
| https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/45530.pdf | YouTube: two-stage, scale, latency, leakage | RecSys 2016, 15-19 Sep 2016 |
| https://developers.google.com/machine-learning/crash-course/overfitting/imbalanced-datasets | Downsampling and upweighting | Undated |
| https://docs.stripe.com/disputes/how-disputes-work.md | Dispute windows; early fraud warning conversion | Undated |
| http://arxiv.org/abs/1810.11953 | Covariate and label shift definitions; shift tests | arXiv 29 Oct 2018; NeurIPS 2019 |
| https://arxiv.org/abs/2004.05785 | Concept drift definition (review) | arXiv 13 Apr 2020 |
| https://arxiv.org/pdf/1810.09591 | Airbnb search: 365 bookings; offline vs online | arXiv v2 24 Oct 2018; KDD 2019 (venue unverified) |
| http://arxiv.org/abs/1706.04599 | Calibration; temperature scaling | arXiv 14 Jun 2017; ICML 2017 |
| https://scikit-learn.org/stable/modules/calibration.html | Calibration definition | Undated |
| https://research.google.com/pubs/archive/41159.pdf | Ad CTR calibration layer (McMahan et al.) | KDD 2013, 11-14 Aug 2013 |
| https://quinonero.net/Publications/predicting-clicks-facebook.pdf | Normalized entropy, calibration, freshness (He et al.) | ADKDD 2014, 24-27 Aug 2014 |
| https://docs.aws.amazon.com/sagemaker/latest/dg/shadow-tests.html | Shadow testing definition | Undated (vendor docs) |
| https://sre.google/workbook/canarying-releases/ | Canary as A/B testing | Undated (SRE Workbook) |
| https://www.statsmodels.org/stable/generated/statsmodels.stats.power.NormalIndPower.html | Power and sample size for two-sample tests | Undated (docs) |
| http://arxiv.org/abs/1702.08734 | FAISS; 55% of peak | arXiv 28 Feb 2017 |
| http://arxiv.org/abs/1908.10396 | ScaNN; maximum inner product search | arXiv 27 Aug 2019 |
| https://arxiv.org/abs/1603.09320 | HNSW graph ANN | arXiv (2016 by ID; API date not returned) |
| https://arxiv.org/pdf/1906.00091 | DLRM; embedding memory | arXiv 31 May 2019 |
| https://arxiv.org/abs/2402.06859 | LiRank; A/B results; calibration; compression | arXiv 10 Feb 2024 |
| http://arxiv.org/abs/1710.11214 | Algorithmic confounding; feedback loop | arXiv 30 Oct 2017 |
| https://netflixtechblog.com/artwork-personalization-c589f074ad76 (read via web.archive.org) | Artwork personalization; new-title framing | Page dated 7 Dec 2017 |
| https://arxiv.org/abs/2404.12272 | LLM judges need human validation (EvalGen) | arXiv 18 Apr 2024 |
| http://arxiv.org/abs/1806.01973 | PinSage; billions of items | arXiv 6 Jun 2018; KDD 2018 |
| http://arxiv.org/abs/2006.11632 | Embedding-based retrieval in Facebook search | arXiv 20 Jun 2020; KDD 2020 |
| https://www.uber.com/blog/scaling-michelangelo/ | Michelangelo 2018 numbers and hardest problem | 2 Nov 2018 |
| https://www.uber.com/en-GB/blog/from-predictive-to-generative-ai | Michelangelo 2024: 10M predictions per second; DeepETA | 2 May 2024 |
| https://www.uber.com/en-SA/blog/how-uber-uses-ray-to-optimize-the-rides-business | Ray: up to 40x | 9 Jan 2025 |
| https://stripe.com/en-in/blog/radar-2018 | Radar 2.0: signals; 25% fewer frauds; 89% | 18 Apr 2018 |
| https://stripe.com/resources/more/ai-for-fraud-detection | Radar risk score "in milliseconds" (guide) | Undated |
| https://docs.stripe.com/radar/risk-evaluation | Score 0 to 99; cutoffs 65 and 75 | Undated |
| https://stripe.com/blog/using-ai-optimize-payments-performance-payments-intelligence-suite | Payments Foundation Model; 59% to 97%; 80% down | 15 May 2025 |
| https://careersatdoordash.com/blog/deep-learning-for-smarter-eta-predictions/ | DoorDash ETA: 2B orders; 20% accuracy | 1 Oct 2024 |
| https://careersatdoordash.com/blog/improving-etas-with-multi-task-models-deep-learning-and-probabilistic-forecasts/ | Not read (empty body in fetch) | Mar 2024 (per search result) |
| https://grouplens.org/datasets/movielens/32m/ | MovieLens 32M size and dates | Collected 10/2023; released 05/2024 |
| https://grouplens.org/datasets/movielens/ | Dataset index; read README for license | Undated |
| https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page | TLC trip records; monthly Parquet | Undated (mentions 2025 data) |
| https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud | ULB fraud dataset page (description not extracted) | Undated |
| https://www.zenml.io/mlops-database/uber-michelangelo-modernization-ray-on-kubernetes-michelangelo-modernization-evolving-an-end-to-end-ml-platform-from-tre | Secondary Uber summary; conflicting figures | Undated (secondary) |

## Conflicts and open questions

- Uber peak predictions: Uber's 2024 post says 10 million per second. The [ZenML summary](https://www.zenml.io/mlops-database/uber-michelangelo-modernization-ray-on-kubernetes-michelangelo-modernization-evolving-an-end-to-end-ml-platform-from-tre) says 60 million. A second ZenML page in search results says 10 million, and a search summary cited 30 million for "2026 coverage" (not read). Use Uber's post.
- Uber users and trips: the ZenML summary says 150 million monthly active users and 28 million trips a day. Uber's 2024 post says 137 million and 25 million. Use Uber's post.
- Uber 2026 Kubernetes rebuild: only search results were seen, not read ([Let's Data Science](https://letsdatascience.com/news/uber-migrates-michelangelo-platform-to-kubernetes-foundation-914e2007); [The New Stack](https://thenewstack.io/uber-standardized-ml-scale/)). Dates and claims are [unverified].
- Airbnb venue: the copy I read is arXiv v2 (24 Oct 2018). KDD 2019 and pages 1927-1935 come from a search summary of DBLP. My DBLP fetch was blocked, and the ACM page did not open. Check the ACM record before you cite it as KDD 2019.
- Stripe card-testing figures (59% to 97%, 80% down): Stripe's own post says them (15 May 2025). They are vendor-reported and not independently tested. Third-party write-ups repeat them.
- Stripe 2018 figures: I used the primary text (25%, 89%, hundreds of signals). Search summaries also gave "four in five", "11%" and "more than 100,000 businesses". None appears in the post I read, so I did not use them.
- Stripe label delay: open. The docs give dispute windows and the early-fraud-warning conversion rate. No Stripe page says how Radar matures labels for training.
- Stripe latency: "in milliseconds" (guide) and "a few milliseconds" for the authorization window (guide). No SLO is public. Open.
- DoorDash: the March 2024 post returned an empty body. The 20% figure is in the October 2024 post, which I read.
- Interview formats: Meta says "up to six 45-minute conversations" and does not name system design. Hello Interview says senior-level ML design is the norm. No company has confirmed these in a primary source. Third-party guides disagree and are anecdotal.
- Concept drift definition: I read Lu et al. (2020). Gama et al. (2014), the classic survey, did not open because the ACM page is blocked.
- ULB fraud dataset: the counts (492 frauds in 284,807 rows, two days, PCA features) come from a search summary of the Kaggle listing. My reader copy did not show the description. A search summary gave a fraud rate of 0.172% in one paper and 0.173% in another. The license name is unclear. Verify before use.
- Kohavi et al. (KDD 2013): the venue and pages come from a search summary. The abstract was not read.
- Book years: Huyen (2022) comes from the repo README. Lakshmanan (2020), Aminian and Xu, and the AI Engineering edition are [unverified]. The O'Reilly tables of contents did not open.
- Rules of ML: the original publication year is not shown. The page was last updated 25 Aug 2025.
- HNSW date: the arXiv API did not return the record, so the year is inferred from the ID.
- Shadow deployment: only vendor docs were read. No research source was found.
- Cold start: no formal primary source was read. The Netflix post only frames the problem.
- LLM cost per request: no sourced figure. Provider pricing pages were not read.
- Hello Interview pages say "early access" and may change.
- Pre-2020 sources kept as classics: Sculley (2015), Covington et al. (2016), McMahan et al. (2013), He et al. (2014), Guo et al. (2017), Chaney et al. (2017), FAISS (2017), PinSage (2018), Radar 2.0 (2018), Netflix artwork (2017), ML Test Score (2017), Failing Loudly (2018), ScaNN (2019), DLRM (2019), Data Validation (2019). Check their numbers against newer work before quoting them as current.
