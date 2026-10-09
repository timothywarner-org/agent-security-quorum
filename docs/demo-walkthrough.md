# Tell the story from Actions history

**The question is who supplies evidence, what the policy does with it, and who owns the consequence.** Keep the browser on completed GitHub runs. The workflow itself is supporting material, not the main screen.

## Open these before presenting

| Beat | Evidence | What it establishes |
|---|---|---|
| Harmless change | [Baseline results on PR #4](https://github.com/timothywarner-org/agent-security-quorum/pull/4#issuecomment-6071680881), including the exact run link | Four valid SAFE results, no evaluation errors, and the file gate passing on the first October 8 baseline |
| Risky change | [Four-voter rehearsal, September 19, 2026](https://github.com/timothywarner-org/agent-security-quorum/actions/runs/35445419741) and [PR #3 findings](https://github.com/timothywarner-org/agent-security-quorum/pull/3#issuecomment-5737262335) | Four UNSAFE votes and a separate test-file gate failure on commit ee80d84 |
| Operational dependency | [Access probe, October 8, 2026](https://github.com/timothywarner-org/agent-security-quorum/actions/runs/37864270825) | Token was accepted, but its October 18 expiration triggered the 14-day maintenance threshold; model checks were skipped |

The September run predates ERROR reporting and uses the older phrase **Merge blocked**. Treat that as a historical scanner verdict. On October 8, the GitHub API reported no rulesets and an unprotected main branch, so that wording does not establish enforced merge protection.

The first October 8 baseline is preserved as [run 37864262324](https://github.com/timothywarner-org/agent-security-quorum/actions/runs/37864262324), commit **22e220d**. All four downloaded result artifacts reported SAFE, without an error flag. The static voter also recorded one informational license finding. PR #4's comment updates on subsequent runs, so read its commit and run footer before presenting. Follow-up workflow changes pin the runner and update existing Actions to Node 24 releases to remove the deprecation notices visible in the first baseline.

## Nine-minute route

1. **0:00-1:00, the proposed behavior.** Show the harmless reviewer instruction: failed or unavailable checks get reported to the maintainer; they never get bypassed. Contrast it verbally with a proposal to approve despite failure. Let the audience name the risk before opening the result.
2. **1:00-2:30, the baseline.** Open the verified harmless run. Read the decision and four-row vote table. Point out the test-file gate as a separate policy control. The question is whether the process can accept normal work.
3. **2:30-5:00, the risky run.** Open September's rehearsal. Read one security finding and one privilege finding, then the static result. Different lenses inspect the same proposal. A successful job means the reviewer completed, even when its answer is UNSAFE.
4. **5:00-6:30, the rule.** Two UNSAFE votes fail the scan. One can pass, so a dissenter still deserves attention. Any evaluation error now fails independently. The file gate is another independent hard stop. Agreement is not proof of correctness.
5. **6:30-7:30, operations.** Open the expiring-token probe. All three model reviewers share Copilot access and a credential. A token-maintenance failure is not a discovered vulnerability or proof of a provider outage.
6. **7:30-9:00, the business decision.** Name the data boundary, acceptable misses/false alarms, cost of review, and human fallback. The owner decides whether added findings justify the operating work.

The risky run contains **both** malicious instructions and a bundled test payload. It demonstrates two controls firing together. It does not isolate their individual contribution. Describe a gate-only or split-vote case as a hypothetical unless you have a recorded run showing it.

## Rehearse without adding an application

1. Run the access probe and resolve maintenance warnings before depending on a live scan.
2. Use a same-repository PR with a harmless agent edit for baseline evidence. Scanner-only changes need an agent edit to match the path filter.
3. Confirm all four results are valid, not fail-safe errors. Record the exact run URL, source commit, requested models, and decision.
4. Keep the risky example PR unmerged. Treat malicious fixtures as inert review data; never execute their bundled code.
5. Open completed run pages in advance. A fresh run can be optional audience participation, but the presentation does not wait for it.

## Claims to keep bounded

| Claim | Evidence boundary |
|---|---|
| Four reviewers completed | Inspect all four artifacts or summaries; job status alone does not establish valid verdicts |
| A specific model ran | Display records the requested model; do not call that independent backend attestation |
| The unsafe change was caught | True for the named fixture and run, not a measured detection rate |
| The check blocks merging | Requires enforced branch protection or a ruleset |
| Multiple reviewers improve security | A hypothesis to test against human review and static analysis, including cost and misses |

Use labels **PASS**, **FAIL**, **ERROR**, **SAFE**, and **UNSAFE** when speaking. Do not depend on status colors. The job graph, summaries, and findings are enough to carry the story.
