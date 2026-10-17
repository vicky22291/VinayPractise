# 38. BPE tokenizer: the merge loop, bytes vs characters

> Goal: after this I can train a byte-level BPE (byte-pair encoding) tokenizer on 1.1 MB of text, measure tokens per 1,000 characters at 0, 256 and 512 merges, and show why byte-level round-trips any string. (No result values anywhere in this file.)

**Level:** W (see `ml-learning/CLAUDE.md`). **Output style:** Explanatory
**Concept link:** [`../README.md#tokenization-and-bpe`](../README.md#tokenization-and-bpe) (read after the lab)
**Borrowed from:** Karpathy, ["Let's build the GPT Tokenizer"](https://www.youtube.com/watch?v=zduSFxRajkE) (2:13:34; GPT is generative pre-trained transformer). This lab is an exception: write P1 to P3 first, then watch the video over 2 evenings before the lab. Raschka, *Build a Large Language Model (From Scratch)*, ch 2 "Working with text data" ([code](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch02)) comes after the lab, as the second contact 1 to 3 days later.
**Dataset:** TinyShakespeare (Karpathy's char-rnn), 1,115,394 characters in 40,000 lines, 1.1 MB, https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt, a subset of Shakespeare's works: the text is public domain, and char-rnn's README says MIT (the repo has no LICENSE file). Lab 39 reads the same file.
**Runs on:** cpu. **Lane:** light. **Compute:** 3 runs x 2 min (baseline, change, break), at most 6 min per run. Precomputed steps: none
**Needs:** base install only
**Before the session** (from the module folder, see section 2): days before, read `scripts/38_bpe_tokenizer.py`, answer its three `# Q:` prompts and write P1 to P3 (section 1 and `../../prediction-log.md`). Then watch the video over 2 evenings. Run `--download` (1.1 MB into `~/ml-data/nanoGPT/data/shakespeare_char/`, shared with lab 39) and `--smoke`.
**Interview question:** Why does the same request cost more tokens in another language or with emoji, and how do token counts set your cost and rate limits?
**Repo link:** [`hld/ai-gateway/deep-dives/token-budgets-and-rate-limiting.md`](../../../hld/ai-gateway/deep-dives/token-budgets-and-rate-limiting.md#2-estimation), §2 "Estimation"
**Captured by the script:** P1 to P3 and every Record row. Each BPE run also prints its first and last 10 merges, and every run prints one line per test string (characters, bytes, tokens, round trip). **Human steps:** none
**Status:** todo

## 0. Retrieval (0:00, 5 min, closed book, no AI)

The AI asks up to three due cards from `../../quiz-bank.md`, one at a time. Do not open the bank first.

## 1. Predict (0:05, 7 min, no AI)

This lab is an exception: you write this section days before the session, before you watch the video.

1. **Days before, no AI.** Level W: read `scripts/38_bpe_tokenizer.py` for 4 minutes and answer its three `# Q:` prompts here. Then write P1 to P3 in the table below.
2. **At 0:05 (7 min).** Reread your answers and rows, and change nothing. Then reread `train()` and `encode()`.

- `train`: why does the vocabulary start with exactly 256 tokens?
- `train`: what does one merge do to the length of ids?
- `encode`: why must encode apply the merges in the order they were learned?

Write each row here before anything runs; the AI copies it into `../../prediction-log.md` word for word. A row that asks for several numbers becomes one log row per number, each with its own range.

How the script counts. It trains on all 1,115,394 characters of TinyShakespeare as one sequence of UTF-8 (Unicode Transformation Format, 8-bit) bytes. Nothing splits the text into words first, so a merge can join bytes across a space or a line break. It counts tokens on the same text. Tokens per 1,000 characters = 1,000 x tokens / characters.

| Step | Question | Kind | Prediction | 80% range or confidence |
|---|---|---|---|---|
| P1 | Byte-level BPE, 256 merges (256 byte tokens plus 256 learned ones), trained on all of TinyShakespeare as one byte sequence, counted on the same text, seed 0. Tokens per 1,000 characters (`P1.tokens_per_1k_chars`) | num | | |
| P2 | `--change`: 512 merges instead of 256. Same text, same counting, seed 0. Tokens per 1,000 characters (`P2.tokens_per_1k_chars`) against P1: up, down or same, plus an 80% range for the size of the change, in tokens per 1,000 characters. Graded on `P2.delta_vs_256`, P2 minus P1: its sign is the direction, and Hit also needs its size inside your range. Off by uses the sizes | dir | | |
| P3 | `--break`: a character-level vocabulary instead of bytes. One id for each distinct character in TinyShakespeare, one unknown id for any other character. Encode, then decode, the 10 strings in `TESTS` (they include an emoji, accented letters and 'naïve café'). How many of the 10 come back exactly as they went in (`P3.char_roundtrip`, 0 to 10)? | num | | |

## 2. Setup (before the session)

```
$ source ~/.venvs/ml/bin/activate
$ cd m7-language-models    # from ml-learning/, where sessions start
$ python scripts/38_bpe_tokenizer.py --download
$ python scripts/38_bpe_tokenizer.py --smoke
```

The script has no random step, so `--seed` changes nothing here.

## 3. Baseline (0:12, 10 min)

Why: providers bill and rate-limit in tokens, so tokens per 1,000 characters turns text into cost. This run measures it at 256 merges, next to the 0-merge row (one token per byte).

```
$ python scripts/38_bpe_tokenizer.py --baseline
(paste your RESULT lines)
```

Prediction vs actual, one sentence. The reference run is in `../../answers/`; the AI opens it only after your P1 row exists and you have pasted your own RESULT lines.

## 4. Change one thing (0:22, 10 min)

Why: vocabulary size is a design knob. Each token costs one embedding row, and training time is a cost to measure, so this run records it. It isolates what 256 more merges do to tokens per 1,000 characters.

Change: 512 merges instead of 256 (`2 * MERGES`). Same text, same counting. P2 is logged above.

```
$ python scripts/38_bpe_tokenizer.py --change
(paste your RESULT lines)
```

## 5. Break it (0:32, 10 min, AI gives hints only; the run finishes by 0:40)

Why: a vocabulary built from one corpus meets text from outside it.

Break: build a character-level vocabulary from TinyShakespeare (one id per distinct character, one unknown id for anything else). Then encode and decode the 10 strings in `TESTS`, which include an emoji and 'naïve café'. P3 is logged above.

```
$ python scripts/38_bpe_tokenizer.py --break
(paste your RESULT lines)
```

Why, in three sentences, written without AI:

## 6. Explain-back (0:42, 5 min) and rebuild (0:47, 10 min), no AI

- Five sentences for a smart engineer new to ML, written without AI. The AI names your weakest claim after the session (section 7).
- Rebuild: open `rebuild/38_bpe_merge_loop.py`, write `merge()` and `train()` from memory (`vocab_of()`, `encode()` and `decode()` are given), then run `python rebuild/38_bpe_merge_loop.py`. Its `check()` compares `merge()` with Python's `str.replace`. It checks every pair `train()` picks against numpy's pair counts (`np.unique`). It round-trips 5 strings, including an emoji and 'naïve café'. It also times 256 merges on a 50 KB slice, against a limit of 2 seconds of CPU (central processing unit) time. It never compares with this lab's results.

## 7. What I learned

After the session (about 5 minutes): the AI names the weakest claim in your five sentences and asks one question that tests it. Edit the sentences here.

## 8. Interview soundbite (one of the three cards written at 0:57)

> One or two sentences only someone who ran this would say.

Staff follow-up (failure modes): the gateway in the repo link estimates input tokens from body bytes times a ratio kept per tenant and model. Overnight, one tenant's traffic moves from English to Japanese and emoji. What goes wrong first, and how does the estimator recover? Answer in 2 sentences from the repo link (§2). Rotate: simplest design, failure modes, migration, what pages at 3 am, cost, trade-off.

## 9. Quiz cards (0:57, 3 min)

The AI drafts three cards (M, N, and T or D). Edit or replace them. Questions go to `../../quiz-bank.md`, keys to `../../answers/quiz-key.md`.

## Record

The script prints these as RESULT lines. Paste, do not type.

| Metric | Your run | Hardware (the script's HW line) | Captured by (script or learner) |
|---|---|---|---|
| `baseline.tokens_per_1k_chars_0_merges`: 0 merges, one token per byte | | | script |
| `P1.tokens_per_1k_chars`: 256 merges | | | script |
| `baseline.train_seconds`: seconds to learn 256 merges (`device=cpu`, `n=1`) | | | script |
| `baseline.byte_roundtrip`: test strings that round-trip, byte-level, 256 merges (of 10) | | | script |
| `P2.tokens_per_1k_chars`: 512 merges | | | script |
| `P2.delta_vs_256`: `P2.tokens_per_1k_chars` minus `P1.tokens_per_1k_chars`, same seed | | | script |
| `change.train_seconds`: seconds to learn 512 merges (`device=cpu`, `n=1`) | | | script |
| `change.byte_roundtrip`: test strings that round-trip, byte-level, 512 merges (of 10) | | | script |
| `break.char_vocab_size`: distinct characters in TinyShakespeare (the unknown id not counted) | | | script |
| `P3.char_roundtrip`: test strings that round-trip, character-level (of 10) | | | script |
