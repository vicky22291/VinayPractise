"""labkit: the small shared header every lab script imports.

It does five jobs, so each lab script can stay about the concept:
parse the run mode, print the HW and SEED lines, seed every random number
generator, download a file once, and print results in one format.

    RESULT <step>.<name>=<value> [unit=...] [seed=...] [device=...] [n=...]

<step> is P1, P2, P3 (P1b in lab 39) for a value a prediction asks about,
or the mode name (baseline, change, break, ...) for any other recorded value.
In --smoke mode the value is hidden: the line says the step ran, not what it got.

Scripts find this file by walking up from their own folder, and import it
before numpy, torch or transformers (it sets cache defaults under ~/ml-data):

    sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents
                                if (p / "labkit.py").exists())))
    import labkit
"""
import argparse
import contextlib
import fcntl
import importlib.metadata
import json
import os
import platform
import random
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile
from pathlib import Path

DATA = Path(os.environ.get("ML_DATA", "~/ml-data")).expanduser()
MODES = ("download", "smoke", "baseline", "change", "break")
os.environ.setdefault("HF_HOME", str(DATA / "hf"))  # import labkit before transformers
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
_run = argparse.Namespace(lab="00", mode="smoke", seed=0, device="cpu")


def start(lab, device="cpu", extra_modes=(), description=None):
    """Parse --<mode> and --seed, seed the RNGs, print the HW and SEED lines.

    Import numpy, torch or mlx before calling this, so their RNGs get seeded.
    """
    modes = MODES + tuple(extra_modes)
    ap = argparse.ArgumentParser(description=description)
    group = ap.add_mutually_exclusive_group(required=True)
    for m in modes:
        group.add_argument(f"--{m}", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    args.mode = next(m for m in modes if getattr(args, m))
    args.lab, args.device = f"{int(lab):02d}", device
    _run.__dict__.update(vars(args))
    seed_all(args.seed)
    print(hw_line(device), flush=True)
    print(f"SEED seed={args.seed} pythonhashseed={os.environ.get('PYTHONHASHSEED', 'unset')}", flush=True)
    return args


def smoke():
    return _run.mode == "smoke"


def seed_all(seed):
    random.seed(seed)
    if "numpy" in sys.modules:
        sys.modules["numpy"].random.seed(seed)
    if "torch" in sys.modules:
        sys.modules["torch"].manual_seed(seed)  # also seeds MPS
    if "mlx.core" in sys.modules:
        sys.modules["mlx.core"].random.seed(seed)


def pick_device():
    """mps when the Apple GPU is usable, else cpu. Light labs pass "cpu" instead."""
    import torch
    return "mps" if torch.backends.mps.is_available() else "cpu"


def sync(device):
    """Wait for queued GPU work. Call it before every clock read on mps or mlx."""
    if device == "mps":
        sys.modules["torch"].mps.synchronize()
    elif device == "mlx":
        sys.modules["mlx.core"].synchronize()


def clock(device="cpu"):
    sync(device)
    return time.perf_counter()


def _hw_info():
    cache = DATA / ".hw.json"
    with contextlib.suppress(Exception):
        return json.loads(cache.read_text())

    def sysctl(key):
        out = subprocess.run(["sysctl", "-n", key], capture_output=True, text=True)
        return out.stdout.strip()

    info = {"chip": platform.processor() or "unknown", "cpu": os.cpu_count(), "gpu": "n/a", "mem_gib": "n/a"}
    if sys.platform == "darwin":
        info["chip"] = sysctl("machdep.cpu.brand_string") or info["chip"]
        info["mem_gib"] = round(int(sysctl("hw.memsize") or 0) / 2**30)
        with contextlib.suppress(Exception):
            out = subprocess.run(["system_profiler", "SPDisplaysDataType", "-json"],
                                 capture_output=True, text=True, timeout=30)
            info["gpu"] = int(json.loads(out.stdout)["SPDisplaysDataType"][0]["sppci_cores"])
    with contextlib.suppress(OSError):
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(info))
    return info


def hw_line(device):
    info = _hw_info()
    parts = [f"chip='{info['chip']}'", f"cpu={info['cpu']}", f"gpu={info['gpu']}",
             f"mem_gib={info['mem_gib']}", f"macos={platform.mac_ver()[0] or 'n/a'}",
             f"python={platform.python_version()}"]
    for pkg in ("torch", "mlx"):
        with contextlib.suppress(importlib.metadata.PackageNotFoundError):
            if pkg == "torch" or device == "mlx":
                parts.append(f"{pkg}={importlib.metadata.version(pkg)}")
    return "HW " + " ".join(parts) + f" device={device}"


def _fmt(v):
    if hasattr(v, "item"):  # numpy or torch scalar
        v = v.item()
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v).replace(" ", "_")


def result(name, value, smoke_ok=False, **tags):
    """Print one RESULT line and keep the value for later modes (see prior()).

    In --smoke mode it prints only 'SMOKE <name> ok', unless smoke_ok=True
    (for values no prediction asks about, such as seconds per iteration).
    """
    step = name.split(".")[0]
    if "." not in name or not step:
        raise ValueError(f"RESULT names look like <step>.<name>, got {name!r}")
    if smoke() and not smoke_ok:
        print(f"SMOKE {name} ok", flush=True)
        return
    tags.setdefault("seed", _run.seed)
    tag_text = "".join(f" {k}={_fmt(t)}" for k, t in tags.items())
    print(f"{'SMOKE' if smoke() else 'RESULT'} {name}={_fmt(value)}{tag_text}", flush=True)
    if not smoke():
        store = DATA / "runs" / f"lab{_run.lab}" / f"seed{_run.seed}.json"
        store.parent.mkdir(parents=True, exist_ok=True)
        saved = json.loads(store.read_text()) if store.exists() else {}
        saved[name] = value.item() if hasattr(value, "item") else value
        store.write_text(json.dumps(saved, indent=1))


def prior(name, seed=None):
    """A value an earlier mode of this lab printed with the same seed, or None."""
    store = DATA / "runs" / f"lab{_run.lab}" / f"seed{_run.seed if seed is None else seed}.json"
    return json.loads(store.read_text()).get(name) if store.exists() else None


def models_dir(lab):
    """Where a lab saves models that a later lab reads (seed 0 only)."""
    path = DATA / "models" / f"lab{int(lab):02d}"
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextlib.contextmanager
def locked(path):
    """Hold a file lock next to path, so two labs that fetch the same data take turns."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{path}.lock", "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        yield


def fetch(url, dest, size=None, tries=3):
    """Download url to dest once. Atomic: a partial file never looks finished."""
    dest = Path(dest).expanduser()
    with locked(dest):
        if dest.exists() and (size is None or dest.stat().st_size == size):
            print(f"HAVE {dest} {dest.stat().st_size / 1e6:.1f} MB", flush=True)
            return dest
        tmp = dest.with_name(f"{dest.name}.{os.getpid()}.part")
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ml-learning labkit)"})
        t0 = time.perf_counter()
        for attempt in range(1, tries + 1):
            try:
                with urllib.request.urlopen(request, timeout=60) as r, open(tmp, "wb") as f:
                    shutil.copyfileobj(r, f, 1 << 20)
                if size is not None and tmp.stat().st_size != size:
                    raise OSError(f"expected {size} bytes, got {tmp.stat().st_size}")
                break
            except OSError as e:
                tmp.unlink(missing_ok=True)
                if attempt == tries:
                    raise
                print(f"RETRY {url} ({e})", flush=True)
                time.sleep(2 * attempt)
        os.replace(tmp, dest)
        print(f"FETCH {dest} {dest.stat().st_size / 1e6:.1f} MB in {time.perf_counter() - t0:.0f} s", flush=True)
        return dest


def extract(archive, dest_dir):
    """Unpack a .tgz, .tar.gz or .zip into dest_dir once, refusing unsafe paths."""
    archive, dest_dir = Path(archive), Path(dest_dir)
    marker = dest_dir / f".extracted-{archive.name}"
    with locked(marker):
        if marker.exists():
            return dest_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as z:
                for name in z.namelist():
                    if name.startswith("/") or ".." in Path(name).parts:
                        raise ValueError(f"unsafe path in {archive}: {name}")
                z.extractall(dest_dir)
        else:
            with tarfile.open(archive) as t:
                t.extractall(dest_dir, filter="data")
        marker.touch()
        print(f"EXTRACT {archive.name} -> {dest_dir}", flush=True)
        return dest_dir


def openml(data_id):
    """An OpenML dataset as one DataFrame (features plus target), cached in DATA/openml."""
    from sklearn.datasets import fetch_openml
    home = DATA / "openml"
    with locked(home / f"{data_id}"):
        return fetch_openml(data_id=data_id, as_frame=True, parser="auto", data_home=str(home)).frame
