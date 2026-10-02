"""LLM vs Jev — The 500 Customer Message Race

Setup:
    pip install typesafe-sdk anthropic rich
    export TYPESAFE_API_KEY=...
    export ANTHROPIC_API_KEY=...
    python generate_messages.py

Run:
    python race.py 5      # try 5 messages first (check the response format)
    python race.py        # full race, 500 messages
"""
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field

from anthropic import AsyncAnthropic
from rich.columns import Columns
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, Score

# ---------------- Settings ----------------
CONCURRENCY = int(os.getenv("CONCURRENCY", "10"))          # same parallelism for both sides
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5")
LLM_PRICE_IN = float(os.getenv("LLM_PRICE_IN", "3.00"))    # $ per 1M input tokens (update to current pricing)
LLM_PRICE_OUT = float(os.getenv("LLM_PRICE_OUT", "15.00")) # $ per 1M output tokens (update to current pricing)
JEV_PRICE_IN = 0.042                                        # $ per 1M input tokens, output is free
JEV_ONLY = os.getenv("JEV_ONLY") == "1"  # skip the LLM to save credits

# CATEGORIES = {
#     "refund": "The customer wants to return a product or get their money back",
#     "shipping": "Delivery, tracking, delays, or address changes",
#     "product_question": "A question about a product's features or specs",
#     "complaint": "A complaint about service, courier, packaging, or the product",
#     "spam": "Advertising, scams, or messages unrelated to being a customer",
# }
CATEGORIES = {
    "refund": "The customer wants to return or exchange a product, or get their money back",
    "shipping": "A question or request about delivery status, tracking, or address changes",
    "product_question": "A question about a product's features or specs",
    "complaint": "The customer is unhappy with service, courier, packaging, delivery speed, or the product",
    "spam": "Advertising, scams, or messages unrelated to being a customer",
}
ANGER = ["calm", "annoyed", "angry", "furious"]
URGENT_Q = "Does this message require immediate attention from a human agent?"

# Jev: questions are defined as types, so the answer format is guaranteed
JEV_QUESTIONS = {
    "category": Choice(instructions="Which category does this customer message belong to?", criteria=CATEGORIES),
    "anger": Score(instructions="How angry is the customer who wrote this message?", criteria=ANGER),
    "urgent": Noul(instructions=URGENT_Q),
}

# LLM: the same questions described in a prompt, asking for JSON
LLM_SYSTEM = f"""You are a customer support classifier. Read the message and return ONLY the JSON below, nothing else.
{{"category": <one of: {", ".join(CATEGORIES)}>, "anger": <number between 0 and 1, 0=calm 1=furious>, "urgent": <true or false>}}
Category definitions: {json.dumps(CATEGORIES)}
urgent: {URGENT_Q}"""


# ---------------- Stats ----------------
@dataclass
class Stats:
    name: str
    price_in: float
    price_out: float
    processed: int = 0
    done: int = 0
    api_errors: int = 0
    bad_json: int = 0
    in_tok: int = 0
    out_tok: int = 0
    cat_ok: int = 0
    urgent_ok: int = 0
    anger_err: float = 0.0
    start: float = 0.0
    end: float | None = None
    rows: dict = field(default_factory=dict)

    def elapsed(self) -> float:
        return (self.end or time.perf_counter()) - self.start

    def cost(self) -> float:
        return self.in_tok / 1e6 * self.price_in + self.out_tok / 1e6 * self.price_out

    def record(self, msg, category, anger, urgent):
        self.done += 1
        self.cat_ok += category == msg["category"]
        self.urgent_ok += urgent == msg["urgent"]
        self.anger_err += abs(anger - msg["anger"])
        self.rows[msg["id"]] = {"category": category, "anger": round(anger, 2), "urgent": urgent}


# ---------------- Jev ----------------
def _attr(obj, *names):
    """SDK answer field names: on the first run, check with print(r.answers) and fix here if needed."""
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    raise AttributeError(f"Unexpected answer format: {obj!r}")


async def ask_jev(client, msg, st: Stats):
    try:
        r = await client.system_one(state=msg["text"], questions=JEV_QUESTIONS)
    except Exception:
        st.api_errors += 1
        return
    a = r.answers
    category = a["category"].choice
    anger = float(_attr(a["anger"], "score", "value")) / (len(ANGER) - 1)  # rubric position -> 0-1
    noul = _attr(a["urgent"], "noul", "value")
    urgent = noul >= 0.5 if isinstance(noul, float) else bool(noul)
    usage = getattr(r, "usage", None)
    # Rough estimate (message + question definitions) if the SDK doesn't return token counts
    st.in_tok += getattr(usage, "input_tokens", None) or (len(msg["text"]) + 600) // 4
    st.record(msg, category, anger, urgent)


# ---------------- LLM ----------------
async def ask_llm(client, msg, st: Stats):
    try:
        r = await client.messages.create(
            model=LLM_MODEL,
            max_tokens=150,
            system=LLM_SYSTEM,
            messages=[{"role": "user", "content": msg["text"]}],
        )
    except Exception:
        st.api_errors += 1
        return
    st.in_tok += r.usage.input_tokens
    st.out_tok += r.usage.output_tokens
    text = "".join(b.text for b in r.content if b.type == "text").strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()  # to be fair: forgive code fences
    try:
        d = json.loads(text)
        category, anger, urgent = d["category"], float(d["anger"]), d["urgent"]
        if category not in CATEGORIES or not 0 <= anger <= 1 or not isinstance(urgent, bool):
            raise ValueError
    except Exception:
        st.bad_json += 1
        return
    st.record(msg, category, anger, urgent)


# ---------------- Race ----------------
async def run_all(fn, client, msgs, st: Stats):
    sem = asyncio.Semaphore(CONCURRENCY)

    async def one(m):
        async with sem:
            await fn(client, m, st)
            st.processed += 1

    await asyncio.gather(*(one(m) for m in msgs))
    st.end = time.perf_counter()


def panel(st: Stats, total: int, color: str) -> Panel:
    ok = max(st.done, 1)
    t = Table.grid(padding=(0, 2))
    t.add_column(style="bold")
    t.add_column(justify="right")
    t.add_row("Processed", f"{st.processed}/{total}")
    t.add_row("Time", f"{st.elapsed():.1f} s")
    t.add_row("Cost", f"${st.cost():.4f}")
    t.add_row("Invalid JSON", str(st.bad_json))
    t.add_row("API errors", str(st.api_errors))
    t.add_row("Category accuracy", f"{100 * st.cat_ok / ok:.0f}%")
    t.add_row("Urgent accuracy", f"{100 * st.urgent_ok / ok:.0f}%")
    t.add_row("Anger error (avg)", f"{st.anger_err / ok:.2f}")
    status = "✅ DONE" if st.end else "⏳"
    return Panel(t, title=f"[bold]{st.name}[/] {status}", border_style=color, width=46)


async def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    with open("messages.json", encoding="utf-8") as f:
        msgs = json.load(f)[:limit]

    llm = Stats(f"🧠 {LLM_MODEL}", LLM_PRICE_IN, LLM_PRICE_OUT)
    jev = Stats("⚡ Jev", JEV_PRICE_IN, 0.0)

    def view():
        panels = [panel(jev, len(msgs), "cyan")]
        if not JEV_ONLY:
            panels.insert(0, panel(llm, len(msgs), "magenta"))
        return Columns(panels)

    async with AsyncTypeSafeClient() as ts:
        llm.start = jev.start = time.perf_counter()
        jobs = [run_all(ask_jev, ts, msgs, jev)]
        if not JEV_ONLY:
            jobs.append(run_all(ask_llm, AsyncAnthropic(), msgs, llm))
        race = asyncio.gather(*jobs)

        with Live(view(), refresh_per_second=10) as live:
            while not race.done():
                live.update(view())
                await asyncio.sleep(0.1)
            live.update(view())
        await race  # any errors surface here

    # Results file for the "why did they disagree?" part of the video
    out = [{**m, "llm": llm.rows.get(m["id"]), "jev": jev.rows.get(m["id"])} for m in msgs]
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    if JEV_ONLY:
        print("\nResults -> results.json (Jev only)")
    else:
        diff = [o for o in out if o["llm"] and o["jev"] and o["llm"]["category"] != o["jev"]["category"]]
        print(f"\nResults -> results.json | Messages where they disagreed on category: {len(diff)}")


if __name__ == "__main__":
    asyncio.run(main())