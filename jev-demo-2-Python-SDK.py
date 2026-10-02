import time

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

# Reads TYPESAFE_API_KEY from the environment; model defaults to jev-latest
client = TypeSafeClient()

request = (
    "The water heater in my apartment stopped working this morning. "
    "There's no hot water at all, and I have two small kids at home."
)

questions = {
    "category": Choice(
        instructions="What type of maintenance issue is this?",
        criteria={
            "plumbing": "Leaks, clogs, pipes, drains, or water supply problems",
            "electrical": "Power outages, outlets, wiring, or lighting problems",
            "appliance": "A broken household appliance like a fridge, oven, washer, or heater",
            "other": "Anything that doesn't fit the categories above",
        },
    ),
    "urgent": Noul(
        instructions="Does this request need a technician today?",
    ),
    "severity": Score(
        instructions="How severe is this issue for the resident?",
        criteria=[
            "Low: cosmetic or minor issue, can wait for a scheduled visit",
            "Medium: inconvenient, but the resident can manage for a few days",
            "High: a basic need is affected, should be fixed within a day",
            "Critical: safety risk or the home is unlivable, needs immediate action",
        ],
    ),
}

start = time.perf_counter()
response = client.system_one(state=request, questions=questions)
elapsed_ms = (time.perf_counter() - start) * 1000

category = response.answers["category"]
urgent = response.answers["urgent"]
severity = response.answers["severity"]

print(f"Category : {category.choice} (confidence: {category.confidence:.2f})")
print(f"           probabilities: {category.probabilities}")
print(f"Urgent   : {urgent.noul:.0%} probability of yes")
print(f"Severity : {severity.score:.2f} of 3 (confidence: {severity.confidence:.2f})")
print(f"Model: {response.model} | Tokens: {response.usage} | {elapsed_ms:.0f} ms")