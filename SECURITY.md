# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public issue.**

Instead, email the maintainer directly:

- **Tim Warner** — tim@techtrainertim.com

Include:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

You should receive a response within 48 hours. We will work with you to understand the issue and coordinate a fix before any public disclosure.

## Scope

This policy covers the Agent Security Quorum scanner itself — the workflow, prompts, and extraction logic. It does not cover the security of the AI models invoked by the scanner (GPT, Claude, Gemini), which are operated by their respective providers.

## Security Design

This project is itself a security tool. Key design decisions:

- **Fail-safe default**: if an LLM evaluator fails or returns invalid output, it votes UNSAFE (blocks the PR)
- **No secrets in code**: the only secret is the `COPILOT_PAT` stored in GitHub Actions secrets
- **Minimal permissions**: the workflow requests only `contents: read` and `pull-requests: write`
- **No external dependencies**: runs entirely on GitHub-hosted runners with pre-installed tools
