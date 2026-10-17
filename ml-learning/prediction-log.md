# Prediction log

> One row per prediction, written before the step runs. The AI fills Actual, Hit and Off by from your pasted RESULT line. Every 10 labs, the calibration table shows what you over- or under-estimate.

## Kinds

| Kind | You write | Hit when |
|---|---|---|
| num | A point estimate and an 80% range | The actual is inside the range |
| dir | Up, down or same, plus a size range | The sign is right and the size is inside the range |
| pick | One option and a confidence from 50 to 100 | The option is right |

Picks are also scored with the Brier score: (1 - conf/100)^2 on a hit, (conf/100)^2 on a miss. Lower is better. 0.25 is a coin flip.

## How a row is filled

- You write Date, Lab, Step, Question, Kind, Predicted and the 80% range or conf, before the step runs.
- Steps are P1, P2 and P3 (and P1b in lab 39).
- `skip` logs the row as skipped. A skipped row gets no Hit and counts in no calibration figure.
- The AI fills Actual, Hit and Off by from your pasted RESULT line. Hit uses only the range written before the run.
- Off by = actual / predicted. A dir row uses the sizes. A quantity predicted in log10 uses 10^(actual - predicted). A pick row gets its Brier score instead. If the prediction is 0, write n/a.
- You write the Lesson after the run: "I assumed X, the run shows Y".

## Predictions

| Date | Lab | Step | Question | Kind | Predicted | 80% range or conf | Actual | Hit | Off by | Lesson (I assumed X, the run shows Y) |
|---|---|---|---|---|---|---|---|---|---|---|

## Calibration (every 10 labs)

| After lab | Range hit rate (target 80%) | Brier on picks (0.25 is a coin flip) | Median Off by | What I over- or under-estimate |
|---|---|---|---|---|
| 10 | | | | |
| 20 | | | | |
| 30 | | | | |
| 40 | | | | |

- Range hit rate: the share of num and dir rows that hit, over those 10 labs. Brier on picks: the mean over pick rows. Median Off by: over num and dir rows.
- About 30 predictions per 10 labs give one standard error of about 7 points at an 80% target. So read only gaps above 15 points.
