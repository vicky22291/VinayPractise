#!/usr/bin/env python3
"""Run and verify ai-coding practice kits. Stdlib only.

    python3 ai-coding/kit.py list
    python3 ai-coding/kit.py start  <kit>          copy candidate/ to a run dir outside the repo, git init
    python3 ai-coding/kit.py next   <run_dir>      reveal the next part into the run dir
    python3 ai-coding/kit.py check  <run_dir>      run the hidden tests for every revealed part
                                       (--summary: counts only, no test names)
    python3 ai-coding/kit.py verify <kit|all>      starter fails part 1, answer key passes everything

The run dir lives under ~/ai-coding-runs/ so the AI assistant you practise with
never loads this repo's CLAUDE.md files or sees interviewer/. No state is stored
in the run dir: the kit is read from the run dir's name and the current part from
the "## Part N" headers in its TASK.md.
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.expanduser(os.environ.get("AI_CODING_RUNS", "~/ai-coding-runs"))
KIT_RE = re.compile(r"^\d\d-[a-z0-9-]+$")
PART_RE = re.compile(r"^## Part (\d+)\b", re.M)
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def kits():
    return sorted(d for d in os.listdir(HERE) if KIT_RE.match(d) and os.path.isdir(os.path.join(HERE, d)))


def kit_dir(name):
    path = os.path.join(HERE, name)
    if not (KIT_RE.match(name) and os.path.isdir(os.path.join(path, "candidate"))):
        sys.exit(f"unknown kit {name!r}; try: {', '.join(kits())}")
    return path


def parts_of(kdir):
    """Part numbers available in interviewer/parts/NN/ (part 1 is candidate/TASK.md)."""
    pdir = os.path.join(kdir, "interviewer", "parts")
    if not os.path.isdir(pdir):
        return []
    return sorted(int(p) for p in os.listdir(pdir) if p.isdigit())


def kit_of_run(run):
    name = os.path.basename(os.path.normpath(run))
    m = re.match(r"^(\d\d-[a-z0-9-]+?)-\d{8}-\d{4}$", name)
    if not m:
        sys.exit(f"{run} does not look like a run dir (<kit>-YYYYMMDD-HHMM)")
    return m.group(1), kit_dir(m.group(1))


def current_part(run):
    with open(os.path.join(run, "TASK.md")) as f:
        found = [int(n) for n in PART_RE.findall(f.read())]
    return max(found) if found else 1


def overlay(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True, ignore=IGNORE)


def reveal(kdir, run, part):
    """Copy parts/NN/files/ into the run dir and append parts/NN/TASK.md to its TASK.md."""
    pdir = os.path.join(kdir, "interviewer", "parts", f"{part:02d}")
    overlay(os.path.join(pdir, "files"), run)
    with open(os.path.join(pdir, "TASK.md")) as f:
        text = f.read()
    with open(os.path.join(run, "TASK.md"), "a") as f:
        f.write("\n\n---\n\n" + text.strip() + "\n")
    return text


def run_tests(run, start, pattern, quiet=False):
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", start, "-t", start, "-p", pattern]
    if not os.path.isdir(start):
        return 0, ""
    p = subprocess.run(cmd, cwd=run, env=ENV, capture_output=True, text=True, timeout=600)
    out = p.stdout + p.stderr
    if not quiet:
        print(out.rstrip())
    return p.returncode, out


def hidden_pattern(upto):
    return f"test_p[1-{upto}]_*.py"


def cmd_list(_):
    for k in kits():
        print(f"{k:40s} parts: {1 + len(parts_of(kit_dir(k)))}")


def cmd_start(a):
    kdir = kit_dir(a.kit)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    run = os.path.join(RUNS, f"{a.kit}-{stamp}")
    shutil.copytree(os.path.join(kdir, "candidate"), run, ignore=IGNORE)
    subprocess.run(["git", "init", "-q"], cwd=run, check=True)
    subprocess.run(["git", "add", "-A"], cwd=run, check=True)
    subprocess.run(["git", "commit", "-qm", "minute zero"], cwd=run, check=True)
    print(f"run dir: {run}\n")
    print("Open a second terminal there and start your AI assistant:")
    print(f"  cd {run}\n")
    with open(os.path.join(run, "TASK.md")) as f:
        print(f.read())


def cmd_next(a):
    run = os.path.abspath(a.run)
    _, kdir = kit_of_run(run)
    nxt = current_part(run) + 1
    if nxt not in parts_of(kdir):
        sys.exit("no more parts. Time for follow-up questions.")
    print(reveal(kdir, run, nxt))


def cmd_check(a):
    run = os.path.abspath(a.run)
    _, kdir = kit_of_run(run)
    upto = a.part or current_part(run)
    print("== your tests (tests/) ==")
    run_tests(run, os.path.join(run, "tests"), "test*.py")
    print(f"\n== hidden tests, parts 1 to {upto} ==")
    code, out = run_tests(run, os.path.join(kdir, "interviewer", "tests"), hidden_pattern(upto), quiet=a.summary)
    if a.summary:
        print("\n".join(l for l in out.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))))
    sys.exit(code)


def verify_one(name):
    kdir = kit_dir(name)
    hidden = os.path.join(kdir, "interviewer", "tests")
    last = 1 + len(parts_of(kdir))
    problems = []
    if not os.path.isfile(os.path.join(kdir, "candidate", "TASK.md")):
        problems.append("candidate/TASK.md missing")
    if parts_of(kdir) != list(range(2, last + 1)):
        problems.append(f"parts must be 02..NN with no gaps, got {parts_of(kdir)}")
    with tempfile.TemporaryDirectory() as tmp:
        starter = os.path.join(tmp, "starter")
        shutil.copytree(os.path.join(kdir, "candidate"), starter, ignore=IGNORE)
        code, _ = run_tests(starter, hidden, hidden_pattern(1), quiet=True)
        if code == 0:
            problems.append("starter already passes the part 1 hidden tests")

        solved = os.path.join(tmp, "solved")
        shutil.copytree(os.path.join(kdir, "candidate"), solved, ignore=IGNORE)
        for p in parts_of(kdir):
            overlay(os.path.join(kdir, "interviewer", "parts", f"{p:02d}", "files"), solved)
        overlay(os.path.join(kdir, "interviewer", "solution"), solved)
        code, out = run_tests(solved, hidden, hidden_pattern(last), quiet=True)
        if code != 0:
            problems.append("answer key fails hidden tests:\n" + out[-3000:])
        code, out = run_tests(solved, os.path.join(solved, "tests"), "test*.py", quiet=True)
        if code != 0:
            problems.append("answer key fails the visible tests:\n" + out[-3000:])
    print(f"{'OK  ' if not problems else 'FAIL'} {name} ({last} parts)")
    for p in problems:
        print("   - " + p)
    return not problems


def cmd_verify(a):
    names = kits() if a.kit == "all" else [a.kit]
    ok = all([verify_one(n) for n in names])
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("start"); p.add_argument("kit"); p.set_defaults(fn=cmd_start)
    p = sub.add_parser("next"); p.add_argument("run"); p.set_defaults(fn=cmd_next)
    p = sub.add_parser("check"); p.add_argument("run"); p.add_argument("--part", type=int)
    p.add_argument("--summary", action="store_true"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("verify"); p.add_argument("kit"); p.set_defaults(fn=cmd_verify)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
