# Agent Security Quorum
## Comprehensive Code Review and Claude Code Remediation Handoff

**Repository:** `timothywarner-org/agent-security-quorum`  
**Reviewed branch:** `main`  
**Reviewed commit:** `8f2302c05db27bf2236d1e5a4bda826e3dfc37cc`  
**Review date:** 2026-09-18  
**Primary target:** Claude Code in VS Code on Windows 11, modifying the repository and validating through GitHub Actions on Linux runners  
**Goal:** Make the current four-voter + deterministic-gate design technically correct, demonstrably live, maintainable, and safe enough to use as a Shift 2026 demo and as a credible reference security project.

---

# Executive Summary

The core idea is strong.

The current architecture is more interesting than “three models vote on a prompt.” The shipped design is:

1. Detect agent/skill changes.
2. Run a deterministic test-file gate.
3. Perform structural checks.
4. Run three semantic reviewers with different lenses.
5. Run Cisco Skill Scanner as a fourth voter.
6. Aggregate the four votes.
7. Fail on `>= 2` UNSAFE votes, or fail independently when the deterministic gate fires.
8. Emit PR feedback and SARIF.

That is a defensible **decision-engineering** pattern: diverse evidence, explicit policy, fail-closed behavior, and retained evidence.

However, the current `main` branch has several issues that materially weaken that story.

The two highest-priority findings are:

- **All three configured Copilot model IDs are retired as of September 18, 2026.** The workflow currently requests `gpt-4.1`, `claude-sonnet-4`, and `gemini-2.5-pro`. GitHub has retired all three. Because the workflow silently retries with Copilot’s default model, the three semantic “independent” votes can collapse onto the same default model while still being counted as separate voters.
- **Copilot CLI is launched from inside the untrusted repository checkout.** GitHub Copilot CLI discovers project-level skills, agents, custom instructions, settings, and hooks from the working tree. This repository is explicitly scanning untrusted `.github/skills/`, `.claude/skills/`, `.agents/skills/`, and agent definitions. The scanner should not execute the Copilot CLI from a directory whose configuration surface is controlled by the content being scanned.

Those two items should be fixed before treating the current 4-voter architecture as demo-ready or production-worthy.

A third major concern is supply-chain hardening: the workflow installs both `@github/copilot` and `cisco-ai-skill-scanner` without pinning versions, while GitHub Actions are referenced by mutable version tags rather than immutable commit SHAs.

Finally, the current 4-voter design was merged in PR #2 with an explicit note that **live CI was still pending**. The repository has not been pushed since that July 18 merge. Before Shift, create a controlled integration PR and preserve its real output.

---

# Priority Legend

- **P0 — Blocker:** Fix before live demo or describing the current design as validated.
- **P1 — High:** Fix before calling this a robust security gate.
- **P2 — Medium:** Important correctness, maintainability, or documentation work.
- **P3 — Nice to have:** Quality and polish improvements.

---

# P0 Findings

## P0-1 — All three configured LLM model IDs are retired

### Current code

In `.github/workflows/agent-scan.yml`:

```yaml
matrix:
  include:
    - lens: security
      model: gpt-4.1
    - lens: privilege
      model: claude-sonnet-4
    - lens: compliance
      model: gemini-2.5-pro
```

As of September 18, 2026, GitHub documents these retirement dates:

- `claude-sonnet-4` — retired 2026-05-01
- `gpt-4.1` — retired 2026-06-01
- `gemini-2.5-pro` — retired 2026-07-31

Current GitHub Copilot models include newer GPT, Claude, and Gemini families.

### Why this is worse than a stale-version problem

The workflow contains this fallback:

```bash
if [ "$EXIT_CODE" -ne 0 ] && grep -qi "not available\|unknown model\|invalid model" /tmp/copilot-stderr.txt; then
  MODEL="default"
  copilot ...
fi
```

That means:

- security can become `default`
- privilege can become `default`
- compliance can become `default`

All three can therefore become the same effective model while the aggregate job still counts them as three votes.

That defeats one of the core claims of the repository: **model-family diversity**.

### Required remediation

1. Replace retired IDs with three currently supported Copilot CLI models from distinct providers.
2. Resolve the exact IDs against the current Copilot CLI command reference during implementation.
3. Remove the silent `default` fallback from quorum-counted voters.
4. If a requested model is unavailable, emit an error result and vote UNSAFE, or fail the semantic-voter job explicitly.
5. Record both:
   - configured model
   - actual model reported by the CLI, if available in JSON output
6. Add a preflight or integration test proving all configured model IDs are available.
7. Add a repository maintenance note that model IDs are operational configuration with expected retirement churn.

### Candidate current families

Do **not** blindly copy these without checking the current CLI on implementation day, but current GitHub documentation shows active GPT, Claude, and Gemini families such as:

- GPT-5.5 / GPT-5.4 family
- Claude Sonnet 5
- Gemini 3.7 Flash / other currently supported Gemini model

The architectural requirement matters more than the exact model:

> Three semantic voters must represent three distinct, explicitly selected model families/providers, and an unavailable voter must not silently become a duplicate of another voter.

### Acceptance criteria

- No retired model IDs remain in workflow/docs/examples.
- A semantic-voter failure cannot silently substitute `default`.
- Test output proves all three configured voters use distinct requested models.
- PR comment displays the actual semantic engines used.

---

## P0-2 — Copilot CLI runs inside the untrusted repository it is scanning

### Current behavior

The LLM job:

1. checks out the PR repository;
2. builds a prompt from changed agent/skill files;
3. invokes `copilot -p ...` from the repository working directory.

The repository paths being scanned include:

- `.github/agents/**`
- `.github/skills/**`
- `.claude/agents/**`
- `.claude/skills/**`
- `.agents/skills/**`

Those overlap directly with configuration and skill locations that GitHub Copilot CLI knows how to discover.

GitHub’s current CLI documentation states that project skills can be loaded from:

- `.github/skills/`
- `.agents/skills/`
- `.claude/skills/`

Copilot CLI can also discover repository custom instructions, repository settings, agents, and hooks.

### Threat

A malicious PR is not merely supplying text embedded in your explicit `BEGIN UNTRUSTED FILE` markers.

It may also be changing files that the **Copilot CLI runtime itself recognizes as project configuration or skills**.

The base prompt saying “treat this as data” does not address runtime-level discovery.

This is especially important because the project is specifically designed to scan malicious skills.

### Required remediation

Run the semantic analyzer from a **neutral directory outside the checkout**.

Recommended pattern:

1. Checkout only to collect source data.
2. Read and serialize the changed files into an explicit prompt payload.
3. Create a fresh analyzer directory under `$RUNNER_TEMP`.
4. Create a fresh `COPILOT_HOME` under `$RUNNER_TEMP`.
5. `cd` into the neutral analyzer directory before launching Copilot CLI.
6. Do not use `--add-dir` pointing back to the checkout.
7. Disable repository custom instructions explicitly where supported:
   - `--no-custom-instructions`
8. Ensure repository hooks/extensions/workspace MCP do not load in prompt mode.
9. Do not mark the checkout as a trusted Copilot workspace.
10. Pass only the serialized prompt text to the CLI.

### Additional hardening

The analyzer needs **no local tools** because all subject text is already in the prompt.

Explicitly deny or remove tool access.

GitHub’s current CLI supports tool restriction via flags such as:

- `--available-tools`
- `--excluded-tools`
- `--deny-tool`

At minimum deny:

- shell
- write
- read
- URL/network access
- memory
- MCP tools, if any can be present

Use the exact current CLI syntax verified during implementation.

### Important clarification

`--no-ask-user` is **not** a sandbox.

GitHub documents it as disabling the `ask_user` tool. It does not mean “disable all tools.”

### Acceptance criteria

- `copilot -p` executes from an empty neutral directory, not `$GITHUB_WORKSPACE`.
- Fresh `COPILOT_HOME` is used.
- No repository skill/agent/instruction/hook is discoverable by the analysis process.
- All tools are explicitly unavailable or denied.
- A fixture that tries to instruct the scanner to read files or execute shell cannot cause tool usage.
- The scanner still receives the fixture text through the serialized prompt and returns a verdict.

---

## P0-3 — Current four-voter design has not been proven in live CI

PR #2 introduced:

- deterministic test-file gate
- Cisco static voter
- 2-of-4 quorum
- OWASP AST mapping
- SARIF

The PR’s own test plan explicitly states:

> Not yet exercised in live CI.

The repository’s current `main` has not been pushed since the July 18, 2026 merge.

This is not a criticism of the implementation effort; the PR clearly labeled the limitation. But the limitation still exists as evidence debt.

### Required remediation

Create controlled integration PRs after the P0 fixes.

Minimum live matrix:

1. **Known-good agent** → PASS
2. **Prompt injection fixture** → FAIL by quorum
3. **Privilege escalation fixture** → FAIL by quorum
4. **Data exfiltration fixture** → FAIL by quorum
5. **Wildcard-tools fixture** → expected policy result
6. **Subtle-risk fixture** → expected policy result
7. **Test-file smuggling skill** → deterministic gate FAIL
8. **One semantic voter intentionally unavailable** → fail closed without collapsing to `default`
9. **Static scanner intentionally broken** → fail closed
10. **Malformed LLM JSON** test in local/unit harness → fail closed

Capture:

- PR URL
- workflow run URL
- job summary
- PR comment
- SARIF result
- exact configured/actual model identities
- package versions
- commit SHA

### Shift demo requirement

Before the conference, preserve a known-good screenshot or saved browser tab of a **real current 4-voter run**.

Do not rely on the old 3-voter PR output to prove the current architecture.

---

# P1 Findings

## P1-1 — Unpinned `@github/copilot` package executes in a job holding the Copilot secret

Current:

```bash
npm install -g @github/copilot
```

The semantic-voter job also receives:

```yaml
COPILOT_GITHUB_TOKEN: ${{ secrets.COPILOT_PAT }}
```

An unpinned package install in the same job as a high-value token is a supply-chain risk.

### Required remediation

- Pin an exact tested `@github/copilot` version.
- Record that version in a single configuration location.
- Add a maintenance process for updating it intentionally.
- Prefer a reproducible install mechanism.
- If feasible, validate package integrity/checksum.
- Log `copilot --version` in the run.

Do not auto-track latest in a security gate.

---

## P1-2 — Unpinned Cisco scanner package

Current:

```bash
pip install cisco-ai-skill-scanner
```

The workflow comment itself acknowledges:

> Pin to a validated version in production; unpinned here so the teaching repo tracks upstream detection improvements.

That tradeoff is not appropriate for a repository being presented as a security gate.

### Required remediation

- Pin an exact tested Cisco scanner release.
- Log `skill-scanner --version`.
- Prefer hash-locked installation if practical.
- Validate the exact JSON schema against the pinned version.
- Add an upgrade checklist and regression test.

The demo can still explain that upstream evolves quickly; the code should remain reproducible.

---

## P1-3 — GitHub Actions are pinned to mutable tags, not immutable SHAs

Examples:

```yaml
actions/checkout@v4
actions/setup-node@v4
actions/upload-artifact@v4
actions/setup-python@v5
actions/download-artifact@v4
actions/github-script@v7
github/codeql-action/upload-sarif@v3
```

GitHub’s secure-use guidance recommends pinning actions to a **full-length commit SHA** because that is the immutable form.

### Required remediation

Pin every action to a verified full commit SHA and retain a comment with the human-readable version, e.g.:

```yaml
uses: actions/checkout@<full-sha> # v4.x.y
```

Automate dependency-update PRs if desired, but do not float security-control code on mutable tags.

---

## P1-4 — Global workflow permissions are broader than necessary

Current:

```yaml
permissions:
  contents: read
  pull-requests: write
  security-events: write
```

Those permissions apply across jobs unless overridden.

This means jobs that install third-party packages receive write-capable repository permissions they do not need.

### Required remediation

Set conservative workflow default:

```yaml
permissions:
  contents: read
```

Then grant job-scoped permissions only where necessary.

Suggested model:

- `detect_changes`: `contents: read`
- `test_file_gate`: `contents: read`
- `validate_structure`: `contents: read`
- `llm_scan`: `contents: read`
- `static_scan`: `contents: read`
- `aggregate`: `contents: read`, `pull-requests: write`, `security-events: write`

Also set `persist-credentials: false` on checkout jobs that do not need authenticated Git operations.

This is especially important in jobs running npm or pip-installed code.

---

## P1-5 — Cisco scanner error handling can confuse findings with operational success

Current behavior intentionally ignores the scanner exit code and decides based on parsed JSON:

```bash
set +e
skill-scanner ...
EXIT_CODE=$?
set -e
```

If JSON parses, `SCANNED` increments regardless of `EXIT_CODE`.

Cisco currently documents exit code `1` as either:

- runtime error, or
- findings when fail-on-findings is enabled.

Your invocation does not use `--fail-on-findings`, which helps, but operational failures that happen to produce parseable JSON still need a well-defined contract.

### Required remediation

With the pinned Cisco version:

1. Record exact expected exit semantics.
2. Validate expected top-level JSON schema.
3. Detect explicit error envelopes separately from scan results.
4. Treat schema mismatch or runtime-error JSON as `UNSAFE/error`.
5. Prefer Cisco’s documented structured fields instead of recursively searching every object with a `severity` key.
6. Add fixture snapshots of real Cisco JSON.

The current recursive normalization is clever defensive code, but it is intentionally schema-agnostic and therefore hard to reason about.

---

## P1-6 — Fork PRs cannot receive `COPILOT_PAT`

GitHub does not pass repository secrets to workflows triggered by pull requests from forks.

This repository is public and `CONTRIBUTING.md` invites outside contributions.

Therefore an outside contributor’s PR cannot execute the semantic voters with the current `pull_request` + secret design.

### Required remediation

Choose and document a trust model.

Safe options include:

- Explicitly state that full semantic scans only run for trusted/internal PRs and maintainers must run a controlled follow-up.
- Use a two-stage architecture where an unprivileged `pull_request` workflow produces sanitized artifacts and a trusted workflow consumes only reviewed/sanitized data.
- Use a maintainer-triggered command/label to launch the secret-bearing scan against serialized content.
- Do **not** casually switch to `pull_request_target` and then checkout/execute untrusted PR code with secrets.

Add a test for fork behavior.

---

## P1-7 — No concurrency policy; stale runs can overwrite the PR comment

Every run looks for an existing comment containing:

```text
Agent/Skill Security Scan
```

and updates it.

If two commits are pushed quickly, older and newer runs can finish out of order. An older run can overwrite the PR comment after a newer run completes.

Required status checks are tied to commits, so branch protection may still be correct, but the human-visible comment can become stale.

### Required remediation

Add workflow concurrency:

```yaml
concurrency:
  group: agent-security-quorum-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

Also include in the PR comment:

- scanned head SHA
- workflow run link
- timestamp
- scanner versions

---

## P1-8 — PR comment identification is too loose

Current:

```js
const existing = comments.find(c =>
  c.body.includes('Agent/Skill Security Scan')
);
```

This can select and overwrite a human-authored comment containing that phrase.

### Required remediation

Use an explicit stable marker, for example:

```html
<!-- agent-security-quorum-report -->
```

Then match:

- marker present
- author is the expected GitHub Actions bot, when available

This makes the update idempotent and avoids accidental human-comment edits.

---

# P2 Findings

## P2-1 — Structural validation is weaker than documentation implies

Current deterministic structural logic checks:

- frontmatter begins with `---`
- `description:` exists
- wildcard tools only when they appear on the same line as `tools:`

Example current regex:

```bash
grep -qiE 'tools:.*(\*|"all"|all)'
```

It will not reliably catch:

```yaml
tools:
  - "*"
```

It also does not deterministically enforce constraints even though project docs describe stronger structural validation.

### Required remediation

Replace grep/sed pseudo-YAML parsing with an actual YAML parser.

Validate the fields you truly want as deterministic policy.

Options:

- require description
- recognize both `tools` and `allowed-tools`
- reject wildcard access where policy says so
- optionally require a constraints section for applicable formats
- validate allowed field types

Then make the docs match the actual enforcement.

If structural validation is intentionally advisory, say so everywhere.

---

## P2-2 — Threat-model explanation is stale relative to current all-file scanning

The threat model says, in effect, that the LLM quorum cannot catch the bundled-test-file attack because the malicious code is not present in `SKILL.md`.

However, the current workflow deliberately changed `detect_changes` to include **all file types**, and the LLM prompt now receives changed non-binary files too.

Therefore a changed `reviewer.test.ts` can be visible to the LLM reviewers.

The deterministic gate remains valuable because it is:

- deterministic
- full-tree rather than diff-only
- independent of model behavior
- resilient to truncation/model misses
- able to fail even if semantic voters are unavailable

### Required remediation

Rewrite the explanation to:

> LLM review may detect the payload when the code is in the changed-file prompt, but a probabilistic semantic review is not an appropriate sole control for a known auto-execution class. The deterministic gate closes that class explicitly and scans the full tree.

That is more accurate and actually strengthens the engineering story.

---

## P2-3 — “Static analysis does not work here” contradicts the shipped architecture

README currently says:

> Static analysis does not work here.

The same README then proudly describes Cisco static analysis as the fourth voter.

### Fix

Use something like:

> Static analysis alone is insufficient for semantic attacks, but it contributes a complementary detection class.

---

## P2-4 — Repository links point to the wrong owner

The actual repository is:

```text
timothywarner-org/agent-security-quorum
```

Several locations still use:

```text
timothywarner/agent-security-quorum
```

Confirmed in:

- README fork command
- README archive/curl example
- configuration guide fork command
- configuration guide archive/curl example
- SARIF `informationUri`
- PR comment footer

### Required remediation

Replace all stale owner references.

Add a CI documentation/link check if worthwhile.

---

## P2-5 — Repository “About” description still says 2/3 quorum

Current public metadata still describes the original design:

> ... GPT, Claude, Gemini with 2/3 quorum ...

The current code is 2/4 + deterministic hard gate.

Update repository metadata before Shift.

---

## P2-6 — `SECURITY.md` is stale and currently inaccurate

It claims:

- only `contents: read` and `pull-requests: write`
- no external dependencies

Current workflow also requests:

- `security-events: write`

And it installs:

- `@github/copilot`
- `cisco-ai-skill-scanner`
- multiple GitHub Actions

### Required remediation

Rewrite `SECURITY.md` to reflect current architecture and dependency model.

Include:

- dependency pinning policy
- model retirement policy
- fail-closed semantics
- shared Copilot delivery plane
- fork-PR limitation
- responsible disclosure
- current permissions

---

## P2-7 — `CONTRIBUTING.md` and PR template conflict with current architecture

`CONTRIBUTING.md` says:

> Keep the workflow self-contained. No external scripts...

The PR template says:

> I have not added external dependencies

But the current architecture intentionally includes Cisco as an external dependency.

These rules are now ambiguous.

### Fix

Change the policy to:

> New dependencies require explicit justification, pinning, and security review.

If you decide to extract workflow logic into scripts for testability, update the “no external scripts” rule.

---

## P2-8 — `docs/PRD.md` is a historical spec but looks current

The PRD still describes:

- three evaluators
- identical prompts
- risk `low|medium|high`
- 2/3 quorum

PR #2 intentionally preserved it as historical design context.

That is reasonable, but a code agent or new contributor can easily mistake it for current architecture.

### Required remediation

Add a banner at the top:

> Historical design document. This does not describe current shipped behavior. See README / threat model / workflow for current architecture.

Or move it under:

```text
docs/history/PRD-v1.md
```

---

## P2-9 — Model-diversity claims overstate infrastructure independence

The semantic voters use different model families but all route through **GitHub Copilot CLI**.

That means the design has:

- model-family diversity
- prompt/lens diversity

It does **not** have:

- independent authentication planes
- independent service delivery
- independent outage domains

Documentation currently uses phrases such as “genuinely independent evaluations.”

### Fix

Use precise language:

> Diverse model families and analysis lenses delivered through a shared Copilot access plane.

This is especially important for the Shift story.

---

## P2-10 — Prompt-size and command-line-size behavior is unbounded

Each changed textual file contributes up to 16 KiB.

There is no:

- max changed-file count
- max total prompt size
- explicit chunking behavior

The prompt is then passed as a command-line argument:

```bash
copilot -p "$(cat /tmp/prompt.txt)"
```

Large PRs can become operational DoS or hit shell/process argument limits before model context is the limiting factor.

### Required remediation

1. Define max files and max aggregate bytes.
2. If exceeded:
   - chunk deterministically and aggregate sub-results, or
   - fail closed with a clear “manual/security review required” result.
3. Prefer a supported stdin/file-input mechanism if Copilot CLI provides one at implementation time.
4. Add boundary tests.

---

## P2-11 — Filename handling is newline-delimited, not NUL-safe

Current:

```bash
git diff --name-only ...
while IFS= read -r file
```

Git filenames can legally contain unusual characters including newlines.

A malicious path can corrupt:

- changed-file enumeration
- prompt markers
- output handling

### Required remediation

Use NUL-delimited Git output (`-z`) and serialize changed paths into a structured format such as JSON.

Alternatively, explicitly reject unsafe path characters within scanned roots.

---

## P2-12 — Root lists are duplicated throughout the workflow

The same scan roots appear in:

- workflow trigger
- `git diff`
- test-file gate
- static scanner loop
- docs

This invites drift whenever another ecosystem is added.

### Required remediation

Centralize the roots where possible.

The `on.pull_request.paths` list must remain YAML, but runtime jobs should consume one canonical configuration/manifest.

Add a test ensuring trigger paths and runtime roots remain aligned.

---

## P2-13 — One 718-line workflow is difficult to unit test

The current single-file approach made sense for a teaching prototype, but logic now includes:

- path collection
- frontmatter validation
- prompt construction
- Copilot JSONL extraction
- verdict normalization
- Cisco normalization
- quorum policy
- SARIF rendering
- PR report rendering

That is enough logic to justify testable modules.

### Recommendation

Extract pure logic into small scripts and leave Actions YAML as orchestration.

Given the maintainer environment, Node.js is a reasonable first choice, using built-in `node:test` where possible.

Candidate structure:

```text
scripts/
  collect-changes.mjs
  validate-structure.mjs
  normalize-copilot.mjs
  normalize-cisco.mjs
  aggregate.mjs
  render-sarif.mjs
  render-pr-comment.mjs

test/
  unit/
  fixtures/
```

Do not refactor for aesthetics. Refactor only where it creates deterministic unit-test seams.

---

# P3 Improvements

## Add explicit run provenance

Every report should include:

- commit SHA
- PR number
- workflow run ID / URL
- scanner version
- Copilot CLI version
- Cisco scanner version
- configured model IDs
- actual model IDs
- prompt version/hash

This turns a demo into auditable evidence.

---

## Improve SARIF location fidelity

Current SARIF anchors findings at line 1.

If the semantic output can safely include a line or range, add it to the evaluator contract.

Do not require this for the first remediation pass.

---

## Add `concurrency`

Already listed as P1 for comment correctness, but it also saves unnecessary AI-credit use.

---

## Add model-policy documentation

Models are now operational dependencies with retirement dates.

Create one section explaining how to update them and how to prove the replacement is actually in service.

---

## Consider a policy/config file

Instead of hardcoding:

- roots
- semantic models
- quorum threshold
- file-size limits
- static severity threshold

consider a simple versioned config.

Do not over-engineer this before Shift.

---

# Recommended Target Architecture

```text
PR
 |
 v
detect changed agent/skill paths
 |
 +--> deterministic test-file gate ---------------------+
 |                                                      |
 +--> deterministic structural validation               |
 |                                                      |
 +--> serialize untrusted file contents                  |
 |       |                                              |
 |       +--> neutral analyzer dir                      |
 |             fresh COPILOT_HOME                       |
 |             no repo instructions/skills/hooks        |
 |             no local tools                           |
 |             |                                        |
 |             +--> GPT-family security lens            |
 |             +--> Claude-family privilege lens        |
 |             +--> Gemini-family compliance lens       |
 |                                                      |
 +--> pinned Cisco static scanner ----------------------+
                                                        |
                                                        v
                                                normalize evidence
                                                        |
                                                        v
                                      explicit policy / quorum decision
                                                        |
                          +-----------------------------+------------------+
                          |                                                |
                          v                                                v
                    PR comment + summary                                SARIF
                          |
                          v
                 required check PASS/FAIL
```

Key rule:

> **Untrusted repository content is data to the analyzers, never analyzer configuration.**

---

# Claude Code Implementation Plan

## Phase 1 — Make the current architecture honest and runnable

### Task 1.1 — Update model configuration

- Replace retired model IDs.
- Remove `default` retry from quorum voters.
- Record requested and actual model identity.
- Update README, configuration guide, bug template, and examples.

### Task 1.2 — Isolate Copilot execution

- Build prompt while inside checkout.
- Write finalized prompt to `$RUNNER_TEMP`.
- Create fresh neutral working directory.
- Create fresh `COPILOT_HOME`.
- Launch Copilot from neutral working directory.
- Disable custom instructions.
- Disable all unnecessary tools.
- Ensure no project skills/agents/hooks load.

### Task 1.3 — Pin runtime dependencies

- Pin exact `@github/copilot` version.
- Pin exact `cisco-ai-skill-scanner` version.
- Log versions.
- Pin GitHub Actions to full SHAs.

### Task 1.4 — Scope permissions per job

- Global `contents: read`.
- Add write permissions only to aggregate/reporting job.
- Use `persist-credentials: false` where possible.

### Task 1.5 — Add concurrency

Cancel obsolete runs per PR.

---

## Phase 2 — Add deterministic tests

Extract only the logic that benefits from unit tests.

Test at least:

- SAFE/UNSAFE normalization
- malformed Copilot response
- missing evaluator result
- duplicate model identity
- quorum 0/4, 1/4, 2/4, 3/4, 4/4
- deterministic gate fail
- Cisco schema success/error
- SARIF generation
- PR comment marker/update
- weird filenames
- large input behavior

Use current fixtures as golden test vectors.

---

## Phase 3 — Live integration proof

Create controlled PRs from an internal branch so secrets are available.

For each fixture, record expected and observed behavior.

Publish a short `docs/integration-validation.md` containing:

- date
- commit
- package versions
- model identities
- fixture
- expected result
- actual result
- workflow run link

This document becomes the source of truth for the Shift demo.

---

## Phase 4 — Documentation reconciliation

Update:

- README
- SECURITY.md
- CONTRIBUTING.md
- configuration guide
- threat model
- bug template
- PR template
- repo About description
- historical PRD banner
- stale owner URLs

Run a repository-wide search for:

```text
2/3
gpt-4.1
claude-sonnet-4
gemini-2.5-pro
timothywarner/agent-security-quorum
No external dependencies
Static analysis does not work here
```

No unintended stale hits should remain outside explicitly historical material.

---

# Live-CI Acceptance Matrix

| Scenario | Expected result | Required evidence |
|---|---|---|
| `good-agent.md` | PASS | 0 or 1 UNSAFE, gate PASS |
| `good-skill/SKILL.md` | PASS | gate PASS |
| `prompt-injection.md` | FAIL | >=2 semantic/static UNSAFE |
| `data-exfiltration.md` | FAIL | >=2 UNSAFE |
| `privilege-escalation.md` | FAIL | >=2 UNSAFE |
| `wildcard-tools.md` | FAIL or explicitly documented threshold result | evidence visible |
| `subtle-risk.md` | expected policy documented | evidence visible |
| test-file smuggling skill | FAIL | deterministic gate alone sufficient |
| missing semantic model | FAIL CLOSED | no default-model substitution |
| malformed LLM output | FAIL CLOSED | `error:true` / UNSAFE |
| Cisco runtime/schema failure | FAIL CLOSED | static error/UNSAFE |
| one semantic false positive | PASS if all other controls safe | 1/4 UNSAFE |
| two semantic UNSAFE | FAIL | 2/4 |
| one semantic UNSAFE + static UNSAFE | FAIL | mixed-mode 2/4 |

---

# Demo Readiness Checklist for Shift 2026

Before rehearsal:

- [ ] Current models are supported.
- [ ] Semantic voters remain genuinely distinct.
- [ ] Copilot analyzer runs outside untrusted repo configuration scope.
- [ ] Copilot tools are disabled.
- [ ] Copilot package is pinned.
- [ ] Cisco package is pinned.
- [ ] Actions are SHA-pinned.
- [ ] Current four-voter flow has at least one real PASS run.
- [ ] Current four-voter flow has at least one real FAIL run.
- [ ] Test-file hard gate has a real FAIL run.
- [ ] PR comment displays commit SHA and actual model identities.
- [ ] Saved screenshots/tabs exist as stage fallback.
- [ ] README and repo About description match 2/4 + hard gate.
- [ ] No slide claims infrastructure independence among the three LLMs.
- [ ] The stage story remains: risky change -> diverse checks -> explicit policy -> accountable decision.

---

# Specific Code Review Notes

## `detect_changes`

Good:

- all file types are in scope
- deletions are intentionally excluded
- base-to-head comparison is explicit
- full history checkout supports diff

Improve:

- use NUL-safe changed-file handling
- prefer explicit PR head SHA over implicit `HEAD` for clarity
- serialize paths structurally
- centralize scan roots

---

## `test_file_gate`

Good:

- deterministic
- independent of quorum
- full-tree scan
- fails immediately
- directly addresses a known test-runner auto-discovery attack class

Improve:

- narrow documentation claims to the specific forbidden auto-execution class
- test case-insensitive/path edge cases if relevant
- document why each forbidden pattern is disallowed
- keep policy configurable if real users need legitimate colocated test/config files

---

## `validate_structure`

Good:

- cheap deterministic pre-check
- informational rather than pretending regex equals semantic security

Improve:

- real YAML parsing
- multiline wildcard detection
- `tools` vs `allowed-tools`
- docs must reflect whether it warns or blocks

---

## `llm_scan`

Good:

- lens-specific prompts
- fail-closed malformed response
- untrusted-content markers
- strict SAFE/UNSAFE contract
- result artifacts
- model field retained

Critical improvements:

- neutral working directory
- fresh Copilot home
- no project config discovery
- no tools
- current models
- no silent default fallback
- pinned CLI
- total-prompt size handling
- actual model identity capture

---

## `static_scan`

Good:

- complementary detection class
- normalizes to same contract
- fail closed when nothing parseable is produced
- full directory scan

Improve:

- pinned package
- validate real pinned JSON schema
- distinguish runtime errors
- stop relying indefinitely on recursive “find any severity key”
- add snapshot tests

---

## `aggregate`

Good:

- `always()` behavior is intentional
- missing evaluator counts unsafe
- deterministic gate remains independent
- fail unless explicit PASS
- useful PR/SARIF evidence

Improve:

- detect duplicate semantic engine/model identity
- add provenance
- stable bot-comment marker
- concurrency
- modularize/test pure quorum function

---

# Documentation Accuracy Corrections

## README

Change:

> Static analysis does not work here.

To:

> Static analysis alone is insufficient for semantic attacks, so the gate combines semantic model review with static analysis and deterministic controls.

Change “independent evaluators” to wording that acknowledges the shared Copilot delivery plane.

Fix wrong `timothywarner/...` URLs.

Remove/qualify “no SaaS dependencies.”

Update model names.

---

## SECURITY.md

Current statements about permissions and external dependencies are outdated.

Rewrite from current code after permission/dependency hardening.

---

## Configuration guide

Fix:

- owner URLs
- retired models
- “genuine independence” wording
- current fork PR behavior
- model maintenance process

---

## Threat model

Keep the excellent bundled-test-file story, but update the statement that LLMs cannot see the payload at all.

Current design sends changed non-Markdown files to the LLM prompt.

The deterministic gate is still justified because semantic detection is not deterministic and the gate scans the full tree.

---

## PRD

Mark as historical.

Do not let future coding agents use it as the current implementation spec.

---

# Security Principles to Preserve

Do not lose these during refactoring:

1. **Fail closed on missing evidence.**
2. **Deterministic controls stay outside the vote when appropriate.**
3. **One semantic false positive should not necessarily block.**
4. **Two independent unsafe signals should block.**
5. **Do not equate model agreement with truth.**
6. **Preserve evidence after the run.**
7. **Treat the scanned repository as hostile input.**
8. **The scanner itself must have less privilege than the thing it is evaluating.**
9. **Model diversity is useful only when it is observable and real.**
10. **A security control must be reproducible, not “latest package wins.”**

---

# What Claude Code Should Not Do

- Do not switch to `pull_request_target` and checkout untrusted PR code with secrets.
- Do not remove fail-closed behavior to make CI “less annoying.”
- Do not keep the silent `default` model fallback.
- Do not run Copilot CLI from the PR checkout after this review.
- Do not solve security isolation with prompt wording alone.
- Do not add a large framework or service layer.
- Do not bury the repo under abstractions before live validation.
- Do not update docs before code and then assume the implementation matches.
- Do not claim “independent providers” while all semantic calls use the Copilot access plane.

---

# Suggested Claude Code Prompt

Use the following as the opening instruction after placing this file in the repository:

```text
You are working in the agent-security-quorum repository.

Read CODE_REVIEW_HANDOFF.md completely before modifying anything.

Goal:
Make the current 4-voter + deterministic-gate architecture secure, reproducible, testable, and demonstrably live without changing its core product concept.

Order of work:
1. Fix all P0 findings.
2. Fix P1 supply-chain, permission, and CI correctness findings.
3. Add deterministic unit tests for extracted pure logic.
4. Run local/static validation.
5. Prepare controlled GitHub integration PRs for the acceptance matrix.
6. Reconcile documentation only after code behavior is verified.

Constraints:
- Preserve fail-closed behavior.
- Do not use pull_request_target with untrusted checkout and secrets.
- Run Copilot semantic analysis from a neutral directory outside the PR checkout.
- Do not allow Copilot CLI to load repository skills, agents, custom instructions, hooks, extensions, or MCP configuration from the untrusted repository.
- Disable all unnecessary Copilot tools.
- Remove the silent default-model fallback.
- Pin runtime dependencies and GitHub Actions.
- Prefer small, reviewable commits.
- Do not push or merge without showing me the diff and test results.

Before editing, produce:
A. a concise implementation plan,
B. the exact files you expect to change,
C. any finding from this handoff you disagree with and why.
```

---

# External References Checked During Review

GitHub Copilot CLI programmatic reference:  
https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference

GitHub Copilot CLI command reference:  
https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference

Supported GitHub Copilot models / retirement history:  
https://docs.github.com/en/copilot/reference/ai-models/supported-models

GitHub Copilot CLI security / trusted directories:  
https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-copilot-cli

GitHub Copilot skills/customization behavior:  
https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference

GitHub Actions secure use / SHA pinning:  
https://docs.github.com/en/actions/reference/security/secure-use

GitHub Actions secrets and fork PR behavior:  
https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets

Cisco AI Skill Scanner repository:  
https://github.com/cisco-ai-defense/skill-scanner

Cisco Skill Scanner CLI usage:  
https://github.com/cisco-ai-defense/skill-scanner/blob/main/docs/user-guide/cli-usage.md

---

# Bottom Line

Keep the product idea.

The architecture is worth saving.

The most important correction is conceptual:

> The semantic scanner must not let untrusted repository content become scanner configuration, and the quorum must not pretend it has diversity when retired models silently fall back to the same default.

Once those are fixed and the four-voter path is proven in a real PR, the repository becomes substantially stronger both as engineering and as a conference demo.

The Shift demo should then be able to show a truthful chain:

**one risky change -> diverse evidence -> one explicit policy -> one accountable decision.**
