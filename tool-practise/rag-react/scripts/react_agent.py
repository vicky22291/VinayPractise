"""Exercise 06: ReAct from scratch, no framework. Reason + Act in a loop:
the model writes a Thought and an Action as plain text, we parse the Action,
run the tool, and send the result back as an Observation. Repeat until finish[].

Two ways to drive the model:
  chat (default)  each step is a chat turn; the chat template ends the turn
  --raw           one growing text transcript the model continues, like the
                  2022 paper's completion API (Ollama only)

Run:  python react_agent.py "How many MB does a 1% Bloom filter need for 100 million keys?"
      python react_agent.py "..." --raw --no-stop   (break it: the model writes the tools' results)
      python react_agent.py "..." --max-steps 1     (break it: budget runs out)
"""
import argparse
import ast
import operator
import re

from llm import CHAT_MODEL, chat, complete
from search import retrieve

SYSTEM = """You answer questions about the user's system-design notes. Work in steps.
Each turn write exactly one Thought line and one Action line, then stop:

Thought: <what you know so far and what you still need>
Action: <tool>[<input>]

Tools:
  search[query]     search the notes, returns the 3 best passages
  calculate[expr]   arithmetic only, e.g. calculate[3 * 86400 / 1000]
  finish[answer]    the final answer, naming the note files you used

After each Action you receive an Observation. Never write an Observation yourself.
Search before answering. Never guess a number that a search could give you."""

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}


def calculate(expr):
    """Safe arithmetic: walk the AST, allow only numbers and + - * / **."""
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp):
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp):
            return OPS[type(n.op)](ev(n.operand))
        raise ValueError(f"not arithmetic: {expr!r}")
    return str(ev(ast.parse(expr.replace(",", ""), mode="eval").body))


def search(query):
    rows, _ = retrieve(query, k=3, mode="hybrid")
    return "\n".join(f"({r[1]} :: {r[2]}) {r[3][:600]}" for r in rows)


TOOLS = {"search": search, "calculate": calculate}


def parse_action(text):
    """First 'Action: tool[arg]' in the text, and where it ends. The arg runs to the
    last ']' before the next Thought/Observation/Action, so answers may hold brackets."""
    m = re.search(r"Action:\s*(\w+)\s*\[", text)
    if not m:
        return None, None, len(text)
    rest = text[m.end():]
    nxt = re.search(r"\s*(?:Observation|Thought|Action):", rest)
    seg = rest[:nxt.start()] if nxt else rest
    close = seg.rfind("]")
    arg = seg[:close] if close >= 0 else seg
    return m.group(1), arg.strip(), m.end() + (close + 1 if close >= 0 else len(seg))


def run(question, max_steps=6, use_stop=True, raw=False):
    stop = ["Observation:"] if use_stop else None
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Question: {question}"}]
    transcript = f"{SYSTEM}\n\nQuestion: {question}\n"
    tot = {"calls": 0, "prompt_tokens": 0, "gen_tokens": 0, "wall_ms": 0}
    for step in range(1, max_steps + 1):
        r = complete(transcript, stop) if raw else chat(messages, stop=stop)
        tot["calls"] += 1
        for key in ("prompt_tokens", "gen_tokens", "wall_ms"):
            tot[key] += r[key]
        print(f"\n--- step {step}: {r['prompt_tokens']} prompt tokens, {r['wall_ms']:.0f} ms ---\n{r['content']}")
        tool, arg, end = parse_action(r["content"])
        extra = r["content"][end:].strip()
        if extra:   # one action per turn is enforced HERE, not by the stop sequence
            print(f"!! {len(extra)} chars after the first Action: the model invented the next steps itself. Discarded.")
        text = r["content"][:end]
        messages.append({"role": "assistant", "content": text})
        transcript += text + "\n"
        if tool == "finish":
            print(f"\nANSWER: {arg}")
            break
        try:
            obs = TOOLS[tool](arg) if tool in TOOLS else f"Error: unknown or missing Action ({tool})"
        except Exception as e:  # tool errors go back to the model, not up the stack
            obs = f"Error: {e}"
        print(f"Observation: {obs[:240]}{' ...' if len(obs) > 240 else ''}")
        messages.append({"role": "user", "content": f"Observation: {obs}"})
        transcript += f"Observation: {obs}\n"
    else:
        print(f"\nSTOPPED: {max_steps} steps used, no finish[]. Return a fallback, never loop forever.")
    print(f"\n{CHAT_MODEL}: {tot['calls']} LLM calls, {tot['prompt_tokens']} prompt tokens, "
          f"{tot['gen_tokens']} generated tokens, {tot['wall_ms'] / 1000:.1f} s")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--max-steps", type=int, default=6)
    ap.add_argument("--no-stop", action="store_true")
    ap.add_argument("--raw", action="store_true", help="text completion instead of chat turns")
    a = ap.parse_args()
    run(a.question, a.max_steps, use_stop=not a.no_stop, raw=a.raw)
