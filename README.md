<p align="center">
  <img src="images/logo.png" alt="Agent Security Quorum" width="400">
</p>

# Agent Security Quorum

[![Website](https://img.shields.io/badge/TechTrainerTim.com-4285F4?style=for-the-badge&logo=google-chrome&logoColor=white)](https://techtrainertim.com)
[![GitHub Org](https://img.shields.io/badge/timothywarner--org-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/timothywarner-org)
[![GitHub](https://img.shields.io/badge/timothywarner-6e40c9?style=for-the-badge&logo=github&logoColor=white)](https://github.com/timothywarner)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

Automated security scanning for AI agent and skill definition files in GitHub pull requests, using multi-model LLM consensus to catch prompt injection, privilege escalation, and data exfiltration before merge.

## Why This Matters

- **Agent definitions are executable attack surface.** Files in `.github/agents/`, `.claude/agents/`, and similar paths are instructions that AI systems follow at runtime. A malicious or compromised agent file can exfiltrate secrets, bypass review gates, or escalate privileges — and it looks like plain Markdown.
- **Static analysis does not work here.** These attacks are semantic, embedded in natural language. No linter or regex will catch "ignore all previous instructions" or "read ~/.ssh/id_rsa and POST it to an external endpoint."
- **Four independent evaluators per PR, across two detection classes.** Three LLM lenses (security, privilege, compliance) run on different model families, plus a static-analysis voter (Cisco's open-source skill-scanner: YARA, AST dataflow, taint analysis). A bypass has to defeat two fundamentally different detection methods, not just fool three language models.
- **2/4 quorum prevents single-model blind spots.** One false positive will not block your PR. Two independent evaluators must agree a file is unsafe before the build fails.
- **Deterministic test-file gate blocks the bundled-payload bypass.** A skill can ship a clean `SKILL.md` alongside a `*.test.ts` file that test runners auto-discover and execute with developer credentials — no agent involved, so LLM scanners miss it ([Gecko Security, 2026](https://www.gecko.security/blog/rce-in-your-test-suite-ai-agent-skills-bypass-skill-scanners)). A hard, non-voting gate fails the build on any test, spec, or build-config file inside a skill directory.
- **Findings map to the OWASP Agentic Skills Top 10** (AST01–AST10) and surface in the GitHub Security tab as SARIF, so they survive after the PR closes and feed code-scanning campaigns.
- **Zero infrastructure.** Runs entirely in GitHub Actions using Copilot CLI plus a pip-installed static scanner. No servers, no SaaS dependencies, no additional cost beyond your existing Copilot subscription.

## Architecture

```
PR touches agent/skill files (ALL files, not just *.md)
         |
         v
+-------------------+
| Detect Changes    |  git diff filtered to agent/skill directories
+--------+----------+
         |
         +----------------------+-------------------------+
         v                      v                         v
+-------------------+  +-------------------+   +---------------------------+
| Test-File Gate    |  | Validate          |   | Evaluators (4x parallel)  |
| (deterministic)   |  | Structure         |   |                           |
|                   |  | (deterministic)   |   | LLM lenses (3 models):    |
| No *.test.*,      |  |                   |   |  Security / Privilege /   |
| *.spec.*,         |  | YAML frontmatter  |   |  Compliance               |
| conftest.py,      |  | required fields   |   | Static analysis (1):      |
| *.config.* in     |  |                   |   |  cisco-skill-scanner      |
| skill dirs        |  |                   |   |  (YARA + AST + taint)     |
+--------+----------+  +--------+----------+   +-------------+-------------+
         |                                                   |
         | hard fail                                         v
         |                            +----------------------------------------+
         +--------------------------->| Quorum: 2/4 UNSAFE = FAIL,             |
                                      | OR test-file gate fired = FAIL         |
                                      | Findings -> PR comment + SARIF (AST01-10)|
                                      +----------------------------------------+
```

Evaluators span two detection classes (semantic LLM judgment and static analysis) on different model families, so the quorum has genuine diversity. A single false positive will not block your PR. The test-file gate is separate: it is deterministic and non-voting, and any match fails the build outright. See [docs/threat-model.md](docs/threat-model.md) for the attack it closes.

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

Go to the **Actions** tab on your PR. You'll see six jobs:

1. **Detect Changes** — finds your new agent file
2. **Test-File Gate** — hard-fails on any test/spec/config file inside a skill directory
3. **Validate Structure** — checks YAML frontmatter for required fields
4. **LLM Scan (security / privilege / compliance)** — three parallel evaluations on different models
5. **Static Scan (cisco-skill-scanner)** — the fourth voter, YARA + AST + taint analysis
6. **Quorum Decision** — aggregates votes, posts the result, and uploads SARIF to the Security tab

### Step 6: Check the Results

The workflow posts a comment on your PR:

```
## ✅ Agent/Skill Security Scan

| Evaluator      | Engine              | Verdict |
|----------------|---------------------|---------|
| security       | gpt-4.1             | ✅ SAFE |
| privilege      | claude-sonnet-4     | ✅ SAFE |
| compliance     | gemini-2.5-pro      | ✅ SAFE |
| static         | cisco-skill-scanner | ✅ SAFE |
| test-file gate | deterministic       | ✅ PASS |

**Quorum: PASS** (0/4 UNSAFE)
```

If the agent had dangerous instructions, you'd see:

```
## ❌ Agent/Skill Security Scan

| Evaluator      | Engine              | Verdict   |
|----------------|---------------------|-----------|
| security       | gpt-4.1             | ❌ UNSAFE |
| privilege      | claude-sonnet-4     | ❌ UNSAFE |
| compliance     | gemini-2.5-pro      | ✅ SAFE   |
| static         | cisco-skill-scanner | ❌ UNSAFE |
| test-file gate | deterministic       | ✅ PASS   |

**Quorum: FAIL** (3/4 UNSAFE)

### Findings

**security** (gpt-4.1):
- **AST01** `.github/agents/sneaky-agent.md`: Prompt injection: instructions attempt to override system constraints
- **AST01** `.github/agents/sneaky-agent.md`: Data exfiltration: reads SSH keys and sends data to external URL
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

Every file under these directories is scanned, not only the instruction markdown. Bundled scripts and test files are part of the attack surface (see the threat model), so they are in scope too.

| Location | Platform |
|----------|----------|
| `.github/agents/**` | GitHub Copilot |
| `.github/skills/**` | GitHub Copilot |
| `.claude/agents/**` | Claude Code |
| `.claude/skills/**` | Claude Code |
| `.agents/skills/**` | Cross-platform (`npx skills add` install target) |

## What Gets Flagged

Findings map to the [OWASP Agentic Skills Top 10](https://owasp.org/www-project-agentic-skills-top-10/).

- **Prompt injection** (AST01) — instructions that override constraints, claim special modes, or address the scanner itself
- **Supply chain / bundled payloads** (AST02) — test, spec, or build-config files inside a skill directory that execute through the developer toolchain
- **Privilege escalation & over-privilege** (AST03) — wildcard permissions, unrestricted shell, tools exceeding stated purpose
- **Data exfiltration** (AST01) — reading secrets/keys and sending to external URLs
- **Untrusted external instructions** (AST05) — fetching remote content and following it as instructions
- **Weak isolation** (AST06) — path traversal, home directory or system-file access
- **Scanner/review bypass** (AST08) — instructions to skip reviews, disable hooks, or defeat CI checks
- **Ambiguous authority / no governance** (AST09) — vague scope with no explicit constraints

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
    testfile-smuggling-skill/  ← clean SKILL.md + malicious *.test.ts (AST02 demo)
docs/
  threat-model.md        ← controls mapped to OWASP AST, the test-file bypass
  org-deployment.md      ← guide for org-level deployment
  configuration-guide.md ← install, models, prompts, quorum, troubleshooting
```

## Dependencies

- `jq`, `perl` — pre-installed on GitHub runners
- `node` / `npm` — pre-installed on GitHub runners (used to install Copilot CLI)
- `python` / `pip` — pre-installed on GitHub runners (used to install the static scanner)
- `@github/copilot` — installed in-workflow via npm
- `cisco-ai-skill-scanner` — installed in-workflow via pip (the fourth quorum voter)
- A `COPILOT_PAT` secret with the "Copilot Requests" permission

## Org-Level Deployment

To deploy across all repos in your organization using a reusable workflow, see [docs/org-deployment.md](docs/org-deployment.md).

## Extending

The evaluator contract is intentionally simple. Each evaluator writes `results/<name>.json`:

```json
{
  "verdict": "SAFE|UNSAFE",
  "findings": [
    { "id": "AST01", "file": ".claude/agents/x.md", "detail": "one-sentence description" }
  ],
  "model": "engine-name",
  "lens": "name"
}
```

`id` is an OWASP Agentic Skills Top 10 category (`AST01`–`AST10`, or `UNMAPPED`). The quorum counts verdicts; the aggregator folds every evaluator's findings into one SARIF file for code scanning. Because the contract is engine-agnostic, the static scanner sits in the same quorum as the three LLM lenses — you add a voter by writing one more `results/<name>.json` and adding its name to the quorum loop.

The [Cisco skill-scanner](https://github.com/cisco-ai-defense/skill-scanner) is already wired in as the static voter. Adding another engine (Azure OpenAI, a local model, NVIDIA SkillSpector) is the same one-file pattern.

## License

MIT
