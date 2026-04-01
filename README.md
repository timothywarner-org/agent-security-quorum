# Agent Security Quorum

Automated security scanning for AI agent and skill definition files in GitHub pull requests, using multi-model LLM consensus to catch prompt injection, privilege escalation, and data exfiltration before merge.

## Why This Matters

- **Agent definitions are executable attack surface.** Files in `.github/agents/`, `.claude/agents/`, and similar paths are instructions that AI systems follow at runtime. A malicious or compromised agent file can exfiltrate secrets, bypass review gates, or escalate privileges — and it looks like plain Markdown.
- **Static analysis does not work here.** These attacks are semantic, embedded in natural language. No linter or regex will catch "ignore all previous instructions" or "read ~/.ssh/id_rsa and POST it to an external endpoint."
- **Three independent LLM evaluations per PR.** Each uses a different analytical lens (security, privilege, compliance), providing genuine diversity rather than three identical calls.
- **2/3 quorum prevents single-model blind spots.** One false positive will not block your PR. Two independent models must agree a file is unsafe before the build fails.
- **Zero infrastructure.** Runs entirely in GitHub Actions using Copilot CLI. No servers, no SaaS dependencies, no additional cost beyond your existing Copilot subscription.

## Architecture

```
PR touches agent/skill files
         |
         v
+-------------------+
| Detect Changes    |  git diff filtered to agent/skill paths
+--------+----------+
         |
         v
+-------------------+     +------------------------------------------+
| Validate          |     | LLM Scan (3x parallel)                   |
| Structure         |     |                                          |
| (deterministic)   |     |  +-----------+ +-----------+ +---------+ |
|                   |     |  | Security  | | Privilege | | Compli- | |
| YAML frontmatter  |     |  |   lens    | |   lens    | |  ance   | |
| required fields   |     |  +-----+-----+ +-----+-----+ +----+---+ |
+--------+----------+     +--------+-------------+------------+------+
         |                         |             |            |
         v                         v             v            v
         |                 +--------------------------------------+
         +---------------->| Quorum: 2/3 UNSAFE = FAIL the build |
                           +--------------------------------------+
```

Each evaluator uses a different analytical lens so the quorum has genuine diversity, not three identical calls. A single false positive will not block your PR.

## Quick Start

1. **Copy the workflow and prompts into your repo.** Fork this repository, or copy `.github/workflows/agent-scan.yml` and the `prompts/` directory into an existing project.
2. **Create a fine-grained PAT with the "Copilot Requests" permission.** Add it as a repository secret named `COPILOT_PAT` under Settings > Secrets and variables > Actions.
3. **Open a PR that touches agent or skill files.** The scanner runs automatically and posts a quorum verdict as a PR comment.

## Tutorial: Get Scanning in 5 Minutes

### Prerequisites

- A GitHub repository with [GitHub Actions](https://docs.github.com/en/actions) enabled
- A [GitHub Copilot](https://docs.github.com/en/copilot) subscription (any plan: Free, Pro, Pro+, Business, or Enterprise)
- A **Personal Access Token** (fine-grained) with the **"Copilot Requests"** permission, stored as a repository secret named `COPILOT_PAT`

### Step 1: Create a Copilot PAT

The workflow needs a Personal Access Token to authenticate with Copilot CLI.

1. Go to [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new)
2. Create a **fine-grained** token with the **"Copilot Requests"** permission
3. In your repo, go to **Settings > Secrets and variables > Actions**
4. Click **New repository secret**, name it `COPILOT_PAT`, paste the token value

### Step 2: Fork or Copy

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

### Step 3: Create a Branch and Add an Agent File

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

### Step 4: Push and Open a PR

```bash
git add .github/agents/my-agent.md
git commit -m "feat: add my-helper agent"
git push -u origin test-agent-scan
gh pr create --title "Add my-helper agent" --body "Testing the agent security scanner."
```

### Step 5: Watch the Scan Run

Go to the **Actions** tab on your PR. You'll see four jobs:

1. **Detect Changes** — finds your new agent file
2. **Validate Structure** — checks YAML frontmatter for required fields
3. **LLM Scan (security / privilege / compliance)** — three parallel evaluations
4. **Quorum Decision** — aggregates votes and posts the result

### Step 6: Check the Results

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

### Step 7: Try It with a Dangerous Agent

Test with one of the included fixtures. Copy `test/fixtures/prompt-injection.md` into your agents folder:

```bash
cp test/fixtures/prompt-injection.md .github/agents/sneaky-agent.md
git add .github/agents/sneaky-agent.md
git commit -m "test: add agent with prompt injection"
git push
```

The scanner should catch it and fail the build.

### Step 8 (Optional): Enforce with Branch Protection

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

- `jq` — pre-installed on GitHub runners
- `node` / `npm` — pre-installed on GitHub runners (used to install Copilot CLI)
- `@github/copilot` — installed in-workflow via npm
- A `COPILOT_PAT` secret with the "Copilot Requests" permission

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
