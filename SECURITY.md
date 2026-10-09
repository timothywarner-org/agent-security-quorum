# Security Policy

## Supported scope

This is a maintained teaching and reference project, not a security service with a response SLA. Report problems against **main** and include the release tag or commit you used. Fixes normally land on main and in a subsequent release; older versions do not have a separate backport commitment.

## Reporting a Vulnerability

Use [GitHub private vulnerability reporting](https://github.com/timothywarner-org/agent-security-quorum/security/advisories/new). Email **tim@techtrainertim.com** if that route is unavailable. Do not open a public issue for an exploitable bypass or disclose a working exploit in a routine bug report.

Include:

- A description, impact, and affected release or commit
- A minimal, synthetic reproducer that never needs real credentials
- Relevant run URLs and sanitized diagnostic excerpts
- A suggested fix, if available

The maintainer will review reports on a best-effort basis and coordinate disclosure where possible. If you receive no acknowledgement after seven days, follow up by email. Do not send tokens, private source code, complete environment dumps, or unredacted Copilot event streams.

## Scope

This policy covers this repository's workflows, prompts, extraction, aggregation, and tests. Report vulnerabilities in upstream tools or model services to their maintainers as appropriate, while privately notifying this project when its usage is affected. Deliberately malicious files under **test/fixtures/** are inert teaching data; never execute them.

## Security Design

This project is itself a security tool. Key design decisions:

- **Explicit policy:** two valid UNSAFE votes, any evaluator ERROR, or an incomplete/failed file gate fails Quorum Decision. One valid UNSAFE vote can pass and still deserves human review.
- **Credential boundary:** paid model reviews use repository secret COPILOT_PAT. The regression check uses no model credential. GitHub's per-job token is separate.
- **Least privilege:** contents: read by default; only aggregation requests pull-requests: write and security-events: write. Checkout credentials are not persisted. Fork/Dependabot reporting writes are skipped.
- **Real dependencies:** Copilot CLI and Cisco Skill Scanner are installed at pinned versions. Test-only PyYAML is also pinned. Their transitive dependencies are not a fully locked supply chain.
- **Untrusted content:** selected file contents are submitted through Copilot; model tool access is restricted and evaluation runs outside the checkout. This is not a malware sandbox. See [data handling](docs/data-handling.md).
- **Merge enforcement:** GitHub rules must require the checks and code-owner review. The PR controls its own proposed workflow and prompts, so automated results alone cannot authorize that change. See [maintenance and enforcement](docs/maintenance.md).
