# Community contribution roadmap

**The goal is a small, inspectable reference implementation.** The workflow should make a decision understandable, and the tests should make policy mistakes reproducible.

Start with [CONTRIBUTING](../CONTRIBUTING.md), the [fixture scorecard](fixture-scorecard.md), and the [open contribution issues](https://github.com/timothywarner-org/agent-security-quorum/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22help%20wanted%22).

| Work item | Acceptance criteria | Evidence needed |
|---|---|---|
| Add an ordinary enterprise fixture that challenges false positives | A small Contoso or Tailwind Traders definition with a legitimate task, explicit scope, expected outcome, and no executable payload. Extend the catalog and explain the risk of overblocking. | Synthetic source and hashes; observed static findings. Mark model results unmeasured unless a maintainer records a live run. |
| Extend JSONL extraction regression coverage | Exercise the production extraction against synthetic assistant replies, echoed user examples, fenced output, malformed JSON, and missing replies. Preserve fail-closed behavior; never use private event streams. | Secret-free tests reproducing a specific parsing failure, with before/after results. |
| Verify first-time contributor instructions | Follow the current release in a fresh fork and report which no-secret checks run, where maintainer approval is needed, and how a relevant fork PR fails without the credential. | Exact commit and public run links, tested OS, and corrected steps. No live Copilot purchase is required. |

## Proposing a detection change

1. Name the behavior and the current miss or false alarm.
2. Supply one minimal fixture with an intended policy outcome.
3. Keep **intended**, **static observed**, **model observed**, and **final policy decision** separate.
4. Show how the change affects both the new fixture and harmless examples.
5. Explain its added request usage, run time, or review burden. Use **not measured** when evidence is unavailable.

A SAFE result on a malicious fixture is useful evidence to preserve. Do not edit the fixture merely to obtain a preferred verdict. Borderline examples are discussion material until repeated observations justify a policy change.
