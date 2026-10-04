"""Exercise 03: naive RAG. Retrieve top-k chunks, put them in the prompt, answer with citations.

Run:  python rag.py "what is the default ef_search in my vector index note"
      python rag.py "..." --k 20 --show-prompt
      python rag.py "..." --closed-book          (no retrieval: what the model knows alone)
      python rag.py "..." --no-grounding         (retrieve, but drop the "only use the notes" rule)
      python rag.py "..." --k 20 --num-ctx 2048  (context window smaller than the prompt)
"""
import argparse

from llm import CHAT_MODEL, LLM_BASE_URL, NUM_CTX, chat
from search import retrieve

GROUNDED = ("You answer questions about the user's system-design notes. Use ONLY the "
            "numbered notes below. Cite every claim like [2]. If the notes do not "
            "contain the answer, reply exactly: I don't know based on the notes.")
LOOSE = "You answer questions about system design. The notes below may help."


def build_prompt(question, rows, grounded=True):
    notes = "\n\n".join(f"[{i}] {r[1]} :: {r[2]}\n{r[3]}" for i, r in enumerate(rows, 1))
    system = GROUNDED if grounded else LOOSE
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"Notes:\n{notes}\n\nQuestion: {question}"}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--mode", choices=["vector", "text", "hybrid"], default="vector")
    ap.add_argument("--closed-book", action="store_true")
    ap.add_argument("--no-grounding", action="store_true")
    ap.add_argument("--num-ctx", type=int, default=NUM_CTX)
    ap.add_argument("--show-prompt", action="store_true")
    a = ap.parse_args()

    if a.closed_book:
        rows, t = [], {"embed_ms": 0, "search_ms": 0}
        messages = [{"role": "user", "content": a.question}]
    else:
        rows, t = retrieve(a.question, a.k, a.mode)
        messages = build_prompt(a.question, rows, grounded=not a.no_grounding)

    if a.show_prompt:
        print("----- prompt -----\n" + "\n\n".join(m["content"] for m in messages)[:3000])
        print("----- end prompt (first 3000 chars) -----\n")

    r = chat(messages, num_ctx=a.num_ctx)
    print(r["content"], "\n")
    for i, row in enumerate(rows, 1):
        print(f"  [{i}] {row[1]} :: {row[2][:60]}")
    prompt_chars = sum(len(m["content"]) for m in messages)
    ctx = "provider default" if LLM_BASE_URL else a.num_ctx
    print(f"\nmodel {CHAT_MODEL}, context {ctx}, prompt {prompt_chars} chars -> "
          f"{r['prompt_tokens']} tokens seen, {r['gen_tokens']} generated")
    timing = f"embed {t['embed_ms']:.0f} ms | search {t['search_ms']:.0f} ms | "
    if r["prompt_ms"] is not None:   # Ollama native reports prefill and decode separately
        timing += (f"prefill {r['prompt_ms']:.0f} ms | decode {r['gen_ms']:.0f} ms "
                   f"({r['gen_tokens'] / max(r['gen_ms'], 1) * 1000:.0f} tok/s) | ")
    print(timing + f"total {t['embed_ms'] + t['search_ms'] + r['wall_ms']:.0f} ms")


if __name__ == "__main__":
    main()
