import os
import requests
import json

API_KEY = os.environ["TYPESAFE_API_KEY"]

url = "https://api.typesafe.ai/v1/systemone"

payload = {
    "model": "jev-latest",
    "state": "The water heater in my apartment stopped working this morning. There's no hot water at all, and I have two small kids at home.",
    "questions": {
        "category": {
            "type": "choice",
            "instructions": "What type of maintenance issue is this?",
            "criteria": {
                "plumbing": "Leaks, clogs, pipes, drains, or water supply problems",
                "electrical": "Power outages, outlets, wiring, or lighting problems",
                "appliance": "A broken household appliance like a fridge, oven, washer, or heater",
                "other": "Anything that doesn't fit the categories above"
            }
        },
        "urgent": {
            "type": "noul",
            "instructions": "Does this request need a technician today?"
        },
        "severity": {
            "type": "score",
            "instructions": "How severe is this issue for the resident?",
            "criteria": [
                "Low: cosmetic or minor issue, can wait for a scheduled visit",
                "Medium: inconvenient, but the resident can manage for a few days",
                "High: a basic need is affected, should be fixed within a day",
                "Critical: safety risk or the home is unlivable, needs immediate action"
            ]
        }
    }
}

response = requests.post(
    url,
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json=payload
)

response.raise_for_status()
print(f"HTTP {response.status_code} in {response.elapsed.total_seconds() * 1000:.0f} ms")

print(json.dumps(response.json(), indent=2))