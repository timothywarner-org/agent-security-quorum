# Data handling

**Only submit files you are permitted to send through your Copilot account.** File paths under a scanned root are not a confidentiality boundary. The workflow reviews their contents.

| Stage | Data and destination |
|---|---|
| Change detection | Git metadata stays on the GitHub-hosted runner. Workflow/prompt changes select all tracked targets; ordinary agent changes select changed files. |
| Model review | Selected text file paths and full contents, plus the review prompts, go through GitHub Copilot in three separate requests using the configured models. Unsupported binary or oversized files cause an error. |
| Static analysis | Cisco's static analyzers run on the Actions runner. This workflow does not enable Cisco's optional hosted analysis integrations. Installing packages still contacts package registries. |
| Feedback | Model findings, static findings, paths, requested model names, and decision summaries appear in Actions. Eligible same-repository PRs also receive a comment and SARIF upload. |
| Diagnostics | CLI and scanner diagnostics can include source fragments. Repository logs, comments, code-scanning results, and artifacts have their own visibility and retention behavior. |
| Regression check | Synthetic reports and temporary Git repositories stay within the test process and runner. No Copilot credential or model request is used. |

The configured Actions retention is **90 days** as verified October 9, 2026; repository settings may change. Comments and release assets are separate records. This project does not set or attest the upstream model service's data retention, training, regional processing, or organization policies. Review your account's current GitHub Copilot terms and controls before using confidential material.

## Sharing a diagnostic

1. Prefer the public run URL, commit, check name, and a short description.
2. Reproduce with synthetic Contoso or Tailwind Traders content when possible.
3. Remove tokens, personal data, internal URLs, and private source from excerpts. GitHub's secret masking is not a guarantee that arbitrary sensitive content is removed.
4. Never post a complete Copilot JSONL stream: it can contain the echoed input prompt and files.
5. Use [private vulnerability reporting](../SECURITY.md) for an exploitable bypass.

The [release evidence](evidence/v0.1.0/README.md) deliberately preserves selected verdicts and counts rather than raw prompts, logs, or diagnostic dumps.
