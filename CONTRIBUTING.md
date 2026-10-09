# Contributing to Agent Security Quorum

Contribute a reproducible finding, a focused fix, or a teaching example. Keep the product small: workflows and prompts, with a separate test harness for repeatable policy checks.

## Getting Started

1. Start with the [fixture scorecard](docs/fixture-scorecard.md) and [contribution roadmap](docs/community-roadmap.md).
2. Fork the repository and create a branch from main.
3. Make one focused change. Treat malicious fixtures as data; do not run their code or install them as active agent skills.
4. Run the deterministic checks below, or let **Community Checks / Policy regression** run on your PR. No Copilot subscription or token is needed for these checks. GitHub may require maintainer approval before a first-time contributor's workflow runs.
5. Open a PR with the problem, evidence, and validation. State explicitly if live model evaluation was not performed.

## Verify without a model account

Requirements: Python 3.11+, Git, Bash, jq, and Perl. The hosted Ubuntu check supplies the command-line tools. On Windows, use Git for Windows and make jq available in Git Bash.

```powershell
python -m pip install --requirement test/requirements.txt
python test/check_workflow.py
```

The four test groups cover **36 cases** against shell extracted from the real scanner workflow: quorum, final decision, changed-file detection, and static report validation. They do not call models, execute attack fixtures, or measure detection accuracy. Prefer the hosted check if you do not want local tooling.

## Fork PRs and live reviews

GitHub does not normally give fork or Dependabot PRs this repository's COPILOT_PAT. **Policy regression** can pass while a relevant **Quorum Decision** fails because model evidence is unavailable. Unrelated changes receive a scope-based PASS. A fixture-only change does not automatically run that fixture through the models.

For a change needing live review, the maintainer inspects the exact diff, especially workflows, prompts, package configuration, and test code, before applying it to a same-repository branch. Preserve the original contribution's attribution and cross-link both PRs. Review the fresh run before merging the maintainer PR, then close the original as incorporated. Never use pull_request_target to execute an untrusted checkout with privileged credentials.

## What We Need

- **Fixtures:** minimal enterprise scenarios with intended outcomes, observed results, and known misses. Use the scorecard's evidence format.
- **Parser regressions:** synthetic JSONL that demonstrates an extraction failure without disclosing the original prompt or credentials.
- **Prompt improvements:** a before/after comparison that includes false alarms as well as detected risks.
- **Documentation:** verify instructions against the current release and identify the source of any product claim.

## Guidelines

- Keep scanner runtime logic inline. The small test-only harness is an intentional exception; do not add an application, build system, or provider framework.
- Keep prompts concise. Live reviews make three separate model calls and consume the maintainer's entitlement.
- Keep tests isolated from **test/fixtures/**. Never use unrestricted test discovery that could execute a deliberately hostile file.
- Follow conventional commit format: `feat:`, `fix:`, `docs:`, `test:`, `chore:`

## Reporting Issues

For ordinary defects, [open an issue](https://github.com/timothywarner-org/agent-security-quorum/issues/new/choose) with:

- What you expected to happen
- What actually happened
- Release or commit, run URL, and a sanitized diagnostic excerpt

Remove credentials, private source, personal data, and internal URLs. Complete CLI event streams can echo source files. For exploitable vulnerabilities, follow [SECURITY.md](SECURITY.md) instead.

## Contact

- **Tim Warner**, maintainer
- Website: [TechTrainerTim.com](https://techtrainertim.com)
- Email: tim@techtrainertim.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
