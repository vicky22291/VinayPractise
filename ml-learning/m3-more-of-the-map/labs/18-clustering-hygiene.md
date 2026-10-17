# 18. Clustering hygiene: what scaling and outliers do to k-means

> Goal: after this I can segment about 4,300 customers by recency, frequency and monetary value (RFM) and show what scaling and cleaning do to cluster sizes. (No result values anywhere in this file.)

**Level:** S (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** `../README.md#clustering-hygiene` (read after the lab; at the rebuild you may open only its Formula block)
**Borrowed from:** Kaggle Learn [Feature Engineering](https://www.kaggle.com/learn/feature-engineering), the lesson "Clustering With K-Means". Do it after the lab, as the second contact 1 to 3 days later.
**Dataset:** Online Retail, dataset 352 of the UCI (University of California, Irvine) Machine Learning Repository, 541,909 invoice lines, 8 columns, one Excel workbook in a 23.7 MB zip, https://archive.ics.uci.edu/dataset/352/online+retail, CC BY 4.0 (Creative Commons Attribution)
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 1 min, at most 6 min per run. Precomputed steps: none
**Needs:** base install only (`openpyxl`, used once to read the workbook, is in it)
**Before the session** (from the module folder, see section 2): `--download` once (it fetches the zip and caches `~/ml-data/online_retail/online_retail.parquet`, about a minute), then `--smoke`.
**Interview question:** Segment about 4,000 customers into risk tiers without labels: what does skipping feature scaling do to k-means, and how do you choose k?
**Repo link:** [`hld/news-aggregator/deep-dives/dedup-and-story-clustering.md`](../../../hld/news-aggregator/deep-dives/dedup-and-story-clustering.md#8-level-5-story-clustering), section 8 "Level 5: story clustering"
**Captured by the script:** every RESULT line of `--baseline`, `--change` and `--break`, plus one scatter plot per run in `~/ml-data/results/lab18/`. **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level S: read `load_data()` and `report()` in `scripts/18_clustering_hygiene.py` for 2 minutes, so you know what each RESULT line measures.

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Share of customers in the biggest of k = 4 clusters. RFM table of all customers with an id, cancellation lines included, scaled with `StandardScaler`, then `KMeans(n_clusters=4, n_init=10, random_state=0)`. A fraction from 0 to 1. | num | | |
| P2 | Drop the cancellation lines (`InvoiceNo` starting with C), rebuild RFM, drop the customers above the 99th percentile of `monetary` (the top 1% of spenders), then fit a fresh `StandardScaler` on the cleaned table and run the P1 `KMeans` call (k = 4, n_init=10, seed 0). Biggest-cluster share vs P1: up, down or same, and by how much (a change in the fraction)? | dir | | |
| P3 | Skip scaling: the same `KMeans` call as P1 on the raw RFM table, all customers, cancellation lines included, seed 0. Share of customers in the biggest cluster, a fraction from 0 to 1. | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m3-more-of-the-map    # from ml-learning/, where sessions start
$ python scripts/18_clustering_hygiene.py --download
$ python scripts/18_clustering_hygiene.py --smoke
```

`--smoke` feeds random points to `report()`. It checks the plumbing, not your code.

## 3. Baseline (0:12, 10 min)

Why: a scaled RFM table cut into k = 4 is the segmentation a first pass ships, and the next two runs are measured against it.

You write two pieces first, no AI. If they run over, the change slot absorbs it: `clean()` is a few lines and `--change` is one short run.

**(a) In this file, no AI (2 min): your harness prompt, 3 to 5 lines.** Open it with "No split: k-means sees every customer with an id." Name the metric: the biggest-cluster share and the silhouette that `report()` prints. Then cover these, briefly:

- The table each mode clusters: `rfm()` of all lines in `--baseline` and `--break`, and the cleaned table from `clean()` (section 4) in `--change`.
- The scaler and the call: a fresh `StandardScaler` fit on the table being clustered, skipped in `--break`, then the `KMeans` call from the P1 row, with `random_state=args.seed`.
- The RESULT contract: `report(mode, X, labels)` in every mode.
- The elbow, in `--baseline` only: the `baseline.inertia_k2` to `baseline.inertia_k8` lines in the Record table (unit `sum_sq`), with the same `KMeans` settings.
- The plot: recency and frequency against monetary, coloured by cluster, saved to `~/ml-data/results/lab18/`.

```
(your prompt: split, metric, RESULT contract)
```

**(b) In `scripts/18_clustering_hygiene.py`, no AI (4 min): `rfm(lines)`.** Drop the lines without a `CustomerID`, then one row per customer:

- `recency`: whole days from the customer's last `InvoiceDate` to 2011-12-10.
- `frequency`: the number of distinct `InvoiceNo`.
- `monetary`: the sum of `Quantity * UnitPrice`, in pounds sterling.

Cancellation lines stay in for this run.

The AI writes the harness only after your prompt block is filled. Before the first run, write a one-line annotation above each block it wrote.

```
$ python scripts/18_clustering_hygiene.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Change: one knob, the cleaning rule. `clean()` drops the cancellation lines and the top 1% of spenders. Then fit a fresh `StandardScaler` on the cleaned table and use the baseline's `KMeans` call. P2 is logged above.

Why: cancellations and the largest accounts are real rows, and this run measures whether, and how much, they shape the segments.

You write `clean(lines)` first, no AI (3 min): drop every line whose `InvoiceNo` starts with C, build the table with your `rfm()`, then drop the customers whose `monetary` is above `quantile(0.99)` of that table. The AI wires it into `--change`.

```
$ python scripts/18_clustering_hygiene.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Break: skip `StandardScaler` and give `KMeans` the raw RFM table of all customers, with the baseline's call. P3 is logged above.

Why: `recency` is in days, `frequency` in invoices and `monetary` in pounds, and this run clusters them in those units.

```
$ python scripts/18_clustering_hygiene.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/18_kmeans.py`, write `standardize()` and `kmeans()` (Lloyd's algorithm) from memory, then run `python rebuild/18_kmeans.py`. Its `check()` compares with scikit-learn's `StandardScaler` and with `KMeans` started from the same initial centres, never with this lab's results. Stuck on Lloyd's two steps? Open only the Formula block under the concept link, safe now that P1 to P3 are logged.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (your line: one or two sentences only someone who ran this would say, with your own numbers)

Staff follow-up (failure modes): the four segments become risk tiers, and the job re-clusters every week. What breaks when a weekly run reshuffles who sits in which tier, and how does the story clusterer in the repo link keep its clusters stable? Answer in 2 sentences from section 8 of the repo link. Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.n_customers`: customers in the baseline table | | | script |
| `baseline.sizes`: cluster sizes, biggest first | | | script |
| `P1.biggest_share`: biggest-cluster share, scaled, all customers | | | script |
| `baseline.silhouette`: silhouette in the scaled space, up to 5,000 customers | | | script |
| `baseline.inertia_k2`: inertia, scaled, k = 2 | | | script |
| `baseline.inertia_k3`: inertia, scaled, k = 3 | | | script |
| `baseline.inertia_k4`: inertia, scaled, k = 4 | | | script |
| `baseline.inertia_k5`: inertia, scaled, k = 5 | | | script |
| `baseline.inertia_k6`: inertia, scaled, k = 6 | | | script |
| `baseline.inertia_k7`: inertia, scaled, k = 7 | | | script |
| `baseline.inertia_k8`: inertia, scaled, k = 8 | | | script |
| `change.n_customers`: customers left after cleaning | | | script |
| `change.sizes`: cluster sizes after cleaning, biggest first | | | script |
| `P2.biggest_share`: biggest-cluster share after cleaning | | | script |
| `P2.delta_share`: P2 minus your P1 (printed when a `--baseline` run exists) | | | script |
| `change.silhouette`: silhouette in the cleaned, scaled space | | | script |
| `break.n_customers`: customers in the raw table | | | script |
| `break.sizes`: cluster sizes on raw RFM, biggest first | | | script |
| `P3.biggest_share`: biggest-cluster share, raw RFM | | | script |
| `break.silhouette`: silhouette in the raw RFM space | | | script |
