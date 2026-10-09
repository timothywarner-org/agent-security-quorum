# Maintenance and enforcement

**Tim Warner is the current maintainer.** Support is best effort. Contributions should improve a measured weakness, reduce maintenance, or clarify a teaching point.

## Main branch policy

The publication baseline uses two branch rulesets, visible in [repository rules](https://github.com/timothywarner-org/agent-security-quorum/rules):

| Rule group | Requirement |
|---|---|
| Main checks | Changes go through a PR; **Quorum Decision** and **Policy regression** must pass against the current base. Check results must come from GitHub Actions. Force pushes and branch deletion are blocked. No bypass actor is configured for this group. |
| Main review | One approving review, code-owner review for owned paths, and dismissal of stale approvals. Maintainer **timothywarner** can bypass this review group **through a PR only**, which leaves a bypass audit record. |

The review exception is intentional for a repository with one listed maintainer: authors cannot approve their own PRs. It does not bypass the separate required checks or permit direct pushes. Contributors' changes still need maintainer review. GitHub settings are the enforcement authority; copying these files into another repository does not copy its rules. Revisit the exception when another maintainer joins.

Workflows and tests run from the proposed PR checkout. A contributor can propose changing the checks themselves. Code-owner review and review of the exact commit remain essential; this is not an independently attested security boundary.

## Maintenance rhythm

1. Review grouped weekly Dependabot Action updates. Never auto-merge them merely because checks pass.
2. Check embedded analyzer/runtime versions and test-only PyYAML during release or rehearsal maintenance. Dependabot's current GitHub Actions configuration does not update those package pins.
3. Run the weekly/manual Copilot Access Probe. Rotate COPILOT_PAT before expiry. Its 14-day warning intentionally stops before the model checks; it is not a vulnerability verdict.
4. After scanner or prompt upgrades, run regression checks and compare a harmless live case with selected risk fixtures. Keep individual model findings and known misses in the scorecard.
5. Publish a new tag with release notes and dated evidence when adopting a new baseline. Never rewrite a published tag to replace inconvenient results.

## Release checklist

- All required PR checks pass on the reviewed commit; no uncommitted release inputs.
- The public guides match permissions, dependencies, trigger behavior, and failure policy.
- Fixture evidence identifies the exact bytes, scanner version, method, date, and limitations.
- Archived run summaries distinguish observed results, synthetic tests, and intended outcomes.
- Release assets are sanitized, checksummed, and tied to the released source commit.

Use [the roadmap](community-roadmap.md) for bounded work. A dashboard, extra reviewer, or provider framework needs evidence of a problem it would solve.
