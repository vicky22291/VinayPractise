"""02. Ship it: a model is a service with a size, a p95 and inputs it has never seen. Lab 01's pet classifier
served one photo at a time on one CPU thread: its file size, its latency percentiles, and its answers for non-pets.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import math
import os
import random
import re
import sys
import time
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy, torch, transformers: it sets cache defaults
import torch
from fastai.vision.all import RandomResizedCropGPU, load_learner

URL, TGZ_BYTES = "https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-160.tgz", 99_003_388
VAL = labkit.DATA / "imagenette2-160" / "val"  # one folder per class; shared with lab 35
NON_PETS = {"n03028079": "church", "n03888257": "parachute", "n03445777": "golf_ball",
            "n03425413": "gas_pump", "n03417042": "garbage_truck"}
LAB01 = labkit.DATA / "models" / "lab01"       # written by lab 01's --baseline at seed 0
N_PETS, PER_CLASS, WARMUP, THRESHOLD = 200, 4, 10, 0.9
SIZE = {"baseline": 224, "change": 160, "break": 224}  # px: the square the model sees


def download():
    labkit.extract(labkit.fetch(URL, labkit.DATA / "imagenette2-160.tgz", size=TGZ_BYTES), labkit.DATA)
    for folder in NON_PETS:
        print(f"HAVE {VAL / folder} {len(list((VAL / folder).glob('*.JPEG')))} images", flush=True)
    print(f"HAVE {LAB01 / 'export.pkl'} and {len(pet_files())} held-out pet photos", flush=True)


def pet_files():
    "The held-out pets: the first 200 files of lab 01's validation list, which is sorted by file name."
    listing = LAB01 / "valid_files.txt"
    files = [labkit.DATA / n for n in listing.read_text().splitlines()[:N_PETS]] if listing.exists() else []
    if not (LAB01 / "export.pkl").exists() or len(files) < N_PETS or not all(f.exists() for f in files):
        print("MISSING lab 01's model or photos: run python scripts/01_pet_breeds.py --download, "
              "then python scripts/01_pet_breeds.py --baseline (seed 0)", flush=True)
        sys.exit(2)
    return files[:12] if labkit.smoke() else files


def non_pet_files(seed):
    "4 validation photos from each of the 5 non-animal Imagenette classes, drawn at random by the seed."
    rng = random.Random(seed)
    return [(name, f) for folder, name in NON_PETS.items()
            for f in rng.sample(sorted((VAL / folder).glob("*.JPEG")), PER_CLASS)]


def breed(f):
    return re.match(r"^(.*)_\d+\.jpg$", f.name).group(1)  # Bombay_103.jpg -> Bombay, as lab 01 labels it


def percentile(sorted_vals, q):
    "Nearest rank: the value at rank ceil(q/100 x n) of n values sorted ascending (rank 1 is the smallest)."
    return sorted_vals[max(1, math.ceil(q * len(sorted_vals) / 100)) - 1]


def latency_report(predict, inputs, warmup=WARMUP):
    "Call predict on the first warmup inputs untimed, then time one call per input, in milliseconds."
    # Q: why are the first 10 calls made but left out of the timings?
    for x in inputs[:warmup]:
        predict(x)
    outputs, ms = [], []
    for x in inputs:
        t0 = time.perf_counter_ns()
        outputs.append(predict(x))
        ms.append((time.perf_counter_ns() - t0) / 1e6)
    ms.sort()
    return {"p50": percentile(ms, 50), "p95": percentile(ms, 95), "max": ms[-1]}, outputs


def confident_share(probs, threshold=THRESHOLD):
    "The share of inputs whose top class probability is above threshold."
    # Q: what do the 37 probabilities in one output add up to, and what does that leave a photo that is not a pet?
    return sum(float(p.max()) > threshold for p in probs) / len(probs)


def serve(learn, files, px):
    "learn.predict on each photo's JPEG bytes, one request at a time, with the model's input set to px x px."
    crop = next(t for t in learn.dls.valid.after_batch.fs if isinstance(t, RandomResizedCropGPU))
    crop.size = (px, px)  # the exported pipeline's last resize: lab 01's 448 px squares become px x px
    requests = [f.read_bytes() for f in files]  # each request carries one JPEG file, as an upload would
    shape = learn.dls.test_dl(requests[:1]).one_batch()[0].shape  # the tensor the model is handed
    print(f"DATA requests={len(requests)} input={'x'.join(map(str, shape))} threads={torch.get_num_threads()} "
          f"warmup={WARMUP} load1={os.getloadavg()[0]:.1f}", flush=True)  # load1: the Mac's 1-minute load average
    with learn.no_bar():
        return latency_report(learn.predict, requests)


def report_latency(names, stats, n):
    "One RESULT line per statistic, with the conditions it was measured under."
    for stat, name in names.items():
        labkit.result(name, stats[stat], unit="ms", device="cpu", batch=1, warmup=WARMUP, n=n,
                      threads=torch.get_num_threads(), stat=stat)


def accuracy(outputs, files):
    return sum(pred == breed(f) for (pred, _, _), f in zip(outputs, files)) / len(files)


def baseline(learn, pets, seed):
    stats, outputs = serve(learn, pets, SIZE["baseline"])
    report_latency({"p95": "P1.p95_ms", "p50": "baseline.p50_ms", "max": "baseline.max_ms"}, stats, len(pets))
    labkit.result("baseline.accuracy", accuracy(outputs, pets), unit="fraction", px=SIZE["baseline"], n=len(pets))
    labkit.result("baseline.pet_share_above_0_9", confident_share([p for _, _, p in outputs]),
                  unit="fraction", n=len(pets), threshold=THRESHOLD)
    labkit.result("baseline.export_mb", (LAB01 / "export.pkl").stat().st_size / 1e6, unit="MB")
    labkit.result("baseline.params", sum(p.numel() for p in learn.model.parameters()), unit="params")


def change(learn, pets, seed):
    stats, outputs = serve(learn, pets, SIZE["change"])
    acc = accuracy(outputs, pets)
    report_latency({"p95": "P2.p95_ms", "p50": "change.p50_ms", "max": "change.max_ms"}, stats, len(pets))
    labkit.result("P2.accuracy", acc, unit="fraction", px=SIZE["change"], n=len(pets))
    p95_224, acc_224 = labkit.prior("P1.p95_ms"), labkit.prior("baseline.accuracy")
    if p95_224 is not None and acc_224 is not None:  # only after a --baseline run with the same seed
        labkit.result("P2.p95_ratio_vs_224", stats["p95"] / p95_224, unit="ratio")
        labkit.result("P2.accuracy_delta_vs_224", (acc - acc_224) * 100, unit="points")


def break_it(learn, pets, seed):
    photos = non_pet_files(seed)
    _, outputs = serve(learn, [f for _, f in photos], SIZE["break"])
    probs = [p for _, _, p in outputs]
    if not labkit.smoke():  # one line per photo: the breed it was given, and that breed's probability
        for (name, f), (pred, _, p) in zip(photos, outputs):
            print(f"NONPET class={name} file={f.name} breed={pred} top_prob={float(p.max()):.4f}", flush=True)
    labkit.result("P3.share_above_0_9", confident_share(probs), unit="fraction", n=len(probs), threshold=THRESHOLD)
    labkit.result("break.max_top_prob", max(float(p.max()) for p in probs), unit="probability", n=len(probs))


def main():
    args = labkit.start(lab=2, device="cpu")
    if args.mode == "download":
        return download()
    pets = pet_files()  # stops with lab 01's commands if its model or photos are missing
    # Q: why time inference on one CPU thread, and why does the core that thread runs on matter for p95?
    torch.set_num_threads(1)
    learn = load_learner(LAB01 / "export.pkl", cpu=True)  # the weights plus lab 01's preprocessing, no data
    steps = {"baseline": baseline, "change": change, "break": break_it}
    for mode in (steps if labkit.smoke() else [args.mode]):  # smoke runs all three on a few photos
        steps[mode](learn, pets, args.seed)


if __name__ == "__main__":
    main()
