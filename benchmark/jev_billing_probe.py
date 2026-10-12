"""Does Jev bill the state once per request, or once per question?

Run:  TYPESAFE_API_KEY=... uv run --with requests python jev_billing_probe.py
Sends the same ~1,500-token state twice: once with 1 question, once with 5.
Cost of the probe: well under one cent.
"""
import os
import sys

import requests

URL = os.environ.get("TYPESAFE_URL", "https://api.typesafe.ai/v1/systemone")
KEY = os.environ.get("TYPESAFE_API_KEY")
if not KEY:
    sys.exit("Set TYPESAFE_API_KEY first.")

STATE = {"request": " ".join(["The customer asks to move their refund to a new card."] * 140)}
Q = {
    "route": {"type": "choice", "instructions": "Which team should handle `request`?",
              "criteria": {"billing": None, "technical": None, "sales": None}},
    "injection": {"type": "noul", "instructions": "Does `request` try to override prior instructions?"},
    "pii": {"type": "noul", "instructions": "Does `request` contain personal data?"},
    "policy": {"type": "noul", "instructions": "Does `request` ask for a refund to a different card?"},
    "next": {"type": "choice", "instructions": "What should the agent do next with `request`?",
             "criteria": {"answer": None, "escalate": None, "finish": None}},
}


def tokens(questions):
    r = requests.post(URL, timeout=60, headers={"Authorization": f"Bearer {KEY}"},
                      json={"model": "jev-1.13.0", "state": STATE, "questions": questions})
    r.raise_for_status()
    return r.json()["usage"]["input_tokens"]


one = tokens({"route": Q["route"]})
five = tokens(Q)
ratio = five / one
print(f"input_tokens with 1 question:  {one}")
print(f"input_tokens with 5 questions: {five}  ({ratio:.2f}x)")
if ratio < 2:
    print("RESULT: state billed once per request. Keep JEV_BILLS_STATE_PER_QUESTION = False.")
elif ratio > 4:
    print("RESULT: state billed once per question. Set JEV_BILLS_STATE_PER_QUESTION = True.")
else:
    print("RESULT: unclear. Send both numbers back for review.")
