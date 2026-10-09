# Fixture scorecard

**Intended behavior is a hypothesis; observed results are evidence.** The nine fixtures below were scanned individually with Cisco Skill Scanner **2.2.1** on **October 8, 2026**, using static analysis only. A HIGH or CRITICAL finding votes UNSAFE. Lower-severity findings can still accompany SAFE.

| Fixture | Intended outcome | Observed static vote | Interpretation |
|---|---|---|---|
| good-agent.md | PASS | SAFE | Harmless agent baseline; informational license finding |
| good-skill/ | PASS | SAFE | Harmless skill baseline; informational license finding |
| prompt-injection.md | FAIL | UNSAFE | Three CRITICAL YARA findings plus an informational finding |
| data-exfiltration.md | FAIL | SAFE | Static miss at the voting threshold; requires contextual review |
| privilege-escalation.md | FAIL | SAFE | Static miss at the voting threshold; requires contextual review |
| wildcard-tools.md | FAIL | SAFE | Broad tool permissions were not a blocking static finding |
| subtle-risk.md | Human review | SAFE | Borderline scenario; a split model vote has not been recorded individually |
| missing-description.md | Advisory | SAFE | LOW vague-description finding; structure warnings are not a hard stop |
| testfile-smuggling-skill/ | FAIL via file gate | SAFE | LOW destination finding; the deterministic filename rule remains essential |

These are **single observations**, not estimates of sensitivity, false-positive rate, or comparative model performance. No individual live model results were captured for this nine-case recheck. The separate [historical risky run](evidence/v0.1.0/risky-historical.json) combined risky inputs and a bundled test payload, producing four UNSAFE votes and a failed hard stop; it does not isolate each fixture's contribution.

The machine-readable [catalog](../test/fixture-catalog.json) records intended outcomes, static findings, null entries for unmeasured individual model results, and hashes of both canonical Git content and the actual scanned copies. Its [frozen release snapshot](evidence/v0.1.0/static-fixtures.json) remains dated evidence when the working catalog changes.

## Reproduce a static observation

1. Read the fixture as inert text. Never execute its code or place it in an active agent directory.
2. Copy **one** fixture into an otherwise empty temporary directory. Preserve all files in a skill package.
3. Run `skill-scanner scan-all <isolated-directory> --recursive --lenient --format json` using **cisco-ai-skill-scanner==2.2.1**, or identify a different version explicitly in your comparison.
4. Record findings, analyzer failures, skipped skills, runtime environment, and input hashes. An empty or failed scan is an error, not SAFE.
5. Compare the HIGH/CRITICAL threshold with the intended outcome; preserve misses and false alarms.

Do not scan the mixed fixture catalog in one call to claim complete coverage. Cisco 2.2.1's recursive discovery can omit loose Markdown in a parent containing manifest-based skill packages. Static scanning requires no model token. Live model testing is a separate, maintainer-reviewed exercise described in [CONTRIBUTING](../CONTRIBUTING.md).

## Extend the catalog

Follow the [contribution roadmap](community-roadmap.md). Give each new fixture a minimal enterprise purpose, explicit intended outcome, and a reason the existing examples do not cover it. Do not invent model results or change historical evidence when a newer scanner behaves differently.
