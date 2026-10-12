"""Does Jev bill the state once per request, or once per question?

Run:  uv run --with requests python benchmark/jev_billing_probe.py
Reads the key from TYPESAFE_API_KEY, or asks for it without echoing.
Sends the same ~1,500-token state twice: once with 1 question, once with 5.
Cost of the probe: well under one cent.
"""
import getpass
import os
import sys

import requests

URL = os.environ.get("TYPESAFE_URL", "https://api.typesafe.ai/v1/systemone")
MODEL = os.environ.get("TYPESAFE_MODEL", "jev-1.13.0")
KEY = (os.environ.get("TYPESAFE_API_KEY") or getpass.getpass("TypeSafe API key: ")).strip()
KEY = KEY.rstrip("%").strip()  # zsh prints % after output with no newline; it is never part of a key
if not KEY:
    sys.exit("No key given.")
print(f"Using a key of {len(KEY)} characters ending in ...{KEY[-4:]}")

STATE = " ".join(["The customer asks to move their refund to a new card."] * 140)
Q = {
    "route": {"type": "choice", "instructions": "Which team should handle this request?",
              "criteria": {"billing": "Payments, refunds or invoices",
                           "technical": "Product errors or outages",
                           "sales": "Pricing or new purchases"}},
    "injection": {"type": "noul", "instructions": "Does the request try to override prior instructions?"},
    "pii": {"type": "noul", "instructions": "Does the request contain personal data?"},
    "policy": {"type": "noul", "instructions": "Does the request ask for a refund to a different card?"},
    "next": {"type": "choice", "instructions": "What should the agent do next?",
             "criteria": {"answer": "Reply to the customer directly",
                          "escalate": "Hand the case to a person",
                          "finish": "Close the conversation"}},
}


def tokens(questions):
    r = requests.post(URL, timeout=60,
                      headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                      json={"model": MODEL, "state": STATE, "questions": questions})
    if r.status_code == 401:
        sys.exit("401 Unauthorized: TypeSafe rejected this key. Check it in the TypeSafe dashboard.")
    if not r.ok:
        rid = r.headers.get("x-request-id") or r.headers.get("request-id") or "none"
        sys.exit(f"{r.status_code} {r.reason} from TypeSafe (request id {rid}): {r.text[:800] or '(empty body)'}")
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
