"""Generates 500 labeled customer messages -> messages.json

The labels (category, anger 0-3, urgent) are the ground truth used to measure accuracy.
Messages marked hard=True are for the "why did the two models disagree?" part of the video.
"""
import json
import random

random.seed(42)

# (text, category, anger 0=calm..3=furious, urgent, hard)
SEEDS = [
    # refund
    ("Hi, the shoes I bought last week are too small. How can I return them?", "refund", 0, False, False),
    ("I'd like to return this item, the box was never opened.", "refund", 0, False, False),
    ("My refund still hasn't arrived after 3 weeks! If it's not in my account today, I'm filing a chargeback with my bank.", "refund", 3, True, False),
    ("I accidentally placed the same order twice, can I return one of them?", "refund", 0, False, False),
    ("One side of the headphones doesn't work, I want to return them. Honestly a bit disappointed.", "refund", 1, False, False),
    # shipping
    ("When will my order be shipped?", "shipping", 0, False, False),
    ("My tracking number doesn't show up in the system, can you help?", "shipping", 1, False, False),
    ("It has said 'out for delivery' for 5 days and still nothing. I'm running out of patience.", "complaint", 2, False, False),
    ("My wedding is TOMORROW and the dress still hasn't arrived!!! Someone call me right now please!", "shipping", 3, True, False),
    ("Can I change my delivery address? I think the order hasn't left the warehouse yet.", "shipping", 0, False, False),
    # product question
    ("Is this jacket waterproof?", "product_question", 0, False, False),
    ("Will this laptop bag fit a 15.6 inch laptop?", "product_question", 0, False, False),
    ("How long is the warranty on the coffee machine?", "product_question", 0, False, False),
    ("Does this cream contain parabens? Asking because I have sensitive skin.", "product_question", 0, False, False),
    ("How many cm is a size M? I couldn't find the size chart.", "product_question", 0, False, False),
    # complaint
    ("I tried to reach your customer service 4 times and nobody got back to me. Terrible service.", "complaint", 3, True, False),
    ("The package arrived crushed. The product is fine but I wanted to let you know.", "complaint", 1, False, False),
    ("The courier left the package at my door and walked off without even ringing the bell.", "complaint", 2, False, False),
    ("The charger overheated and started smoking while in use, and it was in my kid's room!", "complaint", 3, True, False),
    # spam
    ("Congratulations! You won $500, click the link to claim your prize: bit.ly/prize123", "spam", 0, False, False),
    ("Let our SEO services take your site to #1 on Google! Call now.", "spam", 0, False, False),
    ("Make $500 a day with crypto investing, details in DM.", "spam", 0, False, False),
    ("Your account has been suspended. Reply to this message with your password to verify.", "spam", 0, False, False),
    # hard cases
    ("Great, the wrong item arrived for the THIRD time 👏 Well done, really.", "complaint", 3, True, True),
    ("Hola, I received the wrong color. Can I exchange it or do I have to return it?", "refund", 0, False, True),
    ("Nice product, but shipping took 2 weeks. Would be nice if it were faster next time.", "complaint", 1, False, True),
    ("I got the return code but the shipping office refused to take the package, what should I do?", "refund", 1, False, True),
    ("I trusted you, but this is my last purchase. Delete my account.", "complaint", 2, True, True),
]

NAMES = ["Alice", "Mehmet", "Sofia", "James", "Elena", "Omar", "Lina", "David", "Yuki", ""]


def vary(text: str) -> str:
    """Adds small variations so the same message isn't repeated verbatim."""
    parts = [text]
    if random.random() < 0.5:
        parts.append(f"Order #{random.randint(100000, 999999)}")
    name = random.choice(NAMES)
    if name:
        parts.append(f"- {name}")
    return " ".join(parts)


messages = []
for i in range(500):
    text, category, anger, urgent, hard = random.choice(SEEDS)
    messages.append({
        "id": i + 1,
        "text": vary(text),
        "category": category,
        "anger": anger / 3,  # normalized to 0-1
        "urgent": urgent,
        "hard": hard,
    })

with open("messages.json", "w", encoding="utf-8") as f:
    json.dump(messages, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(messages)} messages -> messages.json")