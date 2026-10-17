# 11. Error analysis by hand: errors decide the next experiment: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 11'.

- HW: `HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=mps`
- Seeds: 0, 1 and 2 for every step. The heavy-lane protocol asks for seeds 1 and 2 on the baseline only; change and break got them too (see Build notes).
- Reference script: `answers/11_error_analysis_ref.py` (sha256 prefix `70f0ab4f577603c9`). The learner's starter is `m2-dont-fool-yourself/scripts/11_error_analysis.py`.
- Runs and wall times (s), seeds 0, 1, 2: baseline 173.2, 170.1, 163.6; change 25.9, 29.6, 22.7; break 258.4, 215.8, 199.4. Each run trains or reloads its own model; no step is precomputed.
- Tolerance rule (from the .json): "tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step". The .json notes replace the heavy-lab clause for this lab: "Change and break were also run at seeds 1 and 2, so every value has its own spread over seeds 0, 1 and 2, and that spread is its tolerance, in place of the baseline spread." So the P2 count and P3 are graded against their own spreads, never a baseline spread. A seed changes the 80/20 split, the head's initial weights, the batch order and the flipped rows.

<details><summary>P1. Of the 50 highest-loss validation images of the seed 0 model, how many carry a wrong or ambiguous label rather than a model mistake?</summary>

Open this block only after the learner's tally table in the lab file is filled in: it shows the same 50 images.

**Answer:** the learner's own count. The tally is a human step, so the reference holds no count, only the script's values and the item list below (`ml-learning/CLAUDE.md` §9). Grade the P1 row against the learner's count. A hand count has no seed spread.

Seed-0 RESULT lines:

```
RESULT baseline.error_rate=0.0913396 unit=fraction seed=0
RESULT baseline.valid_errors=135 unit=images seed=0
RESULT baseline.top50_misclassified=50 unit=images seed=0
```

Other seeds: `baseline.error_rate` 0.0757781 (seed 1) and 0.0818674 (seed 2), spread 0.015561500000000006. `baseline.valid_errors` 112 and 121, spread 23. `baseline.top50_misclassified` 50 and 50, spread 0.

The seed-0 item list, from the TOP lines in `11-error-analysis.out` (loss in nats). The learner's run is a separate training run on MPS, so a few ranks near the bottom may differ from theirs.

| Rank | File | Actual | Predicted | Loss |
|---|---|---|---|---|
| 1 | `german_shorthaired_130.jpg` | german_shorthaired | great_pyrenees | 10.332 |
| 2 | `german_shorthaired_116.jpg` | german_shorthaired | staffordshire_bull_terrier | 9.664 |
| 3 | `boxer_182.jpg` | boxer | english_setter | 7.977 |
| 4 | `german_shorthaired_132.jpg` | german_shorthaired | great_pyrenees | 7.275 |
| 5 | `chihuahua_42.jpg` | chihuahua | american_pit_bull_terrier | 6.845 |
| 6 | `shiba_inu_157.jpg` | shiba_inu | Maine_Coon | 6.499 |
| 7 | `yorkshire_terrier_141.jpg` | yorkshire_terrier | scottish_terrier | 5.307 |
| 8 | `shiba_inu_187.jpg` | shiba_inu | Abyssinian | 5.291 |
| 9 | `Ragdoll_53.jpg` | Ragdoll | Birman | 5.195 |
| 10 | `boxer_18.jpg` | boxer | american_bulldog | 5.139 |
| 11 | `Ragdoll_245.jpg` | Ragdoll | Birman | 5.057 |
| 12 | `Ragdoll_204.jpg` | Ragdoll | Birman | 4.689 |
| 13 | `leonberger_162.jpg` | leonberger | newfoundland | 4.688 |
| 14 | `Ragdoll_181.jpg` | Ragdoll | Birman | 4.569 |
| 15 | `pomeranian_80.jpg` | pomeranian | japanese_chin | 4.457 |
| 16 | `american_pit_bull_terrier_100.jpg` | american_pit_bull_terrier | american_bulldog | 4.313 |
| 17 | `Ragdoll_228.jpg` | Ragdoll | Birman | 4.139 |
| 18 | `Persian_233.jpg` | Persian | Ragdoll | 4.132 |
| 19 | `Bengal_180.jpg` | Bengal | British_Shorthair | 4.001 |
| 20 | `Birman_24.jpg` | Birman | Siamese | 3.943 |
| 21 | `samoyed_131.jpg` | samoyed | great_pyrenees | 3.638 |
| 22 | `Maine_Coon_98.jpg` | Maine_Coon | Ragdoll | 3.452 |
| 23 | `samoyed_150.jpg` | samoyed | great_pyrenees | 3.424 |
| 24 | `yorkshire_terrier_125.jpg` | yorkshire_terrier | Egyptian_Mau | 3.380 |
| 25 | `staffordshire_bull_terrier_48.jpg` | staffordshire_bull_terrier | american_pit_bull_terrier | 3.327 |
| 26 | `Russian_Blue_184.jpg` | Russian_Blue | Bombay | 3.196 |
| 27 | `Egyptian_Mau_28.jpg` | Egyptian_Mau | Bengal | 3.160 |
| 28 | `Bengal_153.jpg` | Bengal | Sphynx | 3.157 |
| 29 | `yorkshire_terrier_93.jpg` | yorkshire_terrier | havanese | 3.141 |
| 30 | `Birman_50.jpg` | Birman | Siamese | 3.138 |
| 31 | `Ragdoll_140.jpg` | Ragdoll | Birman | 3.081 |
| 32 | `Russian_Blue_43.jpg` | Russian_Blue | Bombay | 2.970 |
| 33 | `american_bulldog_169.jpg` | american_bulldog | beagle | 2.916 |
| 34 | `beagle_88.jpg` | beagle | basset_hound | 2.843 |
| 35 | `boxer_41.jpg` | boxer | saint_bernard | 2.770 |
| 36 | `chihuahua_107.jpg` | chihuahua | miniature_pinscher | 2.719 |
| 37 | `american_pit_bull_terrier_62.jpg` | american_pit_bull_terrier | american_bulldog | 2.711 |
| 38 | `Birman_56.jpg` | Birman | Siamese | 2.696 |
| 39 | `Bengal_133.jpg` | Bengal | Egyptian_Mau | 2.672 |
| 40 | `beagle_167.jpg` | beagle | miniature_pinscher | 2.662 |
| 41 | `Egyptian_Mau_155.jpg` | Egyptian_Mau | Abyssinian | 2.630 |
| 42 | `pug_190.jpg` | pug | chihuahua | 2.627 |
| 43 | `Siamese_95.jpg` | Siamese | chihuahua | 2.624 |
| 44 | `staffordshire_bull_terrier_27.jpg` | staffordshire_bull_terrier | american_pit_bull_terrier | 2.609 |
| 45 | `japanese_chin_127.jpg` | japanese_chin | great_pyrenees | 2.605 |
| 46 | `Bengal_161.jpg` | Bengal | Egyptian_Mau | 2.582 |
| 47 | `staffordshire_bull_terrier_29.jpg` | staffordshire_bull_terrier | great_pyrenees | 2.551 |
| 48 | `american_pit_bull_terrier_171.jpg` | american_pit_bull_terrier | miniature_pinscher | 2.525 |
| 49 | `american_pit_bull_terrier_191.jpg` | american_pit_bull_terrier | staffordshire_bull_terrier | 2.521 |
| 50 | `english_setter_134.jpg` | english_setter | great_pyrenees | 2.514 |

Why: the per-image loss is minus the log of the probability the model gives the recorded label, so it is large exactly when that probability is small, whether the rest sits on one other breed or is spread over several. The top of the list is therefore the images whose recorded label the model most strongly rejects, not every error. A clear photo with a wrong label gets there because the model sees the real breed and gives the recorded one almost nothing, but a hard photo or a look-alike breed can get there too, and a confident vote for one other breed is a pattern to check in the plot (each title ends with the top predicted breed's probability), not something a high loss guarantees. All 50 images are misclassified at every seed, so each one is either a label problem or a model mistake, and only the tally decides which.

Common wrong prediction: a number fixed before looking, from "a published benchmark has clean labels" or from "every look-alike breed is a label problem". The working rule: a label problem is an image whose label a careful person would change, or could not decide from the photo. A Ragdoll that looks like a Birman, correctly labelled, is a model mistake.

</details>

<details><summary>P2. Will the top pair of interp.most_confused(min_val=3) on the same model fall inside your largest error category from the tally?</summary>

**Answer:** graded against the learner's own largest category. The script's side at seed 0: the top pair is Ragdoll/Birman with 13 images. The top pair is american_pit_bull_terrier/staffordshire_bull_terrier at seed 1 and Ragdoll/Birman at seed 2, so which look-alike pair leads changes with the split; it was a look-alike breed pair at all three seeds. Tolerance for the count: spread 4.

Seed-0 RESULT lines:

```
RESULT P2.top_pair=Ragdoll/Birman unit=actual/predicted seed=0
RESULT change.top_pair_count=13 unit=images seed=0
RESULT change.pairs_min3=10 unit=pairs seed=0
RESULT change.images_in_pairs_min3=59 unit=images seed=0
```

Other seeds: `change.top_pair_count` 9 and 10. `change.pairs_min3` 9 and 15, spread 6. `change.images_in_pairs_min3` 41 and 63, spread 22.

The seed-0 list, from the CONFUSED lines (actual, predicted, count):

| Actual | Predicted | Count |
|---|---|---|
| Ragdoll | Birman | 13 |
| Bengal | Egyptian_Mau | 10 |
| american_pit_bull_terrier | american_bulldog | 7 |
| american_pit_bull_terrier | staffordshire_bull_terrier | 7 |
| Birman | Siamese | 6 |
| american_bulldog | staffordshire_bull_terrier | 4 |
| British_Shorthair | Russian_Blue | 3 |
| Russian_Blue | British_Shorthair | 3 |
| american_pit_bull_terrier | miniature_pinscher | 3 |
| staffordshire_bull_terrier | american_pit_bull_terrier | 3 |

Why: `most_confused` counts (actual, predicted) cells over all 135 validation errors, so it ranks confusions by how often they happen, while the top-loss list ranks single images by how little probability the model gives the recorded label. Both read the recorded labels, so neither can tell a label error from a model mistake: a Birman photo labelled Ragdoll that the model calls Birman lands in the same Ragdoll/Birman cell as a true Ragdoll that the model calls Birman. A repeated pair can therefore hold label errors, model mistakes or both, and only reading its images says which. The pairs listed hold 59 of the 135 errors at seed 0; the rest sit in cells below 3.

Common wrong prediction: a confident answer from treating the two tools as two views of one list. One counts how often a confusion happens and the other ranks single images, so they can agree or not. Grade against the learner's own tally and top pair: "yes" when most of that pair's images among their 50 (in the reference run, the Ragdoll rows predicted as Birman in the P1 item list) sit in their largest category, whether they filed them as look-alike mistakes or as label problems; "no" when those images sit in a smaller category or none of them reach the 50.

</details>

<details><summary>P3. Flip exactly 10% of the training labels (591 of 5,912, flip seed 0) and retrain: how many of the 50 highest training losses are flipped labels?</summary>

**Answer:** 50 of 50 at seed 0, and 50 and 50 at seeds 1 and 2: spread 0, so the tolerance is 0. With no signal in the loss, the expected count is `break.chance_in_top50` = 4.99831.

Seed-0 RESULT lines:

```
RESULT P3.flipped_in_top50=50 unit=images k=50 seed=0
RESULT break.chance_in_top50=4.99831 unit=images seed=0
RESULT break.flipped_memorised=0.0203046 unit=fraction seed=0
RESULT break.error_rate=0.104871 unit=fraction seed=0
```

Other seeds: `break.flipped_memorised` 0.0101523 and 0.0236887, spread 0.0135364. `break.error_rate` 0.0866035 and 0.100135, spread 0.018267500000000006.

Effects (mkanswers, mean over seeds 0, 1, 2): `P3.flipped_in_top50` minus `break.chance_in_top50` = 45.001689999999996 images, spread 0: far above 2x the spread. `break.error_rate` minus `baseline.error_rate` = 0.014208133333333331, against a split-to-split spread of 0.018267500000000006: below 2x the spread, so the cost of the flips in validation error is small here. It has the same sign at all three seeds when each break run is paired with the baseline on the same split, but this lab does not teach it as a real effect.

Why: the ImageNet body already separates the breeds, and `fine_tune(1)` gives it two short epochs (the head alone, then the whole network). That is enough to learn the true breeds and far too little to memorise 591 random labels: the model predicts the flipped label for only 0.0203046 of the flipped images at seed 0. So most flipped images get a low probability for their training label, and the 50 highest losses are all flipped labels; the run measures those 50 and the memorised share, not the loss of every flipped image. Zhang et al. 2017 show networks can fit random labels, but that takes many epochs; Arpit et al. 2017 show simple patterns are learned first, which is the regime here.

Common wrong prediction: a count near the 10% base rate, or a small multiple of it, from "deep nets memorise noise". True after long training, not after two epochs of fine-tuning. The payments version: in a model trained briefly on fresh labels, the highest training losses are a cheap first queue for label review.

</details>

<details><summary>Rebuild check</summary>

Stub `m2-dont-fool-yourself/rebuild/11_top_losses.py`, solution `answers/rebuild/11_top_losses.py` (`top_losses`, `flip_labels`, `tally`). rebuildcheck verdict: stub     fails as it should (exit 1); solution passes (exit 0); REBUILDCHECK OK. Its `check()` compares with `F.cross_entropy(reduction='none')` and `topk` on 1,000 synthetic rows where every tenth row has logits 100 times larger, checks that `flip_labels` flips exactly 10% of the rows and changes the class of each one, and compares `tally` with pandas `value_counts`.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 11-M | 11 | M | Why does ranking validation images by per-image loss, instead of listing every misclassified image, bring wrong labels to the top? |
| 11-N | 11 | N | Lab 11 flipped 10% of the Pets training labels and retrained with `fine_tune(1)`. How many of the 50 highest training losses were flipped labels, against about 5 by chance, and why? |
| 11-D | 11 | D | A fraud model's precision drops 5 points after a retrain on a fresh month of chargeback labels. What do you look at first, and what would tell you it is the labels rather than the model? |

Keys:

- 11-M: (1) the loss is minus the log of the probability given to the recorded label, so it grows as that probability falls, wherever the rest of the probability goes; (2) a clear photo with a wrong label gets almost no probability on its label, so it ranks near the top, though hard photos and look-alike breeds can rank there too; (3) "misclassified" is yes or no and hides how little probability the label got.
- 11-N: (1) 50 of 50 at seeds 0, 1 and 2, against 4.99831 by chance; (2) two epochs learn the true breeds before the noise: only 0.0203046 of flipped images were predicted as their flipped label at seed 0; (3) so most flipped labels get a low probability, and they fill the top of the loss ranking.
- 11-D: (1) rank the new training examples by loss and read the top ones, sliced by label source and by segment; (2) labels: the high-loss items cluster in one label source, such as disputes a merchant won or friendly fraud, or in one merchant; (3) the model or a segment: the errors sit on clean labels, or in one segment, so compare per-segment metrics before changing the model.

</details>

<details><summary>Build notes</summary>

- Runs: 9 reference runs, baseline, change and break at seeds 0, 1 and 2. The heavy-lane protocol asks for 5. Change and break were added at seeds 1 and 2 because P3 is a count with no baseline counterpart, so the baseline spread cannot serve as its tolerance, and the P2 pair needed a stability check. Each change run takes under a minute.
- Knob changes: none. The taught effect (flipped labels among the top 50 training losses, against chance) clears 2x its spread. The flips' cost in validation error does not, and is reported as small, never inflated.
- Precomputed steps: none. The longest seed-0 run is break, 258.4 s.
- Prototype comparison: the spec carries no `[answers only]` values for lab 11. Its rejected-proposals note says "the retrain takes about 2 minutes". Each `fine_tune(1)` here runs two epochs of 1 to 2 minutes each (the seed-0 logs show the epoch times), so a retrain takes about 3 minutes, and the break run adds a pass over the 5,912 training images. The note was a design-time estimate, and every run stays under the 6-minute cap, so nothing changed.
- Human step: P1's actual is the learner's tally. The reference never tallies; the P1 block holds the item list only.
- Deviations from the spec: (1) the plot and CSV go to `~/ml-data/results/lab11/top_losses_seed<S>.png` and `.csv` (the folder rule for plots) rather than `~/ml-data/results/lab11_top_losses.png`, and the baseline also saves `model_seed<S>.pth` there for `--change`; (2) `--download` uses the spec's primary URL only, while lab 01 keeps the Oxford fallback; (3) the script is 189 lines, over the 150-line guide, because it holds five modes, `--check`, a plot, a CSV and a model hand-off.
- Method notes: images and labels flow as (file, label) pairs so the flip touches training labels only; the split is lab 01's `RandomSplitter(valid_pct=0.2, seed=42 + seed)` on the same sorted file list. Training losses use the validation transforms (no augmentation) through `dls.test_dl(train items, with_labels=True)`. The plot ranks with fastai's own per-image losses (`ClassificationInterpretation`), and the CSV and TOP lines with `top_losses()`; `--check` makes them the same ranking.

</details>
