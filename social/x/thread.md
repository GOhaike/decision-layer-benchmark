# X thread

Six posts, each under 280 characters. Attach the image named in brackets, from the images folder.

---

**1** [images/page-01.png]

I priced an AI agent's decisions on OpenAI, Anthropic, Google and TypeSafe's Jev.

Against a tuned stack, Jev runs the decision layer 2.5× to 133× cheaper.

Code, tests and report: https://github.com/GOhaike/decision-layer-benchmark

---

**2** [images/page-02.png]

Before an agent writes a word it answers 5 small questions: route, injection, personal data, policy, next step.

In many stacks each is a full model call, billed as if it were writing prose.

---

**3** [images/page-07.png]

What it does to the whole bill depends on your stack:

Naive: 67 to 68% saved
Typical, cached: 7 to 41%
Tuned, batched: 1 to 17%

On a tuned Claude Haiku stack Jev saves $478 a month. I put that in the benchmark on purpose.

---

**4** [images/page-05.png]

The bigger point is architecture.

Jev judges. Code decides. OPA enforces. The LLM writes.

A Jev score can only block an action. The facts that allow one come from systems of record.

---

**5** [images/page-10.png]

Limits, from TypeSafe's own docs: unreliable at arithmetic and dates, reads literally, leans toward the first option, and adversarial text can move it.

So: shadow run first, act only in the confidence bands that clear your bar.

---

**6**

Every number comes from one Python file you can run on your own traffic.

https://github.com/GOhaike/decision-layer-benchmark

No affiliation with TypeSafe. Views my own.
