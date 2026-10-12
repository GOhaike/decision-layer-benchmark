"""Decision Layer Benchmark v1.1: agent decision costs with and without Jev.

Run:  python3 jev_cost_model.py   (or: uv run python jev_cost_model.py)
Edit the SCENARIO block to match your own traffic. Python 3.9+, no dependencies.

Prices are standard list prices per 1M tokens read from each provider's pricing
page on 12 October 2026. Batch APIs (50% off, asynchronous) are excluded because
an agent decides in real time. Output is priced with thinking off.
"""
from __future__ import annotations

VERSION = "1.1"
PRICES_AS_OF = "2026-10-12"

SOURCES = {
    "OpenAI": "https://openai.com/api/pricing/",
    "Anthropic": "https://platform.claude.com/docs/en/about-claude/pricing",
    "Google": "https://ai.google.dev/gemini-api/docs/pricing",
    "TypeSafe": "https://docs.typesafe.ai/models",
    "OpenAI caching": "https://developers.openai.com/api/docs/guides/prompt-caching",
    "Google caching": "https://ai.google.dev/gemini-api/docs/caching",
}

# model: provider, tier, input, output, cached input, cache write, cache storage per hour
# ($ per 1M tokens). Cache write is what a cache miss costs on the static prefix.
MODELS = {
    "GPT-5.6 Sol":              ("OpenAI",    "frontier", 5.00, 30.00, 0.50,  6.25,  0.0),
    "GPT-5.6 Terra":            ("OpenAI",    "mid",      2.00, 12.00, 0.20,  2.50,  0.0),
    "GPT-5.6 Luna":             ("OpenAI",    "small",    0.20,  1.20, 0.02,  0.25,  0.0),
    "Claude Opus 5.5":          ("Anthropic", "frontier", 4.00, 20.00, 0.20,  5.00,  0.0),
    "Claude Sonnet 5.5":        ("Anthropic", "mid",      2.00, 10.00, 0.10,  2.50,  0.0),
    "Claude Haiku 5.5":         ("Anthropic", "small",    0.10,  0.50, 0.01,  0.125, 0.0),
    "Gemini 3.1 Pro Preview":   ("Google",    "frontier", 2.00, 12.00, 0.20,  2.00,  4.50),
    "Gemini 3.8 Flash":         ("Google",    "mid",      0.75,  3.75, 0.075, 0.75,  0.50),
    "Gemini 3.1 Flash-Lite":    ("Google",    "small",    0.25,  1.50, 0.025, 0.25,  1.00),
}
JEV_INPUT_PRICE = 0.042  # Jev 1.13, $ per 1M input tokens; output is free
# Smallest cacheable prefix per provider. OpenAI and Anthropic from their prompt-caching guides;
# Google from its implicit-caching table (Gemini 3.1 Pro Preview and 3.8 Flash; Flash-Lite
# is not listed and is assumed the same).
CACHE_MIN_TOKENS = {"OpenAI": 1_024, "Anthropic": 512, "Google": 4_096}

# ---------------- SCENARIO: change these to match your traffic ----------------
REQUESTS_PER_DAY = 100_000
DAYS = 30
QUESTIONS = ["route", "prompt injection", "personal data", "policy", "next step"]
DECISION_CALLS = 4          # separate-call baseline: injection and PII share one guardrail call
SYSTEM_TOKENS = 1_500       # static instructions per decision call (cacheable)
REQUEST_TOKENS = 1_500      # the request and its recent context (changes every request)
QUESTION_TOKENS = 200       # one question's instructions and options
OUTPUT_PER_CALL = 150       # separate call: JSON label plus a short reason
TERSE_OUTPUT_PER_QUESTION = 30  # batched call: terse JSON per question
CACHE_HIT_RATE = 0.95       # share of static-prefix reads served from cache
REPLY_SYSTEM_TOKENS = 1_500 # static part of the reply prompt (cacheable)
REPLY_DYNAMIC_TOKENS = 2_500
REPLY_OUTPUT_TOKENS = 600
JEV_BILLS_STATE_PER_QUESTION = False  # confirm with jev_billing_probe.py
# ------------------------------------------------------------------------------

M = 1_000_000
HOURS = DAYS * 24
REQUESTS = REQUESTS_PER_DAY * DAYS


def price(model):
    return dict(zip(("provider", "tier", "inp", "out", "cached", "write", "storage"), MODELS[model]))


def can_cache(p, prefix_tokens):
    return prefix_tokens >= CACHE_MIN_TOKENS[p["provider"]]


def static_cost(p, tokens, cached):
    """Cost of a static prefix: full price uncached; hit or write price with caching."""
    if not cached:
        return tokens * p["inp"] / M
    return tokens * (CACHE_HIT_RATE * p["cached"] + (1 - CACHE_HIT_RATE) * p["write"]) / M


def storage(p, tokens):
    return tokens * p["storage"] * HOURS / M  # per month, for the whole cache


def decisions(model, mode):
    """Monthly cost of the decision layer on one model. mode: naive, cached, optimized."""
    p = price(model)
    if mode in ("naive", "cached"):
        cached = mode == "cached" and can_cache(p, SYSTEM_TOKENS)
        per_call = (static_cost(p, SYSTEM_TOKENS, cached) + REQUEST_TOKENS * p["inp"] / M
                    + OUTPUT_PER_CALL * p["out"] / M)
        month = per_call * DECISION_CALLS * REQUESTS
        return month + (storage(p, SYSTEM_TOKENS * DECISION_CALLS) if cached else 0)
    n = len(QUESTIONS)
    static = SYSTEM_TOKENS + n * QUESTION_TOKENS
    cached = can_cache(p, static)
    per_req = (static_cost(p, static, cached) + REQUEST_TOKENS * p["inp"] / M
               + n * TERSE_OUTPUT_PER_QUESTION * p["out"] / M)
    return per_req * REQUESTS + (storage(p, static) if cached else 0)


def jev(per_question=None):
    per_question = JEV_BILLS_STATE_PER_QUESTION if per_question is None else per_question
    n = len(QUESTIONS)
    tokens = n * (REQUEST_TOKENS + QUESTION_TOKENS) if per_question else REQUEST_TOKENS + n * QUESTION_TOKENS
    return tokens * JEV_INPUT_PRICE / M * REQUESTS


def reply(model, cached):
    p = price(model)
    cached = cached and can_cache(p, REPLY_SYSTEM_TOKENS)
    per = (static_cost(p, REPLY_SYSTEM_TOKENS, cached) + REPLY_DYNAMIC_TOKENS * p["inp"] / M
           + REPLY_OUTPUT_TOKENS * p["out"] / M)
    return per * REQUESTS + (storage(p, REPLY_SYSTEM_TOKENS) if cached else 0)


STACKS = [
    # name, decision tier, decision mode, reply cached
    ("A  Naive: mid-tier decisions, no caching", "mid", "naive", False),
    ("B  Typical: small-model decisions, cached", "small", "cached", True),
    ("C  Tuned: one batched small-model call, cached", "small", "optimized", True),
]


def stack(provider, tier, mode, cached):
    dmodel = next(m for m, v in MODELS.items() if v[0] == provider and v[1] == tier)
    rmodel = next(m for m, v in MODELS.items() if v[0] == provider and v[1] == "mid")
    without = decisions(dmodel, mode) + reply(rmodel, cached)
    with_jev = jev() + reply(rmodel, cached)
    return dmodel, rmodel, without, with_jev


def money(x):
    return f"${x:,.0f}"


def main():
    n = len(QUESTIONS)
    mode = "per question" if JEV_BILLS_STATE_PER_QUESTION else "once per request"
    print(f"Decision Layer Benchmark v{VERSION}. {REQUESTS_PER_DAY:,} requests a day for {DAYS} days, "
          f"{n} questions, prices as of {PRICES_AS_OF}")
    print(f"Jev state billed {mode}: {money(jev())} a month "
          f"(once: {money(jev(False))}, per question: {money(jev(True))})")

    print("\n1. Decision layer only, per month")
    print(f"{'Model':24}{'Naive':>10}{'Cached':>10}{'Tuned':>10}{'Jev':>8}{'Tuned/Jev':>11}")
    for tier in ("frontier", "mid", "small"):
        for model in [m for m, v in MODELS.items() if v[1] == tier]:
            nv, cv, tv = (decisions(model, k) for k in ("naive", "cached", "optimized"))
            print(f"{model:24}{money(nv):>10}{money(cv):>10}{money(tv):>10}{money(jev()):>8}"
                  f"{tv / jev():>10.1f}x")
        print()

    print("2. Whole stack per month (reply always on the provider's mid-tier model)")
    for name, tier, dmode, cached in STACKS:
        print(name)
        for provider in ("OpenAI", "Anthropic", "Google"):
            dmodel, rmodel, without, with_jev = stack(provider, tier, dmode, cached)
            saved = without - with_jev
            print(f"   {provider:10}{dmodel:24}{money(without):>10}{money(with_jev):>10}"
                  f"{money(saved):>10}{100 * saved / without:>5.0f}%")

    print("\nPrices, $ per 1M tokens: input / output / cached input")
    for model, (prov, _, pi, po, pc, _, _) in MODELS.items():
        print(f"  {model:24}{pi:>6.2f} / {po:>5.2f} / {pc:>5.3f}   {prov}")
    print(f"  {'Jev 1.13':24}{JEV_INPUT_PRICE:>6.3f} / free  / none    TypeSafe")
    print("\nSources")
    for provider, url in SOURCES.items():
        print(f"  {provider:10} {url}")


if __name__ == "__main__":
    main()
