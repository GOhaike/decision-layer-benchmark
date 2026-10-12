# LinkedIn

Attach `carousel.pdf` as the document. Paste the text below as the post.

---

I priced an agent's decision layer on OpenAI, Anthropic, Google and TypeSafe's Jev.

Before an agent writes anything it answers small questions: where to route, is this an injection, does it carry personal data, is the action allowed, what next. In many stacks each one is a full model call.

At 100,000 requests a day, list prices, 12 Oct 2026:
• Against a tuned baseline (one batched call, cached prompt, terse JSON), the decision layer is 2.5× to 133× cheaper on Jev.
• Off the whole bill: 67 to 68% for naive stacks, 7 to 41% for typical ones, 1 to 17% for tuned ones.
• Where Jev barely wins: a tuned Claude Haiku stack saves $478 a month. There the case is calibrated confidence and one pass for every decision.

The architecture matters more than the price. Jev judges, code decides, OPA enforces, the LLM writes. A Jev score can only block; the facts that allow an action come from systems of record.

Code, policy tests and the full report: https://github.com/GOhaike/decision-layer-benchmark

No affiliation with or compensation from TypeSafe. Views my own.

Where do you draw the line between the judge and the enforcer in your stack?

#AgenticAI #EnterpriseArchitecture #LLMOps #AIEngineering
