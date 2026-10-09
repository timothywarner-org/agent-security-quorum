# Configuration and operation

The source of truth is [agent-scan.yml](../.github/workflows/agent-scan.yml). This guide describes the **four-voter** implementation, including the separate hard stop and failure on any evaluation error.

## Installation

1. Copy both workflows from **.github/workflows/** and all four files in **prompts/**, preserving their paths. Forking also includes fixtures and examples.
2. Set repository secret **COPILOT_PAT** to a fine-grained PAT with **Copilot Requests** permission. The token owner's model entitlements and organization policies apply. Never commit the token.
3. Run **Copilot Access Probe**. It reads the scanner's pinned CLI version and model IDs.
4. Open a same-repository PR with a harmless agent change. Scanner/probe workflow and prompt changes also exercise the scanner against all tracked agent and skill files.
5. Review the result, then configure required checks and approvals appropriate to the repository.

GitHub documents PAT setup in [Automating tasks with Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/automate-copilot-cli/automate-with-actions). This repository uses that explicit PAT route; it does not automatically adopt other authentication configurations supported by newer CLI versions.

## Configuration in one place

| Setting | Where | Change discipline |
|---|---|---|
| Copilot CLI version | env.COPILOT_CLI_VERSION | Pin it; rehearse after upgrades |
| Cisco scanner version | env.SKILL_SCANNER_VERSION | Pin it; recheck fixture outcomes after upgrades |
| Requested models | jobs.llm_scan.strategy.matrix.include | Three selected families, no silent fallback |
| Review lenses | prompts/lens-*.txt | Keep short; name must match matrix lens |
| Base rubric | prompts/v1.txt | Retain the untrusted-data boundary and JSON contract |
| Policy | aggregate, **Apply quorum** | Two valid UNSAFE votes fail; any ERROR or failed gate also fails |
| Runtime bound | Each job's timeout-minutes | Bounded detection, review, and reporting; a missing required result prevents PASS |

Do not add another voter for a bigger diagram. A fifth voter requires a demonstrated coverage benefit and corresponding updates to aggregation, summaries, and policy.

## Results

| Label | Meaning |
|---|---|
| **SAFE** | Valid answer without a blocking finding in that reviewer's scope |
| **UNSAFE** | Valid answer with a blocking finding |
| **ERROR** | Missing, invalid, or explicitly failed evaluation; not a vulnerability finding |
| **Hard stop FAIL** | File policy matched or the gate did not finish |
| **Decision PASS** | Four valid responses, fewer than two UNSAFE votes, successful file gate |

The matrix makes three separate calls through shared Copilot access. The model field is **requested configuration**, not backend attestation. There is no fallback to an unspecified model. A successful reviewer job means it ran, not that it voted SAFE.

The compatibility contract is **verdict, findings, model, lens**, and optional **error**. A result with **error: true** fails the decision independently of the threshold. Findings carry **id, file, detail**. Missing or malformed artifacts are errors too.

## Trigger and coverage

Scanned roots: **.github/agents/**, **.github/skills/**, **.claude/agents/**, **.claude/skills/**, and **.agents/skills/**.

Semantic reviewers read changed text files. Binary files and files exceeding 16 KiB produce errors; they are never silently omitted or truncated. Symlinks, submodules, and newline-containing input paths fail scope validation. Static analysis and the file-pattern gate inspect directories, including existing files. Frontmatter checks are advisory.

There is no workflow-level path filter. Every PR receives **Quorum Decision**, avoiding [GitHub's pending required-check problem](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onpull_requestpull_request_targetpathspaths-ignore). Unrelated and deletion-only changes receive a scope-based PASS with no model calls. Workflow or prompt changes rescan all tracked targets. Fixture-only edits outside the scanned roots do not evaluate the fixtures themselves.

Fork and Dependabot PRs normally receive no Copilot secret. Relevant scans fail closed, and PR comments/SARIF uploads are skipped. A maintainer can review the exact update, then apply it to a trusted same-repository branch for testing with the existing credential. Do not solve this by running untrusted PR code with **pull_request_target** and privileged credentials.

## Enforcement

**A failing check alone does not prevent a merge.** Require **Quorum Decision** in branch protection or a ruleset when it should block merging.

The workflow and prompts come from the PR merge checkout. A contributor can propose changing the judge and the evidence together. Require code-owner review for the scanner, probe, and prompts. Having **CODEOWNERS** in the tree does not enforce approval.

## Troubleshooting

| Symptom | Interpretation and next action |
|---|---|
| Token expires in fewer than 14 days | GitHub accepted the token, but maintenance is due. Rotate COPILOT_PAT. That probe stops before testing models. |
| Token check returns HTTP 401 | Token is invalid, expired, or revoked. Replace it securely. |
| Token check returns another non-200 response | Validation is inconclusive. Check service availability and permissions. |
| Model has no valid reply | Inspect its log, entitlements, and configured ID. Do not add fallback. |
| One evaluator shows ERROR | Entire decision fails. Repair the evaluator and rerun. |
| One UNSAFE vote and PASS | Expected policy. Read the dissenting finding before approving. |
| File gate fails | Move legitimate tests/configuration outside agent and skill folders, or reject the payload. |
| SARIF upload fails | Check code-scanning availability and permissions. The run summary and decision remain the primary demo evidence. |
| Docs-only PR reports no review needed | Expected scope decision. No reviewers ran; this is not four SAFE votes. |

Open completed run pages before presenting. Preserve a dated record if it must outlive Actions retention; artifacts and logs are not permanent archives. The [walkthrough](demo-walkthrough.md) separates execution evidence from accuracy claims.
