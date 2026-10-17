"""01. Pet breeds: reuse all, part or none of a pretrained network. One ResNet-34, three ways
to start it on 37 breeds: fine-tune all of it, train only a new head, or start from random weights.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import contextlib
import statistics
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy, torch, transformers: it sets cache defaults
import torch
from fastai.vision.all import (Callback, CategoryBlock, DataBlock, ImageBlock, Normalize, RandomSplitter,
                               RegexLabeller, Resize, aug_transforms, error_rate, get_image_files,
                               imagenet_stats, resnet34, set_seed, using_attr, vision_learner)
from torchvision.models import ResNet34_Weights

PETS_URL, PETS_BYTES = "https://s3.amazonaws.com/fast-ai-imageclas/oxford-iiit-pet.tgz", 811_706_944
OXFORD = [("https://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz", 791_918_971),
          ("https://www.robots.ox.ac.uk/~vgg/data/pets/data/annotations.tar.gz", 19_173_078)]
PETS = labkit.DATA / "oxford-iiit-pet"  # images/ holds Abyssinian_1.jpg ... yorkshire_terrier_99.jpg
BATCH, WORKERS, BASE_LR = 64, 0, 2e-3  # fastai 2.8 sets workers to 0 on macOS: images load in this process
PARKHI_2012 = 0.5921                    # Parkhi et al. 2012, accuracy on the 37 breeds


def download():
    try:
        labkit.extract(labkit.fetch(PETS_URL, labkit.DATA / "oxford-iiit-pet.tgz", size=PETS_BYTES), labkit.DATA)
    except OSError as e:  # the fastai mirror failed: the Oxford originals unpack to the same images/ folder
        print(f"RETRY Oxford originals ({e})", flush=True)
        for url, size in OXFORD:
            labkit.extract(labkit.fetch(url, PETS / Path(url).name, size=size), PETS)
    weights = ResNet34_Weights.IMAGENET1K_V1  # what fastai loads for a pretrained resnet34
    path = Path(torch.hub.get_dir()) / "checkpoints" / Path(weights.url).name
    with labkit.locked(path): weights.get_state_dict(progress=False, check_hash=True)
    print(f"HAVE {path} {path.stat().st_size / 1e6:.1f} MB", flush=True)
    print(f"HAVE {PETS / 'images'} {len(get_image_files(PETS / 'images'))} images", flush=True)


def pet_dataloaders(seed, device):
    files = sorted(get_image_files(PETS / "images"))
    if labkit.smoke():
        files = files[::20]  # smoke: about 10 images per breed, same code path
    block = DataBlock(
        blocks=(ImageBlock, CategoryBlock),
        get_y=using_attr(RegexLabeller(r"^(.*)_\d+.jpg$"), "name"),  # great_pyrenees_17.jpg -> great_pyrenees
        splitter=RandomSplitter(valid_pct=0.2, seed=42 + seed),
        # Q: why resize every image to 448 px first, and only then augment and crop it to 224 px?
        item_tfms=Resize(448),  # fastbook uses 460; on MPS its uneven adaptive-pool step fails (pytorch #96056)
        batch_tfms=[*aug_transforms(size=224, min_scale=0.75), Normalize.from_stats(*imagenet_stats)])
    return block.dataloaders(files, bs=BATCH, num_workers=WORKERS, device=device)


class EpochTimer(Callback):
    "Seconds per epoch (train plus validation) after its first batch, GPU synchronized before every clock read."
    def __init__(self, on): self.on, self.secs = on, []
    def after_batch(self):  # batch 1 can carry one-time start-up work, so the clock starts after it
        if self.training and self.iter == 0: self.t0 = labkit.clock(self.on)
    def after_epoch(self): self.secs.append(labkit.clock(self.on) - self.t0)


def quiet(learn):
    "In --smoke, hide fastai's progress bar and per-epoch table. Otherwise change nothing."
    stack = contextlib.ExitStack()
    if labkit.smoke():
        stack.enter_context(learn.no_bar())
        stack.enter_context(learn.no_logging())
    return stack


def trainable(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def last_error_rate(learn):
    return float(learn.final_record[-1])  # fastai's last epoch: [train_loss, valid_loss, error_rate]


def timing(dls, n):
    return dict(unit="s", device=torch.device(dls.device).type, batch=BATCH,
                workers=dls.train.fake_l.num_workers, warmup=1, n=n, stat="median")


def baseline(dls, seed, timer):
    learn = vision_learner(dls, resnet34, metrics=error_rate)  # ImageNet body + new head; body frozen
    frozen = trainable(learn.model)
    with quiet(learn):
        # Q: fine_tune(1) runs two epochs. What does each epoch train, and at what learning rate?
        learn.fine_tune(1, base_lr=BASE_LR, cbs=timer)
    labkit.result("P1.error_rate", last_error_rate(learn), unit="fraction")
    labkit.result("baseline.trainable_frozen", frozen, unit="params")
    labkit.result("baseline.trainable_unfrozen", trainable(learn.model), unit="params")
    labkit.result("baseline.sec_per_epoch_frozen", timer.secs[0], **timing(dls, 1))
    labkit.result("baseline.sec_per_epoch_unfrozen", timer.secs[1], **timing(dls, 1))
    with tempfile.TemporaryDirectory() as tmp:  # seed 0 saves for lab 02; other runs only measure the size
        out = labkit.models_dir(1) if seed == 0 and not labkit.smoke() else Path(tmp)
        learn.export(out / "export.pkl")
        names = sorted(learn.dls.valid_ds.items, key=lambda f: f.name)
        (out / "valid_files.txt").write_text("".join(f"{f.relative_to(labkit.DATA)}\n" for f in names))
        labkit.result("baseline.export_mb", (out / "export.pkl").stat().st_size / 1e6, unit="MB")


class KeepFrozen(Callback):
    "Freeze the body again at the start of every fit, so fine_tune's unfreeze step does not take effect."
    def before_fit(self): self.learn.freeze()


def change(dls, seed, timer):
    learn = vision_learner(dls, resnet34, metrics=error_rate)  # the same frozen start as the baseline
    with quiet(learn):
        # Q: the body stays frozen for both epochs. What in it still trains, and why?
        learn.fine_tune(1, base_lr=BASE_LR, cbs=[timer, KeepFrozen()])  # the baseline's call, body kept frozen
    err = last_error_rate(learn)
    labkit.result("P2.error_rate", err, unit="fraction")
    p1 = labkit.prior("P1.error_rate")
    if p1 is not None:
        labkit.result("P2.delta_vs_P1", (err - p1) * 100, unit="points")
    labkit.result("change.sec_per_epoch", statistics.median(timer.secs), **timing(dls, len(timer.secs)))


def break_it(dls, seed, timer):
    learn = vision_learner(dls, resnet34, pretrained=False, metrics=error_rate)  # random weights, all trainable
    with quiet(learn):
        learn.fit_one_cycle(2, BASE_LR, cbs=timer)
    err = last_error_rate(learn)
    labkit.result("P3.error_rate", err, unit="fraction")
    labkit.result("break.sec_per_epoch", statistics.median(timer.secs), **timing(dls, len(timer.secs)))
    errs = [e for e in (labkit.prior("P1.error_rate"), labkit.prior("P2.error_rate")) if e is not None] + [err]
    labkit.result("break.best_accuracy", 1 - min(errs), unit="fraction", runs=len(errs))
    labkit.result("break.best_minus_parkhi", (1 - min(errs) - PARKHI_2012) * 100, unit="points")


def main():
    args = labkit.start(lab=1, device=labkit.pick_device())
    if args.mode == "download":
        return download()
    if not (PETS / "images").exists():
        sys.exit("no images: run python scripts/01_pet_breeds.py --download first")
    set_seed(args.seed, reproducible=True)
    dls = pet_dataloaders(args.seed, args.device)
    print(f"DATA device={dls.device} workers={dls.train.fake_l.num_workers} batch={BATCH} "
          f"train={len(dls.train_ds)} valid={len(dls.valid_ds)} classes={dls.c}", flush=True)
    steps = {"baseline": baseline, "change": change, "break": break_it}
    for mode in (steps if labkit.smoke() else [args.mode]):  # smoke runs all three on tiny data
        steps[mode](dls, args.seed, EpochTimer(args.device))


if __name__ == "__main__":  # safe if workers are turned on: macOS DataLoader workers re-import this file
    main()
