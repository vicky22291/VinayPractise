# 04. Text: bag of words vs a pretrained transformer

> Goal: after this I can fine-tune DistilBERT on 2,000 reviews on MPS (Metal Performance Shaders, PyTorch's backend for the Apple GPU, graphics processing unit), compare it with TF-IDF (term frequency times inverse document frequency) plus logistic regression on accuracy and on milliseconds per 1,000 items, and say what word order is worth. (No result values anywhere in this file.)

**Level:** W (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#bag-of-words-vs-transformers`](../README.md#bag-of-words-vs-transformers) (read after the lab)
**Borrowed from:** fast.ai [Lesson 4](https://course.fast.ai/Lessons/lesson4.html) (natural language processing with Hugging Face transformers); fastbook [ch 10](https://github.com/fastai/fastbook/blob/master/10_nlp.ipynb) (a language model fine-tuned on the full IMDB set). Do it after the lab, as the second contact 1 to 3 days later. Both print results for setups close to this lab's, so open them only after your runs. The full-set run on Kaggle is optional and never captured.
**Dataset:** IMDB (Internet Movie Database) reviews, `stanfordnlp/imdb`: 25,000 train and 25,000 test reviews, half positive; train and test parquet 41.45 MB, https://huggingface.co/datasets/stanfordnlp/imdb, Hugging Face licence "other". This lab uses 2,000 training reviews and a fixed 2,000-review test subset, each half positive. Fallback: https://s3.amazonaws.com/fast-ai-nlp/imdb.tgz (144 MB; the same reviews in another order, so other samples). Model: `distilbert/distilbert-base-uncased` (DistilBERT, a smaller distilled copy of BERT, Bidirectional Encoder Representations from Transformers), 268 MB, Apache-2.0
**Runs on:** mps (DistilBERT training; the cost timing runs on the CPU, central processing unit). **Lane:** heavy. **Compute:** 3 runs x at most 3 min (baseline 3, change 1, break 3, rounded up from the seed-0 reference runs), at most 6 min per run. Precomputed steps: none
**Needs:** `python -m pip install transformers==5.20.1`
**Before the session** (from the module folder, see section 2): `python scripts/04_text_bag_of_words_vs_transformer.py --download` (the two IMDB parquet files into `~/ml-data/imdb/`, plus the DistilBERT weights from Hugging Face), then `python scripts/04_text_bag_of_words_vs_transformer.py --smoke` (under a minute). Neither prints a result value: `--smoke` prints `SMOKE <name> ok` lines.
**Interview question:** Categorize 1 M bank-transaction descriptions a day inside a 200 ms budget: TF-IDF plus logistic regression or a transformer, and what does each cost per 1,000 items?
**Repo link:** `hld/quickbooks-ledger/solution.md` [§12 "Presenting this as an Intuit case study"](../../../hld/quickbooks-ledger/solution.md#12-presenting-this-as-an-intuit-case-study), the paragraph "The AI story: one place a model does real work" (bank-transaction categorization that falls back to a rule after 200 ms)
**Captured by the script:** P1 to P3 accuracies, gaps and drops; training seconds for both models in every run (DistilBERT on MPS, synchronized); CPU milliseconds per 1,000 test reviews for both models at 256 and at 32 word pieces; the sampled row ids in `~/ml-data/results/lab04/`. **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

Level W only: before the session, read `scripts/04_text_bag_of_words_vs_transformer.py` (about 10 minutes) and answer its three `# Q:` prompts here. At 0:05 you only predict.

Read `cut`, `train_bert`, `fit_both`, `cpu_cost` and the loop in `main`. `download`, `load_data` and `accuracy` are plumbing you can skip.

- Q1, what `max_length=256` drops (in `cut`):
- Q2, why a learning rate of 5e-5 (in `train_bert`):
- Q3, a test word that no training review has (in `fit_both`):

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range. A point is one percentage point of accuracy (0.01).

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Accuracy gap in points, DistilBERT minus TF-IDF plus logistic regression (`P1.gap_points`), on the fixed 2,000-review test subset. Both models train on the same 2,000 reviews (seed 0), each review cut to its first 256 word pieces ([CLS] and [SEP] count). TF-IDF: scikit-learn `TfidfVectorizer()` defaults (single words) and `LogisticRegression(max_iter=1000)`. DistilBERT: `distilbert-base-uncased`, every weight fine-tuned, AdamW at 5e-5, 2 epochs, batch 16, 10% warm-up, seed 0. | num | | |
| P2 | Cut every review, in training and in test, to its first 32 word pieces instead of 256, for both models, everything else as P1. For each model: accuracy up, down or same vs P1, and by how many points (`P2.tfidf_delta_vs_P1`, `P2.bert_delta_vs_P1`)? | dir | | |
| P3 | The P1 setup, trained on reviews in their normal order. Then shuffle the words of every 256-piece test review and score both models again; neither model is retrained on shuffled text. Which model loses more accuracy (TF-IDF, DistilBERT, or a tie), and by how many points (`P3.tfidf_drop_points`, `P3.bert_drop_points`)? | pick | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m1-whole-game    # from ml-learning/, where sessions start
$ python scripts/04_text_bag_of_words_vs_transformer.py --download
$ python scripts/04_text_bag_of_words_vs_transformer.py --smoke
```

## 3. Baseline (0:12, 10 min)

Why: a word-count model is the bar a transformer has to beat on the same 2,000 reviews, and the CPU cost of each model is half of the interview answer.

```
$ python scripts/04_text_bag_of_words_vs_transformer.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: one knob, how much of each review the models read, changes for both models at once. Bank-transaction descriptions are short, so this input is also closer to the interview's.

Change: cut every review to its first 32 word pieces instead of 256, in training and in test, for both models. P2 is logged above. The two `P2.*_delta_vs_P1` lines print only after a `--baseline` run with the same seed.

```
$ python scripts/04_text_bag_of_words_vs_transformer.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: it measures what word order is worth to each model.

Break: shuffle the words of every test review and score both models again. `--break` first trains both models exactly as `--baseline` does (same seed, reviews in their normal order), then scores the same test reviews twice: in order, and shuffled. P3 is logged above. Start it by 0:34.

```
$ python scripts/04_text_bag_of_words_vs_transformer.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/04_tfidf.py`, write the body of `tfidf` from memory, then run `python rebuild/04_tfidf.py`. Its `check()` compares with scikit-learn's `TfidfVectorizer()` (the same vocabulary in the same order, and the same numbers: exactly on short reviews, within 1e-12 on longer ones), never with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> (one or two sentences only someone who ran this would say)

Staff follow-up (what pages at 3 am): the categorizer in the repo link proposes an account, and when the model has not answered in 200 ms the review list shows the rule-based suggestion instead. What do you page on at 3 am, and what do you leave to a daily report? Answer in 2 sentences from §12 "The AI story". Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `P1.gap_points`: DistilBERT minus TF-IDF accuracy, points, 256 pieces | | | script |
| `baseline.tfidf_accuracy`: fraction, 256 pieces | | | script |
| `baseline.bert_accuracy`: fraction, 256 pieces | | | script |
| `baseline.tfidf_train_s`: s, CPU | | | script |
| `baseline.bert_train_s`: s, MPS, synchronized, 250 steps of batch 16 | | | script |
| `baseline.tfidf_ms_per_1000`: ms per 1,000 test reviews on the CPU, median of 20 batches of 50 | | | script |
| `baseline.bert_ms_per_1000`: ms per 1,000 test reviews on the CPU, median of 20 batches of 50 | | | script |
| `P2.tfidf_accuracy`: fraction, 32 pieces | | | script |
| `P2.bert_accuracy`: fraction, 32 pieces | | | script |
| `P2.tfidf_delta_vs_P1`: points (printed when `--baseline` ran first at the same seed) | | | script |
| `P2.bert_delta_vs_P1`: points (printed when `--baseline` ran first at the same seed) | | | script |
| `change.tfidf_train_s`: s, CPU | | | script |
| `change.bert_train_s`: s, MPS, synchronized | | | script |
| `change.tfidf_ms_per_1000`: ms per 1,000 test reviews on the CPU, 32 pieces | | | script |
| `change.bert_ms_per_1000`: ms per 1,000 test reviews on the CPU, 32 pieces | | | script |
| `P3.tfidf_drop_points`: in order minus shuffled accuracy, points | | | script |
| `P3.bert_drop_points`: in order minus shuffled accuracy, points | | | script |
| `break.tfidf_accuracy`: fraction, in order | | | script |
| `break.tfidf_accuracy_shuffled`: fraction, shuffled | | | script |
| `break.bert_accuracy`: fraction, in order | | | script |
| `break.bert_accuracy_shuffled`: fraction, shuffled | | | script |
| `break.tfidf_train_s`: s, CPU | | | script |
| `break.bert_train_s`: s, MPS, synchronized | | | script |
