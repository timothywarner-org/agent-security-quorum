# Adoption across repositories

**Start with one repository and an accountable maintainer.** This project ships ordinary pull-request workflows, not a ready-made reusable workflow service.

1. Copy both workflows and **prompts/** into a pilot repository.
2. Provide **COPILOT_PAT** as a repository secret, or an organization secret restricted to the intended repositories.
3. Run the access probe and harmless/risky integration examples. Inspect actual findings and review effort.
4. Decide whether **Quorum Decision** should be required. Account for path-filtered and fork PR behavior in the [configuration guide](configuration-guide.md).
5. Add **CODEOWNERS** in each repository and require approvals for workflow and prompt changes.

Do not assume an organization **.github** repository automatically makes these workflows or ownership rules apply everywhere. Keep the copied scanner version documented and review upgrades as normal changes.

## When centralization earns its keep

A reusable workflow becomes useful when maintaining copies causes measurable drift. Before introducing **workflow_call**, define the caller event contract, permissions, secret mapping, and where trusted prompts and scanner code are checked out. Test it in a separate pilot.

There is no **scripts/** directory to copy. The built-in Actions token is not a drop-in replacement for this repository's **COPILOT_PAT** configuration. Check current support and organization policy before changing authentication.

The owner should review false alarms, missed fixture detections, usage, run duration, and time spent investigating results. Keep model reviewers only when their extra findings justify that work.
