"""Shared helpers: embeddings + chat over HTTP (stdlib only), pgvector via psycopg.

Embeddings always come from local Ollama: the index is tied to the embedding
model, so changing it means re-embedding every chunk (exercise 04).

The chat model is swappable. Default is local Ollama's native API, which also
reports the prefill / decode split and lets us set the context window. Set
LLM_BASE_URL to use any OpenAI-compatible endpoint instead:

  LLM_BASE_URL=http://localhost:11434/v1 CHAT_MODEL=qwen2.5:7b          (Ollama, OpenAI format)
  LLM_BASE_URL=https://openrouter.ai/api/v1 CHAT_MODEL=anthropic/claude-haiku-4.5
      (key from LLM_API_KEY, else OPENROUTER_API_KEY)
"""
import json
import os
import time
import urllib.error
import urllib.request

import psycopg

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "").rstrip("/")   # empty = Ollama native API
LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
TEMPERATURE = os.environ.get("LLM_TEMPERATURE", "0")   # set to "" for models that reject it
CHAT_MODEL = os.environ.get("CHAT_MODEL", "qwen2.5:7b")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")
PG_DSN = os.environ.get("PG_DSN", "postgresql://postgres:rag@localhost:5432/rag")
NUM_CTX = int(os.environ.get("NUM_CTX", "8192"))   # tokens the model can see (Ollama native only)


def _post(url, body, headers=None):
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:   # show the server's reason, not just "400"
        raise RuntimeError(f"HTTP {e.code} from {url}: {e.read().decode()[:300]}") from None


def embed(texts, kind="document", prefix=True, model=EMBED_MODEL):
    """Batch-embed a list of strings. nomic-embed-text is trained with task
    prefixes: 'search_document: ' on chunks, 'search_query: ' on questions."""
    if prefix and model.startswith("nomic"):
        texts = [f"search_{kind}: {t}" for t in texts]
    return _post(OLLAMA + "/api/embed", {"model": model, "input": texts})["embeddings"]


def chat(messages, stop=None, tools=None, num_ctx=NUM_CTX, model=CHAT_MODEL):
    """One non-streaming chat call. Returns the same dict shape for both backends:
    message (append it to history), content, tool_calls [(id, name, args)], token
    counts, timings. prompt_ms / gen_ms are None when the backend does not report them."""
    t0 = time.perf_counter()
    if LLM_BASE_URL:
        body = {"model": model, "messages": messages}
        body.update({"temperature": float(TEMPERATURE)} if TEMPERATURE else {})
        body.update({"stop": stop} if stop else {})
        body.update({"tools": tools} if tools else {})
        r = _post(LLM_BASE_URL + "/chat/completions", body, {"Authorization": f"Bearer {LLM_API_KEY}"})
        msg, usage = r["choices"][0]["message"], r.get("usage") or {}
        calls = [(c["id"], c["function"]["name"], json.loads(c["function"]["arguments"] or "{}"))
                 for c in msg.get("tool_calls") or []]
        out = {"prompt_tokens": usage.get("prompt_tokens", 0),
               "gen_tokens": usage.get("completion_tokens", 0), "prompt_ms": None, "gen_ms": None}
    else:
        options = {"temperature": float(TEMPERATURE or 0), "seed": 7, "num_ctx": num_ctx}
        options.update({"stop": stop} if stop else {})
        body = {"model": model, "messages": messages, "stream": False, "options": options}
        body.update({"tools": tools} if tools else {})
        r = _post(OLLAMA + "/api/chat", body)
        msg = r["message"]
        calls = [(c["function"]["name"], c["function"]["name"], c["function"]["arguments"])
                 for c in msg.get("tool_calls") or []]
        out = {"prompt_tokens": r.get("prompt_eval_count", 0), "gen_tokens": r.get("eval_count", 0),
               "prompt_ms": r.get("prompt_eval_duration", 0) / 1e6,   # prefill
               "gen_ms": r.get("eval_duration", 0) / 1e6}             # decode
    out.update(message=msg, content=(msg.get("content") or "").strip(), tool_calls=calls,
               wall_ms=(time.perf_counter() - t0) * 1000)
    return out


def complete(prompt, stop=None, model=CHAT_MODEL):
    """Raw text completion with no chat template (Ollama only). This is how the 2022
    ReAct paper drove its model: it just continues the transcript it is given."""
    options = {"temperature": 0, "seed": 7, "num_ctx": NUM_CTX, "num_predict": 400}
    options.update({"stop": stop} if stop else {})
    r = _post(OLLAMA + "/api/generate",
              {"model": model, "prompt": prompt, "raw": True, "stream": False, "options": options})
    return {"content": r["response"].strip(), "prompt_tokens": r.get("prompt_eval_count", 0),
            "gen_tokens": r.get("eval_count", 0), "wall_ms": r.get("total_duration", 0) / 1e6}


def tool_result(call, content):
    """The message that hands a tool's output back to the model, in the backend's format."""
    if LLM_BASE_URL:
        return {"role": "tool", "tool_call_id": call[0], "content": content}
    return {"role": "tool", "tool_name": call[1], "content": content}


def db():
    return psycopg.connect(PG_DSN, autocommit=True)


def vec(v):
    """pgvector's text format: '[0.1,0.2,...]'. Cast with ::vector in SQL."""
    return "[" + ",".join(f"{x:.7g}" for x in v) + "]"
