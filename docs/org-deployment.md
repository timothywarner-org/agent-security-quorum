# Org-Level Deployment

Deploy the agent security scanner across all repositories in your GitHub organization.

## How It Works

GitHub supports [reusable workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows) via `workflow_call`. You move the scanner to your org's `.github` repository, and individual repos call it with a single line.

## Step 1: Move to Org `.github` Repo

Copy the workflow and scripts to your org-level repo:

```
your-org/.github/
  workflow-templates/
    agent-scan.yml              # template for new repos
  .github/
    workflows/
      agent-scan-reusable.yml   # reusable workflow
  scripts/
    detect-changes.sh
    validate-structure.sh
    llm-evaluate.sh
    aggregate.sh
  prompts/
    v1.txt
    lens-security.txt
    lens-privilege.txt
    lens-compliance.txt
```

## Step 2: Convert to Reusable Workflow

Modify `agent-scan-reusable.yml` to accept `workflow_call`:

```yaml
name: Agent/Skill Security Scan (Reusable)

on:
  workflow_call:
    secrets:
      GH_TOKEN:
        required: true

# ... rest of the workflow stays the same
```

## Step 3: Call from Any Repo

In each repo that has agent/skill files, add a thin caller workflow:

```yaml
# .github/workflows/agent-scan.yml
name: Agent Security Scan

on:
  pull_request:
    paths:
      - ".github/agents/**"
      - ".github/skills/**"
      - ".claude/agents/**"
      - ".claude/skills/**"

jobs:
  scan:
    uses: your-org/.github/.github/workflows/agent-scan-reusable.yml@main
    secrets:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

That's it. Every repo gets scanning with zero local configuration.

## Step 4: Enforce with Branch Protection

For each repo (or via org-level rulesets):

1. Go to **Settings > Branches > Branch protection rules**
2. Enable **Require status checks to pass before merging**
3. Add the `Quorum Decision` check

Or use [org-level repository rulesets](https://docs.github.com/en/organizations/managing-organization-settings/managing-rulesets-for-repositories-in-your-organization) to enforce this across all repos at once.

## Step 5: CODEOWNERS (Org-Level)

In your org `.github` repo, add a `CODEOWNERS` file that applies to inherited paths:

```
# All repos inherit these ownership rules
.github/agents/   @your-org/security-team
.github/skills/   @your-org/security-team
.claude/agents/   @your-org/security-team
.claude/skills/   @your-org/security-team
```

## Updating the Scanner

Because all repos reference the org-level workflow via `@main`, updates to the scanner are picked up automatically. Pin to a tag (e.g., `@v1`) for stability:

```yaml
uses: your-org/.github/.github/workflows/agent-scan-reusable.yml@v1
```

## Limitations

- Reusable workflows can only be called from workflows in other repos within the same org (or public repos)
- The calling repo must have Actions enabled
- Secrets must be explicitly passed (they don't inherit automatically)
