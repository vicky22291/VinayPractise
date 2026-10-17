# 38. BPE tokenizer: the merge loop, bytes vs characters: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 38'.

- **HW:** `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`
- **Seeds:** 0, 1 and 2 for `--baseline`, `--change` and `--break` (light lane, 9 runs). The script has no random step, so every count is identical at all three seeds. Only the timings move.
- **Reference script:** `m7-language-models/scripts/38_bpe_tokenizer.py` (level W: the learner's script is the reference), sha256 prefix `e70b6d5aa5e33ba6`.
- **Runs and wall times (seeds 0, 1, 2):** baseline 52.3, 38.9 and 34.1 s; change 78.3, 70.6 and 53.3 s; break 0.1, 0.1 and 0.1 s. The runs went one at a time, at a 1-minute load average of 11.1 to 17.5 on 14 cores, beside other builds' heavy jobs (Build notes and the .json note give the details).
- **Tolerance rule (from the .json):** tol = spread (max - min) over seeds 0, 1, 2. Every count has spread 0, so the tolerance adds no slack. The learner's own counts should match the reference exactly: a mismatch means a different input file or edited code, not noise. Hit still means the learner's actual is inside their own 80% range, written before the run. The two timing rows carry the machine's load in their spread.

<details><summary>P1. Tokens per 1,000 characters of TinyShakespeare after 256 merges</summary>

**Answer:** 509.425 tokens per 1,000 characters (tolerance 0.0, the spread over seeds 0, 1 and 2).

Seed-0 RESULT lines:

```
RESULT baseline.tokens_per_1k_chars_0_merges=1000 unit=tokens/1k_chars seed=0
RESULT P1.tokens_per_1k_chars=509.425 unit=tokens/1k_chars seed=0
RESULT baseline.train_seconds=52.1388 unit=s device=cpu batch=full_text warmup=0 n=1 stat=median seed=0
RESULT baseline.byte_roundtrip=10 unit=of_10 seed=0
```

Other seeds: `P1.tokens_per_1k_chars` is 509.425 at seeds 1 and 2. `baseline.train_seconds` is 38.7387 and 33.9284 s (spread 18.2104 s, machine load).

**Why:** each BPE (byte-pair encoding) merge replaces every occurrence of the most frequent pair with one new token, so a pair seen c times shortens the text by c tokens (fewer only when copies overlap, as in 'aaa'). Nothing splits the text into words, so many top pairs join a word's last letter to the space after it: the first four merges are `'e '`, `'th'`, `'t '` and `'s '`, and 6 of the first 10 end in a space. By merge 256 the new tokens are word pieces and short words with their spaces (`'sir'`, `', and '`, `'king'`), so 256 merges take the text from 1,000 tokens (one per byte) to 509.425 per 1,000 characters. A vocabulary of 512 is still tiny next to the 50,257 of GPT-2 (OpenAI's generative pre-trained transformer 2): at most 256 tokens are longer than one byte, so only the commonest pieces can be single tokens.

**Common wrong prediction:** about 250, from the rule of thumb of 4 characters per token. That rule belongs to production vocabularies of 50,000 to 200,000 tokens. The opposite miss is 800 to 900, from thinking 256 merges barely dent 1.1 MB.

</details>

<details><summary>P2. 512 merges instead of 256: tokens per 1,000 characters, direction and size</summary>

**Answer:** down by 71.9468 tokens per 1,000 characters, to 437.479 (tolerance 0.0 for both).

Seed-0 RESULT lines:

```
RESULT P2.tokens_per_1k_chars=437.479 unit=tokens/1k_chars seed=0
RESULT P2.delta_vs_256=-71.9468 unit=tokens/1k_chars seed=0
RESULT change.train_seconds=78.066 unit=s device=cpu batch=full_text warmup=0 n=1 stat=median seed=0
RESULT change.byte_roundtrip=10 unit=of_10 seed=0
```

Other seeds: 437.479 and -71.9468 at seeds 1 and 2. `change.train_seconds` is 70.5017 and 53.1399 s (spread 24.9261 s, machine load).

**Why:** BPE is greedy and has no random step, so the first 256 of the 512 merges are exactly the baseline's 256 (both runs print the same first 10 merges). The change only adds merges 257 to 512, which are rarer pairs than `'e '` or `'th'`, so each one saves fewer tokens. The first 256 merges cut 490.575 tokens per 1,000 characters (1,000 minus 509.425), and the next 256 cut 71.9468, about a seventh as much. Compression grows slowly with vocabulary size, which is why production tokenizers need vocabularies of 50,000 and more.

**Common wrong prediction:** a drop of about 250, from thinking that doubling the vocabulary halves the tokens again. A drop near 490 comes from assuming every merge saves the same.

</details>

<details><summary>P3. Character-level vocabulary from TinyShakespeare, then 10 test strings with an emoji and accented letters: how many round-trip</summary>

**Answer:** 4 of 10 (tolerance 0).

Seed-0 RESULT lines and the per-string table:

```
chars   chars=42  bytes=42  tokens=42  ok   'To be, or not to be, that is the question.' -> 'To be, or not to be, that is the question.'
chars   chars=10  bytes=12  tokens=10  FAIL 'naïve café' -> 'na�ve caf�'
chars   chars=23  bytes=23  tokens=23  ok   'Your card was declined.' -> 'Your card was declined.'
chars   chars=21  bytes=24  tokens=21  FAIL 'Thanks, that worked 👍' -> 'Thanks, that worked �'
chars   chars=37  bytes=37  tokens=37  FAIL 'Refund of $25.00 sent for order 7781.' -> 'Refund of $��.�� sent for order ����.'
chars   chars=39  bytes=39  tokens=39  ok   'Is this a dagger which I see before me?' -> 'Is this a dagger which I see before me?'
chars   chars=16  bytes=19  tokens=16  FAIL 'Grüße aus Zürich' -> 'Gr��e aus Z�rich'
chars   chars=25  bytes=25  tokens=25  FAIL 'Reply to help@example.com' -> 'Reply to help�example.com'
chars   chars=9   bytes=27  tokens=9   FAIL '東京で会いましょう' -> '���������'
chars   chars=39  bytes=39  tokens=39  ok   "Shall I compare thee to a summer's day?" -> "Shall I compare thee to a summer's day?"
RESULT break.char_vocab_size=65 unit=characters seed=0
RESULT P3.char_roundtrip=4 unit=of_10 seed=0
```

Other seeds: 4 and 65 at seeds 1 and 2. Byte-level BPE round-trips all 10 at every seed: `baseline.byte_roundtrip=10` and `change.byte_roundtrip=10`.

**Why:** a character vocabulary is closed, and TinyShakespeare's 65 distinct characters are newline, space, 10 punctuation marks and symbols (`! $ & ' , - . : ; ?`), the digit 3 and the 52 ASCII (American Standard Code for Information Interchange) letters. Any other character becomes the unknown id and decodes to U+FFFD, so one unseen character breaks the whole string: accents, the emoji and Japanese, but also the plain-ASCII digits in `$25.00` and `7781` and the `@` in an email address. Byte-level BPE has no unknown token, because its base vocabulary is all 256 byte values. The price shows in the baseline table: the 9 Japanese characters are 27 bytes and stay 27 tokens at 256 and at 512 merges, because merges learned from English never touch those bytes.

**Common wrong prediction:** 6 of 10, from counting only the 4 strings with non-ASCII characters as failures. The plays hold no digit other than 3 and no `@`.

</details>

<details><summary>Rebuild check</summary>

- Stub: `m7-language-models/rebuild/38_bpe_merge_loop.py`. Solution: `answers/rebuild/38_bpe_merge_loop.py`.
- `rebuildcheck`: stub fails as it should (exit 1, NotImplementedError), solution passes (exit 0, `check: PASS`): REBUILDCHECK OK.
- What `check()` does: `merge()` against Python's `str.replace` on 300 random lists over 3 ids (overlapping runs such as 2, 2, 2 included). Then `train(text, 256)` on the first 50,000 characters: every merge must pick a pair whose count equals numpy's top pair count (`np.unique` on a `str.replace` replay of the whole slice), the new ids must run 256 to 511, and the token count must equal the replay's. Then 5 strings round-trip (Hamlet, 'naïve café', an emoji, German, Japanese). Last, `train()` must use under 2 seconds of CPU (central processing unit) time.

</details>

<details><summary>Card drafts</summary>

Three cards: M, N and D. If the last close used D, swap 38-D for the alternate T card under the keys.

| ID | Lab | Type | Question |
|---|---|---|---|
| 38-M | 38 | M | Why can a byte-level BPE tokenizer encode and decode any string, when a character vocabulary built from the same text cannot? |
| 38-N | 38 | N | On TinyShakespeare, how many tokens per 1,000 characters do BPE merges 257 to 512 save, how does that compare with what the first 256 merges saved, and why? |
| 38-D | 38 | D | A tokenizer trained on English support chats turns a customer name with 'ë' and an order note with an emoji into replacement marks after encode and decode. What do you check first, and what fixes it? |

Keys (must-mention items):

- **38-M:** (1) the base vocabulary is all 256 byte values, and every string is a sequence of UTF-8 (Unicode Transformation Format, 8-bit) bytes; (2) merges only add tokens, so an unseen character falls back to its 1 to 4 bytes; (3) one unseen character breaks the whole string, and unseen includes plain ASCII: TinyShakespeare has no digit other than 3 and no `@`, so `$25.00`, `7781` and an email address fail too, not only the accents, the emoji and Japanese.
- **38-N:** (1) about 72 fewer, from about 510 to about 440 (reference 71.9468, from 509.425 to 437.479). Hit: a saving of 65 to 80. Partial: a saving of 20 to 200, the right order of magnitude; (2) the first 256 merges saved about 490, about 7 times as much; (3) BPE is greedy, so merges 1 to 256 are the same in both runs, and merges 257 to 512 are rarer pairs, each saving fewer tokens.
- **38-D:** (1) encode then decode the failing string, compare, and look for the unknown id in the ids; (2) the vocabulary is closed (character or word level) and never saw those characters; (3) fix: a byte-level tokenizer, whose 256 byte tokens make every string round-trip.

Alternate T card, for a close after a D: | 38-T | 38 | T | An alias falls back to another provider's model, and the gateway keeps the token-per-byte ratio it learned on the first model. Why can the input-token estimate now be wrong in either direction, and what bounds it while the new ratio warms up? | Key: (1) each tokenizer's merges come from its own training text and vocabulary size, so the same bytes split into a different number of tokens; (2) key the ratio by tenant and model (`r(tenant, model)` in the repo link §2) and correct the fallback model's ratio from that provider's reported counts; (3) a byte-level BPE spends at most one token per UTF-8 byte, so bytes x 1 is a safe ceiling. This lab's English-only 256-merge BPE hit that ceiling on Japanese (27 tokens for 27 bytes). A production tokenizer with multilingual merges spends less, so the toy figure is an upper bound, not a production cost.

</details>

<details><summary>Build notes</summary>

- **Plain merge loop, as the spec designs it.** The first build switched to pre-tokens (pairs counted inside each distinct word, weighted by its count) under the spec's rule "if 512 merges exceed 2 minutes, merge over unique pre-tokens with counts". Its only evidence was one tagged run, timed while other builds loaded the machine: 350.716 s of training for 512 merges. This fix re-timed the plain loop in tagged runs, which mkanswers ignores. The .json note gives each figure, its log and its load. At a 1-minute load average of 58.6 to 86.0, the plain loop trained 512 merges in 136.517 s, so load alone can push it past 2 minutes. At 15.3 to 20.7, the same `merge()` and `train()` took 86.65 s of wall time and 83.19 CPU seconds for 512 merges. CPU time on a busy machine is at least what the same work takes on an idle one, so it is a safe upper bound. The reference change runs trained in 78.066, 70.5017 and 53.1399 s. All are under 2 minutes, so the rule does not apply. The script and the rebuild use the spec's plain loop: `Counter(zip(ids, ids[1:]))` and `max` over the whole id list. Cross-check: the first build's flat experiment, a different script, also gave 437.479 tokens per 1,000 characters at 512 merges.
- **Rebuild length.** `merge()` and `train()` are 19 lines with their `def` lines, docstrings not counted: about the spec's 18.
- **Rebuild timing.** The check times 256 merges on the first 50,000 characters in CPU seconds (`time.process_time`), against the spec's 2 s limit. The new ids must run 256 to 511. At a load average of 13.2 to 15.0, 256 merges took 1.13 CPU seconds: under the spec's 1.4 s prototype, with about 1.8x headroom. At 20.7 the same work took 2.43 CPU seconds, so a busy Mac can fail a correct rebuild on the time line alone. `rebuildcheck` passed while another build's heavy run shared the machine. If a learner's correct `train()` fails only on time, rerun it with the Mac idle before calling it slow.
- **Timing rows.** The six timing runs went one at a time, at a 1-minute load average of 11.1 to 17.5. Three of them first ran at a load of 14 or more, so this fix reran those three at under 14. The spread still comes from the machine, not the code. Every timing run shared it with another build's heavy job. The slow ones overlapped a lab 15 Ollama run (baseline and change at seed 0) or a lab 35 change run (change at seed 1). Both compete for memory bandwidth, and the load average does not show that. No prediction uses the timing rows. On an idle Mac, expect the fastest seed's time or less.
- **Knob changes:** none. Both effects pass the 2x spread rule with spread 0. The P2 effect is -71.946, equal to `P2.delta_vs_256` at every seed up to the rounding of the RESULT lines. The P3 effect is -6.0 (4 minus 10).
- **Precomputed steps:** none. The longest seed-0 run (change) took 78.3 s of wall time.
- **Choices where the spec is silent.** Tokens are counted on the training text itself, as the goal says "train ... on 1.1 MB" and P1 says "of TinyShakespeare". The 10 test strings are the build's: 4 in-vocabulary English lines (3 Shakespeare, 1 payments), 2 plain-ASCII lines with characters the plays lack (digits, `@`), and 4 non-ASCII lines ('naïve café', an emoji, German, Japanese). The file path is lab 39's (`~/ml-data/nanoGPT/data/shakespeare_char/input.txt`), so the 1.1 MB downloads once. The character vocabulary maps unseen characters to one unknown id that decodes to U+FFFD. Timing tags read `batch=full_text warmup=0 n=1 stat=median`: one timed training run, so the median is that run. In `--smoke`, the change step takes its delta from the smoke baseline's own P1, so smoke never reads a stored full-run value.
- **Prototype comparison.** The spec carries no `[answers only]` values for this lab. Its author note timed the plain loop at 1.4 s (50 KB) and 5.4 s (200 KB) for 256 merges, and extrapolated about 30 s on 1.1 MB. Here the 50 KB slice took 1.13 CPU seconds at a load of 13.2 to 15.0, in line with the note. The full text took 52.1388, 38.7387 and 33.9284 s for 256 merges, slower than the extrapolation. Per character, the full text costs 1.3 to 2.1 times the 50 KB slice. Likely causes: the 1.1-million-id list and its pair Counter no longer fit in the CPU caches, and the other builds' heavy jobs. The counts have no prototype to compare with.
- **Leak search.** Every .json value was searched in the lab file, the script and the rebuild stub, at 2 to 6 significant digits and as a whole number. The only hits are configuration: the lab number 39, the video length 2:13:34, the 1.1 MB file size, the 80% range and the `$25.00` in a test string. The search skips 1000 and 10, which are also configuration there: the unit tokens per 1,000 characters and the 10 test strings.
- **Ledger noise.** Five jobs from the first build exited 2 on a shell quoting slip (mode `break --seed 0` and similar), and mkanswers skips them. The tagged experiments (`flat`, `plain`, `cpuprobe`, `small50k`) are not reference runs, and mkanswers skips them too.

</details>
