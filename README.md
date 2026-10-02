# Jev vs Claude — The 500 Customer Message Race

Demo code for a YouTube video comparing [TypeSafe's Jev](https://typesafe.ai) against Claude (Anthropic) on a real-ish task: classifying customer support messages.

Both systems get the same 500 messages and have to answer three questions about each one:

- **category** — refund, shipping, product question, complaint, or spam
- **anger** — how angry is the customer, on a 0–3 scale
- **urgent** — does this need a human right now?

The race script runs both concurrently and reports speed, cost, and accuracy against ground-truth labels.

## Files

| File | What it does |
|---|---|
| `generate_messages.py` | Generates 500 labeled customer messages → `messages.json` (the ground truth used to score accuracy) |
| `race.py` | The main event: runs Jev and Claude side by side on the same messages and prints a live scoreboard |
| `jev-demo-1-REST_API.py` | Minimal example of calling Jev directly via its REST API |
| `jev-demo-2-Python-SDK.py` | Same example using the `typesafe-sdk` Python client instead |
| `results_analysis.py` | Digs into `results.json` to see which messages Jev and the ground truth disagreed on |
| `messages.json` / `results.json` | Generated output — created when you run the scripts above |

## Setup

```bash
pip install typesafe-sdk anthropic rich requests
export TYPESAFE_API_KEY=...
export ANTHROPIC_API_KEY=...
```

Both keys are read from the environment — never hardcode them in the scripts.

## Running the race

1. Generate the message set first:

   ```bash
   python generate_messages.py
   ```

2. Do a quick sanity check with a handful of messages (good for checking the response format before burning credits):

   ```bash
   python race.py 5
   ```

3. Run the full 500-message race:

   ```bash
   python race.py
   ```

   Set `JEV_ONLY=1` to run Jev alone and skip the LLM side (useful for iterating without spending API credits).

Results land in `results.json`, including where Jev and Claude disagreed on category — which is what `results_analysis.py` explores:

```bash
python results_analysis.py
```

## Standalone Jev examples

`jev-demo-1-REST_API.py` and `jev-demo-2-Python-SDK.py` are small, self-contained examples (unrelated to the race) showing how to call Jev's `system_one` endpoint directly — one via raw HTTP requests, one via the SDK.
