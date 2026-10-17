"""38. BPE tokenizer: the merge loop, bytes vs characters.
A byte-level BPE (byte-pair encoding) trained on TinyShakespeare with Counter and max, tokens per
1,000 characters, then 10 test strings through bytes and through characters.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3). Nothing is random: --seed changes nothing.
"""
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and torch: it sets cache defaults

URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
TEXT = labkit.DATA / "nanoGPT" / "data" / "shakespeare_char" / "input.txt"  # the same file lab 39 uses
MERGES = 256  # --change uses 2 * MERGES
TESTS = [  # the 10 test strings: encode, decode, compare
    "To be, or not to be, that is the question.", "naïve café",
    "Your card was declined.", "Thanks, that worked 👍",
    "Refund of $25.00 sent for order 7781.", "Is this a dagger which I see before me?",
    "Grüße aus Zürich", "Reply to help@example.com",
    "東京で会いましょう", "Shall I compare thee to a summer's day?",
]

args = labkit.start(lab=38, device="cpu")


def merge(ids, pair, new_id):
    """Replace each occurrence of pair (two adjacent ids) with new_id, scanning left to right."""
    out, i = [], 0
    while i < len(ids):
        if i + 1 < len(ids) and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            out.append(new_id)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


def train(text, num_merges):
    """Byte-level BPE on the whole text. Returns the merges {pair: new_id} in learned order, and the token count."""
    ids = list(text.encode("utf-8"))  # Q: why does the vocabulary start with exactly 256 tokens?
    merges = {}
    for k in range(num_merges):
        counts = Counter(zip(ids, ids[1:]))  # every adjacent pair of ids, with how often it occurs
        pair = max(counts, key=counts.get)  # the most frequent pair; a tie goes to the pair counted first
        merges[pair] = 256 + k
        ids = merge(ids, pair, 256 + k)  # Q: what does one merge do to the length of ids?
    return merges, len(ids)


def vocab_of(merges):
    """Token id to the bytes it stands for: 256 single bytes, then one entry per merge."""
    vocab = {i: bytes([i]) for i in range(256)}
    for (a, b), new_id in merges.items():
        vocab[new_id] = vocab[a] + vocab[b]
    return vocab


def encode(text, merges):
    ids = list(text.encode("utf-8"))
    for pair, new_id in merges.items():  # Q: why must encode apply the merges in the order they were learned?
        ids = merge(ids, pair, new_id)
    return ids


def decode(ids, vocab):
    return b"".join(vocab[i] for i in ids).decode("utf-8", errors="replace")


def char_vocab(text):
    """Character level: one id per distinct character in text. Anything else gets the unknown id, len(chars)."""
    chars = sorted(set(text))
    return {ch: i for i, ch in enumerate(chars)}, chars + [chr(0xFFFD)]  # the unknown id decodes to the mark U+FFFD


def char_encode(s, stoi):
    """One id per character. A character missing from stoi gets the unknown id, len(stoi)."""
    return [stoi.get(ch, len(stoi)) for ch in s]


def char_decode(ids, itos):
    """Each id back to its character. The unknown id gives U+FFFD."""
    return "".join(itos[i] for i in ids)


def roundtrips(enc, dec, label):
    """How many of the 10 test strings come back unchanged after encode, then decode."""
    passed = 0
    for s in TESTS:
        ids = enc(s)
        back = dec(ids)
        passed += back == s
        if not labkit.smoke():
            print(f"{label:<7} chars={len(s):<3} bytes={len(s.encode('utf-8')):<3} tokens={len(ids):<3} "
                  f"{'ok  ' if back == s else 'FAIL'} {s!r} -> {back!r}", flush=True)
    return passed


def bpe_step(text, num_merges):
    """Train num_merges merges on text and time it. Returns tokens per 1,000 characters, seconds, round trips."""
    t0 = labkit.clock()
    merges, tokens = train(text, num_merges)
    seconds = labkit.clock() - t0
    vocab = vocab_of(merges)
    if labkit.smoke():  # smoke: encode must give the token count training ended with
        assert len(encode(text, merges)) == tokens, "encode and train disagree"
    else:
        print("first and last 10 merges:", [vocab[256 + k] for k in [*range(10), *range(num_merges - 10, num_merges)]], flush=True)
    passed = roundtrips(lambda s: encode(s, merges), lambda t: decode(t, vocab), f"bpe{num_merges}")
    return 1000 * tokens / len(text), seconds, passed


if args.mode == "download":
    labkit.fetch(URL, TEXT, size=1_115_394)
    sys.exit(0)

if not TEXT.exists():
    print(f"MISSING {TEXT}: run python scripts/38_bpe_tokenizer.py --download first", flush=True)
    sys.exit(2)
text = TEXT.read_text(encoding="utf-8")
if labkit.smoke():
    text = text[:20_000]  # smoke: the first 20,000 characters and 20 or 40 merges, same code path
timing = dict(device="cpu", batch="full_text", warmup=0, n=1, stat="median")

if args.mode in ("baseline", "smoke"):  # P1: 256 merges on all of TinyShakespeare
    raw = 1000 * len(text.encode("utf-8")) / len(text)  # 0 merges: one token per byte
    labkit.result("baseline.tokens_per_1k_chars_0_merges", raw, unit="tokens/1k_chars")
    p1, seconds, passed = bpe_step(text, 20 if labkit.smoke() else MERGES)
    labkit.result("P1.tokens_per_1k_chars", p1, unit="tokens/1k_chars")
    labkit.result("baseline.train_seconds", seconds, unit="s", **timing)
    labkit.result("baseline.byte_roundtrip", passed, unit="of_10")

if args.mode in ("change", "smoke"):  # P2: 512 merges, everything else the same
    per_1k, seconds, passed = bpe_step(text, 40 if labkit.smoke() else 2 * MERGES)
    labkit.result("P2.tokens_per_1k_chars", per_1k, unit="tokens/1k_chars")
    if not labkit.smoke():  # smoke keeps the P1 its own baseline step just made
        p1 = labkit.prior("P1.tokens_per_1k_chars")  # from your --baseline run with the same seed
    if p1 is None:
        print("NOTE run --baseline with this seed first to get P2.delta_vs_256", flush=True)
    else:
        labkit.result("P2.delta_vs_256", per_1k - p1, unit="tokens/1k_chars")
    labkit.result("change.train_seconds", seconds, unit="s", **timing)
    labkit.result("change.byte_roundtrip", passed, unit="of_10")

if args.mode in ("break", "smoke"):  # P3: a character-level vocabulary instead of bytes
    stoi, itos = char_vocab(text)
    passed = roundtrips(lambda s: char_encode(s, stoi), lambda t: char_decode(t, itos), "chars")
    labkit.result("break.char_vocab_size", len(stoi), unit="characters")
    labkit.result("P3.char_roundtrip", passed, unit="of_10")
