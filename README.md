# Decision Layer Benchmark

What it costs an AI agent to make its decisions, priced on OpenAI, Anthropic and Google models and on TypeSafe's Jev 1.13.

Before an agent writes anything it answers small questions: where to route, whether the input is a prompt injection, whether it carries personal data, whether the action is allowed, and what to do next. This benchmark prices that decision layer at list price under three baselines, from naive to tuned, and prices the same layer on Jev, a model that answers typed questions with calibrated probabilities and writes no text.

Full report: [report/Decision-Layer-Benchmark-v1.1.pdf](report/Decision-Layer-Benchmark-v1.1.pdf)

## Results

100,000 requests a day for 30 days, list prices as of 12 October 2026.

| | Result |
|---|---|
| Jev decision layer, all 5 questions | $315 a month |
| Decision layer against a tuned baseline | 2.5× (Claude Haiku 5.5) to 133× (GPT-5.6 Sol) cheaper on Jev |
| Whole bill, naive stacks | 67 to 68% saved |
| Whole bill, typical cached stacks | 7 to 41% saved |
| Whole bill, tuned stacks | 1 to 17% saved |
| Where Jev barely wins | Tuned Claude Haiku 5.5 stack saves $478 a month (1%) |

## Run it

The calculator is one Python file with no dependencies (Python 3.9 or later).

```sh
python3 benchmark/jev_cost_model.py
# or
uv run python benchmark/jev_cost_model.py
```

Every assumption sits in the scenario block at the top of the file: traffic, token counts, cache hit rate, output sizes. Change it to match your own traffic and run it again.

## How Jev bills, measured

TypeSafe's docs say Jev reads the shared state once and answers every question against it. The probe confirmed it on 12 October 2026:

| Questions | Input tokens |
|---|---|
| 1 | 2,011 |
| 5 | 2,133 |

Each extra question adds about 30 tokens, so the state is billed once per request. The calculator assumes 200 tokens per question, more than measured, so the $315 figure is conservative.

Run the probe yourself with two calls that cost well under a cent:

```sh
uv run --with requests python benchmark/jev_billing_probe.py
```

It reads your key from `TYPESAFE_API_KEY`, or asks for it without showing it on screen.

## The policy rule

`policy/refunds.rego` shows the pattern the report recommends: Jev reports facts with a confidence, and only systems of record can allow an action. A Jev score can only block. The six test cases include Jev being fooled by an injection and a missing account field; the rule fails closed in every case.

```sh
sh policy/run_tests.sh
```

Tested with OPA 1.4.2.

## Repository layout

```
benchmark/   the calculator and the Jev billing probe
policy/      the OPA refund rule, six test cases and a test runner
report/      the full benchmark report (PDF)
```

## Method

| Baseline | How the decisions are made |
|---|---|
| Naive | 4 separate calls (the guardrail covers injection and PII), no caching |
| Cached | The same 4 calls with each static prompt cached |
| Tuned | One batched call answering all 5 questions, static prompt cached, terse JSON |

- Each decision call reads a 1,500-token static prompt plus 1,500 tokens of request context and returns 150 tokens. A batched call returns 30 tokens per question.
- Cache hit rate is 95%. Misses pay the provider's cache write price: 1.25× input on OpenAI GPT-5.6 and on Anthropic (five-minute cache).
- Caching applies only when the static prefix reaches the provider's minimum: 1,024 tokens on OpenAI, 512 on Anthropic and 4,096 on Google. Every Google prefix here is shorter, so Google runs uncached.
- The reply always runs on the provider's mid-tier model and is identical with and without Jev.
- Excluded: batch APIs (asynchronous, unsuited to live decisions), volume discounts and thinking tokens. Thinking tokens and tool-use overhead would raise the baselines and favor Jev.
- Gemini 3.8 Flash is at its introductory rate, which doubles on 1 January 2027.

## Limits

This benchmark measures token cost only. Accuracy depends on your decisions and your data, and needs a shadow run on your own traffic. TypeSafe documents that Jev 1.13 is unreliable at arithmetic, counting and date comparison, reads instructions literally, leans toward the first Choice option, and can be moved by adversarial text in the state. Jev is in early access; pin `jev-1.13.0`.

## Sources

- [OpenAI API pricing](https://openai.com/api/pricing/) and [prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) and [context caching](https://ai.google.dev/gemini-api/docs/caching)
- [TypeSafe models](https://docs.typesafe.ai/models) and [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
- [Introducing System One models and Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- [Evaluating and benchmarking the System One model Jev](https://arxiv.org/abs/2609.37647), arXiv preprint, not peer reviewed
- [Open Policy Agent, Rego](https://www.openpolicyagent.org/docs/latest/policy-language/)

## Author

Gabriel Ohaike, Enterprise Principal Agentic AI Architect. [LinkedIn](https://www.linkedin.com/in/gabriel-ohaike)

No affiliation with or compensation from TypeSafe. Views my own.

## License

MIT. See [LICENSE](LICENSE).
