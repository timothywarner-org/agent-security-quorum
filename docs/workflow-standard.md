# Workflow standard

**Verified October 8, 2026.** Stable releases are resolved to full commit SHAs for Actions and exact versions for the analyzers. Upgrades are deliberate changes tested in a PR. A floating `latest` dependency would make yesterday's demo evidence difficult to reproduce.

## Version baseline

| Component | Release | Source |
|---|---|---|
| checkout | 7.0.1 | [Release](https://github.com/actions/checkout/releases/tag/v7.0.1) |
| setup-node | 7.1.0 | [Release](https://github.com/actions/setup-node/releases/tag/v7.1.0) |
| setup-python | 7.0.0 | [Release](https://github.com/actions/setup-python/releases/tag/v7.0.0) |
| upload-artifact | 7.0.2 | [Release](https://github.com/actions/upload-artifact/releases/tag/v7.0.2) |
| download-artifact | 8.0.2 | [Release](https://github.com/actions/download-artifact/releases/tag/v8.0.2) |
| github-script | 9.0.0 | [Release](https://github.com/actions/github-script/releases/tag/v9.0.0) |
| CodeQL upload-sarif | 4.38.3 | [Release](https://github.com/github/codeql-action/releases/tag/v4.38.3) |
| Copilot CLI | 1.0.94 | [Release](https://github.com/github/copilot-cli/releases/tag/v1.0.94) |
| Cisco Skill Scanner | 2.2.1 | [Release](https://github.com/cisco-ai-defense/skill-scanner/releases/tag/2.2.1) |
| Node.js | 24.21.0 LTS | [Official release index](https://nodejs.org/dist/index.json) |
| Python | 3.14.8 | [Runner release](https://github.com/actions/python-versions/releases/tag/3.14.8-36806082737) |

Node uses the maintained LTS line. Python uses the newest stable line supported by Cisco's declared **>=3.11,<3.15** requirement. Ubuntu is fixed to **24.04** to avoid an automatic runner-family migration; the hosted image still receives updates. Copilot uses **--no-auto-update** so it runs the installed pin. Its model selections remain explicit and must pass live checks; software release numbers do not prove model availability.

## Required behavior

| GitHub practice or security boundary | Implementation |
|---|---|
| Immutable Action dependencies | Full verified commit SHA plus exact release comment on every use |
| Minimum token permissions | Read-only workflow default; write scopes only on aggregation |
| No persisted checkout credentials | Every checkout sets persist-credentials to false |
| Required checks always report | Every PR starts detection and Quorum Decision; irrelevant changes do not run models |
| Scanner changes are exercised | Workflow/prompt changes rescan all tracked targets |
| Explicit failure policy | Two valid UNSAFE votes, any evaluation error, or an incomplete hard stop fails |
| Untrusted files remain data | No PR scripts/tests are executed; isolated model working directory; read/write/shell/URL/memory tools denied; built-in MCP disabled |
| Bounded execution | Timeout on every job; per-PR concurrency cancels superseded scans |
| Dependency installation boundary | Analyzer packages installed outside the checkout; automatic npm caching disabled |
| Evidence integrity | Reject unsupported semantic inputs, links/submodules, missing reports, analyzer failures, and partial directory scans |
| Honest reporting | ERROR is distinct from UNSAFE; skipped scope is distinct from SAFE votes; comment updates match only the bot's own report |
| Evidence retention | Result artifacts retained for 90 days, subject to repository policy; missing files are upload errors |
| Safe fork handling | Stay on pull_request; no privileged pull_request_target workaround; skip writes unavailable to forks/Dependabot |

## Maintenance

Dependabot proposes one grouped weekly update for GitHub Actions. Review its release notes and changed SHA pins; do not auto-merge. It does **not** update analyzer or runtime versions embedded in workflow environment variables. Check those versions during rehearsal maintenance, update the four constants together when needed, and rerun the scanner. Keep prereleases out of this baseline.

Test a harmless input, a risky input, missing/invalid reviewer evidence, and the no-relevant-change path. Recheck Cisco report parsing whenever its version changes. Review scan duration, false alarms, missed fixtures, and request usage before expanding the design.

Dependabot PRs may lack COPILOT_PAT. A reviewed update needs a trusted maintainer branch to exercise paid reviewers with the existing credential. Never expose a secret merely to make an automated update green.

## Boundaries this file cannot enforce

Require **Quorum Decision** and code-owner approval in repository rules if they should gate merging. CODEOWNERS protects the workflows, prompts, Dependabot configuration, and itself only when review is enforced. A contributor can propose editing the PR's own workflow; SHA pins do not stop that. This workflow is not configured for a merge queue and does not claim merge_group coverage.

Analyzer package versions are exact, but their transitive package dependencies are resolved during installation. That is not a fully locked software supply chain. The Actions workflow remains a compact teaching example, not an attested build environment or a runtime sandbox.

## First-party guidance

- [GitHub Actions secure use reference](https://docs.github.com/en/actions/reference/security/secure-use): least privilege, SHA pinning, untrusted input, CODEOWNERS, dependency maintenance.
- [Workflow path filters and required checks](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onpull_requestpull_request_targetpathspaths-ignore): why detection is inside the workflow.
- [Keep Actions updated with Dependabot](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/auto-update-actions).
- [setup-node caching guidance](https://github.com/actions/setup-node/blob/v7.1.0/README.md): disable unneeded automatic caching for sensitive workflows.
- [Copilot tool permissions](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/allowing-tools).
