# Contributing to Agent Security Quorum

Thanks for your interest in contributing. This project is open to contributions of all kinds — bug fixes, new features, documentation improvements, and test fixtures.

## Getting Started

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Open a pull request

## What We Need

- **Prompt improvements** — better rubrics, fewer false positives, more attack pattern examples in `prompts/`
- **Test fixtures** — new agent/skill files in `test/fixtures/` that cover edge cases
- **Model support** — testing with additional Copilot CLI models as they become available
- **Documentation** — corrections, clarifications, translations
- **JSONL extraction hardening** — if you encounter a Copilot CLI output format we don't handle, open an issue with the raw output

## Guidelines

- Keep the workflow self-contained. No external scripts, no build steps, no npm project.
- Prompts should be as short as possible. Every token costs money across 3 models per PR.
- Test your changes by opening a PR that includes agent/skill files — the scanner will run automatically.
- Follow conventional commit format: `feat:`, `fix:`, `docs:`, `test:`, `chore:`

## Reporting Issues

Open an issue at https://github.com/timothywarner-org/agent-security-quorum/issues with:

- What you expected to happen
- What actually happened
- The CI log output (if applicable)

## Contact

- **Tim Warner** — maintainer
- Website: [TechTrainerTim.com](https://techtrainertim.com)
- Email: tim@techtrainertim.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
