# 18. Clustering hygiene: what scaling and outliers do to k-means: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 18'.

- HW: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- Seeds: 0, 1 and 2 for every step (light lane). Seed 0 reproduces the spec's `KMeans(4, n_init=10, random_state=0)`.
- Reference script: `answers/18_clustering_hygiene_ref.py` (script_sha256 `e28d8e294650cd49`). Raw seed-0 output: `answers/18-clustering-hygiene.out`.
- Runs and wall times (s): baseline 15.6, 8.3, 12.3; change 12.8, 8.5, 10.1; break 12.7, 9.6, 9.9 (seeds 0, 1, 2).
- Tolerance rule: tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step.
- Effects (mean over seeds, against the larger of the two spreads): `P2.biggest_share:P1.biggest_share` -0.16049233333333338, spread 0.008004999999999929, ok. `P3.biggest_share:P1.biggest_share` 0.243901, spread 0.008004999999999929, ok.

<details><summary>P1. Share of customers in the biggest of k = 4 clusters, scaled RFM, all customers</summary>

**Answer:** 0.72484 at seed 0. Tolerance (seed spread) 0.008004999999999929, about 0.008.

Seed-0 RESULT lines:

```
RESULT baseline.n_customers=4372 unit=customers seed=0
RESULT baseline.sizes=3169/1087/110/6 unit=customers seed=0
RESULT P1.biggest_share=0.72484 unit=fraction seed=0
RESULT baseline.silhouette=0.611331 unit=score seed=0
RESULT baseline.inertia_k2=9204.01 unit=sum_sq seed=0
RESULT baseline.inertia_k3=5527.71 unit=sum_sq seed=0
RESULT baseline.inertia_k4=4046.64 unit=sum_sq seed=0
RESULT baseline.inertia_k5=3020.25 unit=sum_sq seed=0
RESULT baseline.inertia_k6=2383.6 unit=sum_sq seed=0
RESULT baseline.inertia_k7=1906.34 unit=sum_sq seed=0
RESULT baseline.inertia_k8=1585.88 unit=sum_sq seed=0
```

Other seeds: `P1.biggest_share` 0.732845 (seed 1) and 0.72484 (seed 2). Sizes 3204/1092/70/6 (seed 1) and 3169/1087/110/6 (seed 2). Silhouette 0.605631 and 0.611331. Inertia at k = 4: 4065.07 and 4046.64.

**Why:** k-means places its centres where they cut the most squared distance, and `StandardScaler` puts the columns on one scale without shortening their tails, so a few accounts with huge spend and very many invoices still sit far from everyone else. Two of the four centres therefore go to small groups of extreme customers (the 110 and 6 in 3169/1087/110/6), and the other customers are split only in two, mostly active against lapsed. The inertia curve bends once, at k = 3: the drop from k = 2 to k = 3 (9134.64 to 5527.7 at seeds 1 and 2; seed 0 stopped at a worse k = 2 optimum, 9204.01) is more than twice any later drop. From the k = 4 to k = 5 drop on, each drop is about 0.6 to 0.75 of the one before. k = 4 sits past the bend, on the flatter part of the curve, so the elbow alone does not pick it: justify it with the silhouette, stability across seeds and how many tiers the team can act on.

**Common wrong prediction:** about 0.25 to 0.4, from the picture that scaling makes four roughly equal segments.

</details>

<details><summary>P2. Drop cancellations and the top 1% of spenders, then re-cluster: biggest-cluster share, direction and size</summary>

**Answer:** down, by about 0.16. `P2.delta_share` is -0.156272 at seed 0 (tolerance 0.008937), from 0.72484 to 0.568568. `P2.biggest_share` tolerance 0.0037249999999999783.

Seed-0 RESULT lines:

```
RESULT change.n_customers=4295 unit=customers seed=0
RESULT change.sizes=2442/1027/688/138 unit=customers seed=0
RESULT P2.biggest_share=0.568568 unit=fraction seed=0
RESULT P2.delta_share=-0.156272 unit=fraction seed=0
RESULT change.silhouette=0.509394 unit=score seed=0
```

Other seeds: `P2.biggest_share` 0.567637 (seed 1) and 0.564843 (seed 2). `P2.delta_share` -0.165209 and -0.159997. Sizes 2438/1025/694/138 and 2426/1027/704/138. Silhouette 0.508967 and 0.508376.

**Why:** with shorter tails, the four centres move into the bulk: a frequent, mid-spend tier of 688 appears and the biggest cluster shrinks. This run changes both edits at once and no run isolates them, so who each edit removes comes from the cluster profiles: the top-1% cut takes the whole 6-customer cluster and thins the heavy-buyer cluster of 110, and dropping cancellations takes out negative money and the customers who only ever cancelled (4295 customers remain of 4372). The silhouette falls from 0.611331 to 0.509394, but not because the extreme clusters scored well: in the baseline they had the lowest silhouettes of the four, and the two bulk clusters carried the score. It falls because the four centres now cut the dense bulk into more tiers, so more customers sit near a boundary. So cleaning gives a more balanced and more granular segmentation at a lower silhouette. Sizes and silhouette describe the shape of the clusters, not their value: whether the new tiers are more useful needs a downstream check, for example whether they differ in later spend or churn, or whether the team can act on each one.

**Common wrong prediction:** "same, give or take", because 1% of customers sounds too small to matter. The 1% held one whole cluster and part of another.

</details>

<details><summary>P3. Skip scaling (raw RFM): biggest-cluster share</summary>

**Answer:** 0.972553 at seed 0. Tolerance (seed spread) 0.003430999999999962, about 0.003.

Seed-0 RESULT lines:

```
RESULT break.n_customers=4372 unit=customers seed=0
RESULT break.sizes=4252/102/15/3 unit=customers seed=0
RESULT P3.biggest_share=0.972553 unit=fraction seed=0
RESULT break.silhouette=0.884206 unit=score seed=0
```

Other seeds: `P3.biggest_share` 0.969122 (seed 1) and 0.972553 (seed 2). Sizes 4237/117/15/3 and 4252/102/15/3. Silhouette 0.878134 and 0.884206.

**Why:** on raw RFM, `monetary` is in pounds and its spread dwarfs the spread of days and invoice counts, so squared Euclidean distance is almost all money. k-means then cuts the money axis into bands: everyone except the biggest spenders lands in one cluster, and three clusters (102, 15 and 3 customers) hold the big accounts. Recency and frequency play almost no part. The silhouette is the highest of the three runs (0.884206) because it is measured in the raw space, where those money bands are far apart: a high silhouette there scores separation on one axis, not a useful segmentation.

**Common wrong prediction:** about 0.5 to 0.7, from the idea that unscaled k-means is only a little worse than scaled.

</details>

<details><summary>Rebuild check</summary>

Solution: `answers/rebuild/18_kmeans.py` (`standardize()` and `kmeans()`, 16 lines of body). Stub: `m3-more-of-the-map/rebuild/18_kmeans.py`.

`rebuildcheck` verdict: the stub fails as it should (exit 1, NotImplementedError), the solution passes (exit 0, `check: PASS`): REBUILDCHECK OK. `check()` compares `standardize()` with `StandardScaler` and the inertia of `kmeans()` with scikit-learn `KMeans(init=<the same rows>, n_init=1, tol=0.0, algorithm="lloyd")` for k = 3, 4 and 5 on a 180-row, three-blob fixture, relative difference under 1e-6.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 18-M | 18 | M | Why does k-means on raw recency (days), frequency (invoices) and monetary (pounds) end up splitting customers by spend alone? |
| 18-N | 18 | N | Online Retail, RFM scaled with StandardScaler, all 4,372 customers, k = 4: what share of customers sat in the biggest cluster, and why is it far from 0.25? |
| 18-D | 18 | D | A teammate's k = 4 customer segmentation puts nearly every customer in one cluster, the other three hold a handful each, and the silhouette is high. What do you check first? |
| 18-T | 18 | T | Payments version: k-means risk tiers for merchants on two raw columns, monthly card volume in cents and dispute rate as a fraction. What do the tiers end up measuring, and what do you change before clustering? |

18-T is a spare. The quiz rules alternate T and D from one close to the next, so draft 18-T in place of 18-D when the previous close drafted a D card.

Keys:

- 18-M: (1) k-means minimizes squared Euclidean distance, so the column with the largest numeric spread dominates it. (2) Money in pounds spreads far wider than days or invoice counts.
- 18-N: (1) About 0.72 (0.72484 at seed 0, 0.732845 at seed 1). Count a recall from 0.70 to 0.75 as a hit. (2) Two of the four centres went to small groups of extreme accounts (sizes 3169/1087/110/6), so the bulk was split only in two. (3) Scaling does not remove outliers.
- 18-D: must mention (1) Whether the features were scaled: look at each column's units and spread. Follow-ups, not needed for a hit: (2) Whether a few extreme customers or cancellations own the small clusters: cluster sizes and per-cluster means. (3) Silhouette is measured in the space that was clustered, so a high score on unscaled data is separation on the money axis only.
- 18-T: (1) Volume only: squared distance adds raw squared gaps, and volume in cents spreads many orders of magnitude wider than a rate below 1, so the tiers are volume bands and the dispute rate, the risk signal, barely counts. (2) Scale both columns to one spread, for example with StandardScaler. (3) Scaling keeps the long tail of volume, so log or cap it first, or the biggest merchants get tiers of their own.

</details>

<details><summary>Build notes</summary>

**Knob changes:** none. Both effects clear 2x the seed spread at the spec's configuration: P2 against P1 is -0.16049233333333338, P3 against P1 is 0.243901, and the larger spread is 0.008004999999999929.

**Precomputed steps:** none. The longest seed-0 measured run is the baseline at 15.6 s.

**Deviations from the spec, and choices where it is silent:**

1. Interview question, reworded in the lab file. The spec's wording, "Segment about 4,000 customers into risk tiers without labels: why does unscaled k-means put most of them in one cluster, and how do you choose k?", states the size of the P3 answer, which the spoiler gate forbids in a lab file. The lab file asks "what does skipping feature scaling do to k-means, and how do you choose k?".
2. Cleaning order. The spec says "drop cancellations and the top 1% of spenders". The build drops the cancellation lines first, rebuilds RFM from the rest, then keeps customers with `monetary <= quantile(0.99)` of that table. This is the simplest reading. Customers who only ever cancelled drop out because no lines remain for them.
3. Silhouette sample. The spec says a 5,000-row sample, but there are 4372 customers (4295 after cleaning), so `silhouette_score(sample_size=min(5000, n))` scores every customer. The seed only changes their order, not the value. Each silhouette is computed in the space k-means saw: scaled for baseline and change, raw for break.
4. The elbow (inertia for k = 2 to 8) runs in `--baseline` only, on the spec's main configuration (scaled, all customers).
5. Download. The workbook is read once with InvoiceNo, StockCode and Description as text, because InvoiceNo mixes numbers with C-prefixed strings and one parquet column cannot hold both. The spec estimated 1 to 2 minutes for the conversion. On this Mac the fetch plus the conversion took under a minute, so the lab says "about a minute".
6. `<mode>.sizes` is a text RESULT value (sizes joined by "/"), so mkanswers gives it no spread.
7. Rebuild. The spec says the check uses "the same initial centres". The stub's docstring fixes the rule (rows `np.random.default_rng(seed).choice(len(X), size=k, replace=False)` of X), so `check()` can hand the same rows to scikit-learn. The fixture never empties a cluster: there scikit-learn relocates the centre, while the spec's rule keeps it, so `check()` does not test that branch.
8. Level S starter. `--smoke` sends random points through `report()` for all three steps (a stand-in, with one comment saying smoke checks the plumbing only). The measured modes raise `NotImplementedError("write the harness: see the lab file")`.
9. Where the spread comes from. All customers are clustered, so the only random choice is KMeans's k-means++ start. Seed 1 found a different local optimum for the baseline (3204/1092/70/6, inertia at k = 4 of 4065.07 against 4046.64) even with n_init=10, and seed 0 found a worse k = 2 optimum (9204.01 against 9134.64). This is k-means on long tails, not a bug.
10. Customer count. The spec's dataset field gives the customer count, which the script prints as `baseline.n_customers`, so the Dataset line leaves it out and keeps the published invoice-line count only. The Goal keeps the spec's rounded "about 4,300 customers". No prediction asks for the count.
11. Plots. One scatter per run (recency and frequency against monetary, symlog, one colour and marker per cluster) goes to `~/ml-data/results/lab18/`. Four categorical colours fail the all-pairs normal-vision floor for scatter plots, so each cluster also gets its own marker shape.
12. `kmeans()` moved from the session to the rebuild. The spec's learner_builds has the learner write `kmeans()` from the README formula during the session. The lab runs scikit-learn's `KMeans(n_clusters=4, n_init=10, random_state=seed)` in the harness instead. Every Predict row names that one call, so the learner's runs repeat the reference configuration and the seed spread stays a fair tolerance. A hand-written Lloyd's loop with its own starts can stop at other local optima (note 9). The 10-minute baseline slot also has no room for a third write-first piece after the prompt and `rfm()`. The learner still writes the RFM definition and the cleaning rule in the session, and writes `standardize()` and `kmeans()` from memory at the rebuild, where `check()` compares them with scikit-learn from the same initial centres.
13. Checks behind the P1 and P2 Whys. These ran read-only at seed 0, with the reference's own `rfm()`, `clean()`, `StandardScaler` and `KMeans` call, outside the ledger, so their values are not recorded here. Per-customer `silhouette_samples`: the baseline's two small clusters have the lowest mean silhouettes of its four, and on the cleaned, scaled table the silhouette falls step by step as k goes from 2 to 4. Cluster membership: the top-1% cut removes every customer of the 6-customer cluster and part of the 110-customer one, and the customers who only ever cancelled sit mostly in the lapsed cluster. No check isolated each edit's part of the P2 effect. The elbow reading in P1 uses only the recorded inertias.
14. Title, reworded. The spec's title, "Clustering hygiene: scaling and outliers decide k-means", tells the learner that both edits change the clusters a lot, a hint at the size of the P2 and P3 answers. The lab file, its row in the module README, both scripts' docstrings and this file use "Clustering hygiene: what scaling and outliers do to k-means". The docstring edit changed the reference's hash, so all nine reference runs were repeated: every RESULT line came back the same, and only the wall times differ.

**Prototype comparison:** the spec gives no `[answers only]` prototype values for this lab (none in `spec/labs/18.json`, `spec-detailed.json` or the research report's row for old lab 16), so there is nothing to compare. As a check on the mechanism instead, the seed-0 plots and cluster profiles agree with the explanations above: the raw clusters are money bands, and the scaled clusters split active from lapsed customers plus heavy buyers and the largest accounts.

</details>
