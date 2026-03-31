# Agent Security Quorum

A GitHub Actions workflow that scans AI agent and skill definition files for security risks. Uses GitHub Copilot CLI to run 3 parallel LLM evaluations with a 2/3 quorum — consensus on UNSAFE fails the build.

## How It Works

```
PR changes agent/skill files
        │
        ▼
┌─────────────────┐
│ Detect Changes   │  ← git diff filtered to agent/skill paths
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────────────────────────────┐
│ Validate         │     │ LLM Scan (3x parallel matrix)             │
│ Structure        │     │                                           │
│ (deterministic)  │     │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│                  │     │  │ Security │ │ Privilege│ │Compliance│ │
│ YAML frontmatter │     │  │   lens   │ │   lens   │ │   lens   │ │
│ required fields  │     │  └────┬─────┘ └────┬─────┘ └────┬─────┘ │
└────────┬────────┘     └───────┼─────────────┼────────────┼───────┘
         │                      │             │            │
         ▼                      ▼             ▼            ▼
         │              ┌──────────────────────────────────────┐
         └─────────────►│ Quorum: ≥2 UNSAFE → FAIL the build  │
                        └──────────────────────────────────────┘
```

Each evaluator uses a different analytical lens so the quorum has genuine diversity, not 3 identical calls. A single false positive won't block your PR.

## Tutorial: Get Scanning in 5 Minutes

### Prerequisites

- A GitHub repository with [GitHub Actions](https://docs.github.com/en/actions) enabled
- [GitHub Copilot](https://docs.github.com/en/copilot) access on the repo (Business or Enterprise plan, or individual with Copilot enabled)

### Step 1: Fork or Copy

**Option A — Fork this repo** to get everything including test fixtures:

```bash
gh repo fork timothywarner/agent-security-quorum --clone
```

**Option B — Copy into an existing project.** You need two things:

```
your-repo/
  .github/workflows/agent-scan.yml   ← the workflow
  prompts/                            ← the prompt templates
    v1.txt
    lens-security.txt
    lens-privilege.txt
    lens-compliance.txt
```

Copy them in:

```bash
# From inside your repo
curl -sL https://github.com/timothywarner/agent-security-quorum/archive/main.tar.gz | \
  tar xz --strip-components=1 \
    agent-security-quorum-main/.github/workflows/agent-scan.yml \
    agent-security-quorum-main/prompts/
```

### Step 2: Create a Branch and Add an Agent File

```bash
git checkout -b test-agent-scan
mkdir -p .github/agents
```

Create `.github/agents/my-agent.md` with some content:

```markdown
---
name: my-helper
description: Helps answer questions about the codebase.
tools:
  - Read
  - Grep
---

# My Helper

You answer questions about the codebase. Only read files — never modify anything.
```

### Step 3: Push and Open a PR

```bash
git add .github/agents/my-agent.md
git commit -m "feat: add my-helper agent"
git push -u origin test-agent-scan
gh pr create --title "Add my-helper agent" --body "Testing the agent security scanner."
```

### Step 4: Watch the Scan Run

Go to the **Actions** tab on your PR. You'll see four jobs:

1. **Detect Changes** — finds your new agent file
2. **Validate Structure** — checks YAML frontmatter for required fields
3. **LLM Scan (security / privilege / compliance)** — three parallel evaluations
4. **Quorum Decision** — aggregates votes and posts the result

### Step 5: Check the Results

The workflow posts a comment on your PR:

```
## ✅ Agent/Skill Security Scan

| Evaluator  | Verdict   |
|------------|-----------|
| security   | ✅ SAFE   |
| privilege  | ✅ SAFE   |
| compliance | ✅ SAFE   |

**Quorum: PASS** (0/3 UNSAFE)
```

If the agent had dangerous instructions, you'd see:

```
## ❌ Agent/Skill Security Scan

| Evaluator  | Verdict    |
|------------|------------|
| security   | ❌ UNSAFE  |
| privilege  | ❌ UNSAFE  |
| compliance | ✅ SAFE    |

**Quorum: FAIL** (2/3 UNSAFE)

### Findings
- Prompt injection: instructions attempt to override system constraints
- Agent reads SSH keys and sends data to external URL
```

The build fails, blocking the PR from merging.

### Step 6: Try It with a Dangerous Agent

Test with one of the included fixtures. Copy `test/fixtures/prompt-injection.md` into your agents folder:

```bash
cp test/fixtures/prompt-injection.md .github/agents/sneaky-agent.md
git add .github/agents/sneaky-agent.md
git commit -m "test: add agent with prompt injection"
git push
```

The scanner should catch it and fail the build.

### Step 7 (Optional): Enforce with Branch Protection

Lock it down so UNSAFE agents can't be merged:

1. Go to **Settings > Rules > Rulesets** (or Branch protection rules)
2. Target your default branch
3. Add **Require status checks to pass**
4. Search for and add the **Quorum Decision** check
5. Save

Now no PR that modifies agent/skill files can merge without passing the scan.

## What Gets Scanned

| Location | Format | Platform |
|----------|--------|----------|
| `.github/agents/*.md` | Markdown + YAML frontmatter | GitHub Copilot |
| `.github/skills/*/SKILL.md` | Markdown + YAML frontmatter | GitHub Copilot |
| `.claude/agents/*.md` | Markdown + YAML frontmatter | Claude Code |
| `.claude/skills/*/SKILL.md` | Markdown + YAML frontmatter | Claude Code |

## What Gets Flagged

- **Prompt injection** — instructions that override constraints or claim special modes
- **Privilege escalation** — bypassing reviews, force-pushing, disabling safety checks
- **Unsafe tool access** — wildcard permissions, unrestricted shell execution
- **Data exfiltration** — reading secrets/keys and sending to external URLs
- **Ambiguous authority** — vague scope with no explicit constraints

## Repository Structure

```
.github/
  workflows/
    agent-scan.yml       ← the entire scanner (single workflow, no scripts)
  CODEOWNERS             ← require review for agent/skill changes
prompts/
  v1.txt                 ← base evaluation prompt with rubric
  lens-security.txt      ← security-focused framing
  lens-privilege.txt     ← privilege/authority-focused framing
  lens-compliance.txt    ← compliance/guardrails-focused framing
test/
  fixtures/              ← sample agent/skill files for testing
docs/
  org-deployment.md      ← guide for org-level deployment
```

## Dependencies

None beyond what GitHub-hosted runners already provide:

- `jq` — pre-installed
- `yq` — pre-installed
- `gh` CLI — pre-installed (Copilot extension installed in workflow)

## Org-Level Deployment

To deploy across all repos in your organization using a reusable workflow, see [docs/org-deployment.md](docs/org-deployment.md).

## Extending

The evaluator contract is intentionally simple — each returns:

```json
{ "verdict": "SAFE|UNSAFE", "findings": ["..."] }
```

Future versions will support pluggable evaluators (Azure OpenAI, local models, third-party APIs). The quorum logic is evaluator-agnostic by design.

## License

MIT
