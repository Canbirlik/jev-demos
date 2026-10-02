import json
from collections import Counter

d = json.load(open("results.json"))
diffs = Counter(
    (o["text"].split(" Order #")[0].split(" - ")[0], o["category"], o["jev"]["category"])
    for o in d if o["jev"] and o["jev"]["category"] != o["category"]
)
for (text, truth, jev), n in diffs.most_common():
    print(f"{n:3}x  truth={truth:17} jev={jev:17} | {text}")