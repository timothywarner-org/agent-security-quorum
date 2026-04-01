# Configuration and Usage Guide

This guide covers everything you need to install, configure, and operate the Agent Security Quorum scanner. It assumes you are familiar with GitHub Actions and have administrative access to the target repository.

---

## 1. Prerequisites

### GitHub Actions

GitHub Actions must be enabled on your repository. For organization-owned repos, an org admin may need to allow Actions under **Settings > Actions > General**.

### GitHub Copilot Subscription

The scanner invokes the GitHub Copilot CLI (`@github/copilot`) to send prompts to LLMs. Any Copilot plan works: Free, Pro, Pro+, Business, or Enterprise. The specific models available to you depend on your plan tier.

### Fine-Grained Personal Access Token (PAT)

The workflow authenticates to Copilot via a PAT stored as a repository secret. You must use a **fine-grained** token (not a classic token) with the **"Copilot Requests"** permission.

#### Creating the PAT Step by Step

1. Navigate to [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new).
2. Select **Fine-grained token**.
3. Give it a descriptive name, such as `agent-security-quorum-copilot`.
4. Set an expiration. 90 days is a reasonable starting point; you will need to rotate it before expiry.
5. Under **Repository access**, select the repositories where you will use the scanner (or "All repositories" if deploying org-wide).
6. Under **Permissions**, expand **Account permissions** and enable **Copilot Requests** with read access.
7. Click **Generate token** and copy the value immediately. You will not be able to see it again.

#### Storing the PAT as a Repository Secret

1. In your repository, go to **Settings > Secrets and variables > Actions**.
2. Click **New repository secret**.
3. Set the name to `COPILOT_PAT` (this exact name is referenced in the workflow).
4. Paste the token value.
5. Click **Add secret**.

For organization-wide deployment, store the secret at the org level under **Organization settings > Secrets and variables > Actions** and grant access to the relevant repositories.

---

## 2. Installation

You need exactly two things in your repository: the workflow file and the prompts directory.

### Required Files

```
your-repo/
  .github/
    workflows/
      agent-scan.yml          # The workflow definition
  prompts/
    v1.txt                    # Base evaluation prompt with rubric
    lens-security.txt         # Security-focused framing
    lens-privilege.txt        # Privilege/authority-focused framing
    lens-compliance.txt       # Compliance/guardrails-focused framing
```

### Option A: Fork the Repository

Forking gives you the complete project including test fixtures, documentation, and CODEOWNERS:

```bash
gh repo fork timothywarner/agent-security-quorum --clone
```

### Option B: Copy into an Existing Project

If you already have a repository and want to add scanning to it, copy only the necessary files:

```bash
# From inside your existing repo
curl -sL https://github.com/timothywarner/agent-security-quorum/archive/main.tar.gz | \
  tar xz --strip-components=1 \
    agent-security-quorum-main/.github/workflows/agent-scan.yml \
    agent-security-quorum-main/prompts/
```

Alternatively, copy the files manually:

1. Download `.github/workflows/agent-scan.yml` and place it at the same path in your repo.
2. Download the entire `prompts/` directory (4 files) and place it at the repository root.

### Verifying the Workflow Is Registered

After pushing the workflow file:

1. Go to the **Actions** tab in your repository.
2. Look for "Agent/Skill Security Scan" in the workflow list on the left sidebar.
3. If it does not appear, verify the file is at exactly `.github/workflows/agent-scan.yml` and that Actions are enabled.

The workflow only triggers on pull requests that modify agent/skill paths, so it will not appear in the run history until a qualifying PR is opened.

---

## 3. How It Works

The scanner is a single GitHub Actions workflow with four jobs that run in sequence.

### The 4-Job Pipeline

```
detect_changes --> validate_structure --> llm_scan (3x parallel) --> aggregate
```

#### Job 1: detect_changes

Runs `git diff` between the PR base and HEAD, filtered to agent/skill file paths. If no matching files changed, all subsequent jobs are skipped. The list of changed files is base64-encoded and passed as a job output.

#### Job 2: validate_structure

A deterministic (non-LLM) check that examines each changed file for:

- YAML frontmatter presence (file starts with `---`)
- A `description` field in the frontmatter
- Wildcard or unrestricted tool access patterns (e.g., `tools: *` or `tools: "all"`)

Structural warnings are informational. They do not block the PR on their own; the LLM quorum is the gate.

#### Job 3: llm_scan (matrix)

Three parallel matrix jobs, each evaluating the changed files through a different analytical lens and model:

| Lens       | Model            | Focus                                |
|------------|------------------|--------------------------------------|
| security   | GPT-4.1          | Prompt injection, data exfiltration  |
| privilege  | Claude Sonnet 4  | Permission escalation, scope creep   |
| compliance | Gemini 2.5 Pro   | Missing guardrails, policy gaps      |

Each job:

1. Concatenates all changed file contents into a single text block.
2. Prepends the lens-specific prompt and the base evaluation prompt (`v1.txt`).
3. Sends the combined prompt to the Copilot CLI with `--output-format json`.
4. Parses the JSONL event stream to extract the model's text response.
5. Uses Perl balanced-brace matching to locate the JSON verdict block.
6. Validates the verdict is exactly `SAFE` or `UNSAFE`.
7. Falls back to `UNSAFE` if parsing fails (fail-safe behavior).
8. Uploads the result as a GitHub Actions artifact.

#### Job 4: aggregate (Quorum Decision)

Downloads all three evaluation artifacts and applies the quorum rule:

- Counts `SAFE` and `UNSAFE` verdicts across the three lenses.
- Missing or unparseable results count as `UNSAFE`.
- **If 2 or more evaluators vote UNSAFE, the quorum result is FAIL** and the job exits with code 1, failing the check.
- Posts a summary table as a comment on the PR.
- Updates the GitHub Actions job summary.

### Trigger Conditions

The workflow fires on `pull_request` events when changes touch any of these paths:

```
.github/agents/**
.github/skills/**
.claude/agents/**
.claude/skills/**
```

Within those directories, the `git diff` step further narrows to these specific patterns:

```
.github/agents/*.md
.github/skills/*/SKILL.md
.claude/agents/*.md
.claude/skills/*/SKILL.md
```

### JSONL Extraction

The Copilot CLI in programmatic mode (`--output-format json`) outputs a stream of newline-delimited JSON events rather than plain text. Each event has a `type` field and a `data` payload. The workflow extracts text content by:

1. Selecting events where `.data` is not null.
2. Trying known content field names: `.content`, `.text`, `.message`, `.delta`, `.body`.
3. If the primary selector returns nothing, falling back to recursive string extraction (`.. | strings`).
4. Searching the combined text for a JSON object containing a `"verdict"` key using balanced brace matching.

### The Quorum Rule

The quorum threshold is **2 out of 3**. This means:

- 0 UNSAFE = PASS
- 1 UNSAFE = PASS (single dissent tolerated; prevents false-positive blocking)
- 2 UNSAFE = FAIL
- 3 UNSAFE = FAIL

A single evaluator flagging a concern is noted in findings but does not block the PR. This design absorbs model-level false positives while still catching genuinely dangerous agent definitions.

---

## 4. Model Configuration

### The 3-Model Ensemble

The default configuration uses three different model families to ensure diversity of analysis:

| Matrix Entry | Model             | Lens       | Rationale                                    |
|--------------|-------------------|------------|----------------------------------------------|
| 1            | `gpt-4.1`        | security   | Strong at detecting injection and exfiltration |
| 2            | `claude-sonnet-4` | privilege  | Strong at reasoning about authority and scope  |
| 3            | `gemini-2.5-pro`  | compliance | Strong at identifying policy gaps              |

The diversity is intentional. Three identical model calls would be highly correlated in their errors; using different model families produces genuinely independent evaluations.

### Changing Models

Models are configured in the `strategy.matrix` block of the `llm_scan` job. To change a model, edit the `model` value:

```yaml
strategy:
  matrix:
    include:
      - lens: security
        model: gpt-4.1          # Change this to use a different model
      - lens: privilege
        model: claude-sonnet-4   # Change this to use a different model
      - lens: compliance
        model: gemini-2.5-pro    # Change this to use a different model
```

You can use any model identifier supported by the Copilot CLI and available on your plan. Common alternatives include `gpt-4o`, `claude-sonnet-3.5`, or `o3-mini`.

### Model Fallback Behavior

If the specified model is not available on your Copilot plan (or the identifier is unrecognized), the workflow automatically retries with the default model:

```bash
# From the workflow:
if [ "$EXIT_CODE" -ne 0 ] && grep -qi "not available\|unknown model\|invalid model" /tmp/copilot-stderr.txt; then
    echo "Model '$MODEL' not available — retrying with default model..."
    MODEL="default"
    copilot -p "$(cat /tmp/prompt.txt)" --output-format json --no-ask-user > /tmp/copilot-output.jsonl
fi
```

When fallback occurs, the result JSON records `"model": "default"` so you can see in the PR comment which evaluator used a fallback.

### Cost Considerations

Each scan invokes the Copilot CLI three times (once per matrix job). The cost depends on:

- **Your Copilot plan** -- Business and Enterprise plans may have different rate limits and included usage.
- **Model tier** -- Premium models (GPT-4.1, Claude Sonnet 4, Gemini 2.5 Pro) consume more quota or credits than standard models. Check your Copilot plan's model multipliers.
- **Prompt size** -- Larger agent/skill files produce longer prompts. The workflow logs the character count for each evaluation.

If cost is a concern, you can switch to lower-tier models in the matrix configuration. The quorum logic works with any model that can follow the prompt format and return valid JSON.

---

## 5. Customizing Prompts

### How the Prompt System Works

Each evaluation assembles a prompt from three parts, concatenated in this order:

```
[lens prompt]  +  [base prompt (v1.txt)]  +  [changed file contents]
```

For example, the security evaluator sends:

```
{contents of prompts/lens-security.txt}

{contents of prompts/v1.txt}
FILE: .github/agents/my-agent.md
{contents of the file}
```

### Editing the Base Prompt (prompts/v1.txt)

The base prompt defines the evaluation contract: the role, the output format, the UNSAFE criteria, and the SAFE criteria. It also contains worked examples.

Key sections you might customize:

**UNSAFE criteria (lines 9-16 of v1.txt).** These are the six categories the evaluator checks. You can add criteria (e.g., "7. Cost abuse: instructions that would trigger expensive operations") or adjust existing ones.

**SAFE criteria (lines 18-22 of v1.txt).** These define what a passing agent looks like. Tighten these to raise the bar (e.g., require explicit `constraints:` frontmatter) or loosen them for less restrictive environments.

**Examples (lines 24-41 of v1.txt).** The worked examples calibrate the model's judgment. Add examples that reflect your organization's specific patterns, especially edge cases you have encountered.

Important: the prompt instructs the model to return exactly one line of raw JSON with no markdown fences. Do not add instructions that would cause the model to wrap its output in code blocks, as this will break the JSON extraction.

### Editing Lens Prompts

Each lens prompt is a short directive (under 10 lines) that focuses the evaluator's attention. The three lenses are:

- **lens-security.txt** -- Focuses on prompt injection, data exfiltration, obfuscation, and external communication.
- **lens-privilege.txt** -- Focuses on tool/purpose mismatch, escalation patterns, authority inflation, and conditional escalation.
- **lens-compliance.txt** -- Focuses on missing constraints, boundary enforcement, approval bypass, and least privilege violations.

To add a new lens:

1. Create `prompts/lens-yourname.txt` with a `LENS:` directive and evaluation criteria.
2. Add a new entry to the matrix in the workflow:
   ```yaml
   - lens: yourname
     model: your-preferred-model
   ```
3. Update the quorum threshold in the `aggregate` job if you want to change the voting math. The current loop iterates over `security privilege compliance`; add your lens to that list.
4. Adjust the quorum threshold. With 4 evaluators, you might want 3/4 UNSAFE to fail, or keep 2/4 for a stricter gate.

### Tips for Prompt Effectiveness

- **Be explicit about output format.** Models are more reliable when the expected JSON schema is spelled out with examples.
- **Use negative constraints.** Telling the model what NOT to do ("Do NOT execute code, read files, or call tools") reduces hallucinated tool use.
- **Test across models.** A prompt that works well with GPT-4.1 may need adjustment for Gemini. Run the scanner against your test fixtures after changing prompts.
- **Keep lens prompts short.** The lens is a framing directive, not a full rubric. The rubric lives in `v1.txt`.

---

## 6. Understanding Results

### The PR Comment Format

After the quorum job completes, the workflow posts (or updates) a comment on the PR with this structure:

```
## [PASS/FAIL icon] Agent/Skill Security Scan

| Evaluator  | Model            | Verdict     |
|------------|------------------|-------------|
| security   | gpt-4.1          | SAFE/UNSAFE |
| privilege  | claude-sonnet-4  | SAFE/UNSAFE |
| compliance | gemini-2.5-pro   | SAFE/UNSAFE |

**Quorum: PASS/FAIL** (N/3 UNSAFE)
```

If any evaluator voted UNSAFE, its findings are listed below the table. When the quorum result is FAIL, findings are shown inline. When the quorum result is PASS but one evaluator dissented, findings are collapsed inside a `<details>` block.

### What SAFE and UNSAFE Mean

**SAFE** means the evaluator found no issues matching its lens criteria. All five SAFE conditions from the base prompt were satisfied:

1. Tools are explicitly listed and minimal for the stated purpose.
2. A constraints section defines what the agent cannot do.
3. No instructions bypass safety controls or approval gates.
4. No access to secrets, credentials, or external endpoints.
5. Scope matches description with no excess permissions.

**UNSAFE** means the evaluator found at least one issue matching any of the six UNSAFE criteria: prompt injection, privilege escalation, unsafe tool access, data exfiltration, ambiguous authority, or scope mismatch. The specific findings are listed in the `findings` array.

### How Findings Are Extracted

Each model returns a JSON object:

```json
{"verdict": "UNSAFE", "findings": ["finding 1", "finding 2"]}
```

The workflow extracts this from the JSONL event stream using balanced-brace matching (a Perl regex that handles nested JSON). Findings from all UNSAFE evaluators are collected, deduplicated, and displayed in the PR comment grouped by evaluator and model.

### "Evaluation failed -- fail-safe triggered"

If the workflow cannot extract a valid verdict from a model's response, it records:

```json
{
  "verdict": "UNSAFE",
  "findings": ["Evaluation failed or returned invalid response"],
  "model": "...",
  "error": true
}
```

This is the fail-safe mechanism: when in doubt, vote UNSAFE. Common causes:

- The model returned markdown-wrapped JSON instead of raw JSON.
- The JSONL stream was empty (authentication failure or network issue).
- The model produced a verdict value other than `SAFE` or `UNSAFE` (e.g., `"MOSTLY_SAFE"`).
- The Copilot CLI exited with an error and produced no output.

To debug, expand the failing matrix job in the Actions log and look for:

- `Copilot CLI exit code` -- non-zero indicates a CLI-level failure.
- `JSONL output: N lines, M bytes` -- zero lines or zero bytes means no response was received.
- `Extracted text: N chars` -- zero chars means the JSONL parser found no text content.
- `Event types` -- shows what event types were present in the stream, which helps diagnose parsing issues.

---

## 7. Branch Protection

### Adding the Required Status Check

To prevent PRs with UNSAFE agent definitions from being merged:

1. Go to **Settings > Rules > Rulesets** in your repository (or **Settings > Branches > Branch protection rules** for legacy configuration).
2. Create a new ruleset targeting your default branch (e.g., `main`).
3. Enable **Require status checks to pass before merging**.
4. In the status check search box, type `Quorum Decision` and select it.
5. Save the ruleset.

The "Quorum Decision" check is the name of the aggregate job. It will appear in the search results only after the workflow has run at least once on the repository.

Note: the scan only triggers when agent/skill files are modified. PRs that do not touch those paths will not have the check at all and will not be blocked.

### Organization-Level Rulesets

For org-wide enforcement:

1. Go to your **Organization settings > Rules > Rulesets**.
2. Create a ruleset that targets all repositories (or a specific subset).
3. Add the `Quorum Decision` required status check.
4. This ensures every repo in the org enforces the scan when agent/skill files change.

For full org-level deployment details including reusable workflows, CODEOWNERS, and centralized prompt management, see [org-deployment.md](org-deployment.md).

---

## 8. Troubleshooting

### PAT Has Wrong Type or Permissions

**Symptom:** The Copilot CLI fails to authenticate. The stderr log shows authentication or permission errors.

**Fix:** Verify you created a **fine-grained** token (not a classic token) with the **Copilot Requests** permission. Classic tokens do not support this permission scope. Regenerate the token if needed and update the `COPILOT_PAT` secret.

### Model Not Available on Your Plan

**Symptom:** The log shows `Model 'gpt-4.1' not available -- retrying with default model...` and the PR comment shows `default` in the Model column.

**Explanation:** This is expected behavior, not an error. The workflow automatically falls back to the default Copilot model. The evaluation still runs. If you want to use specific models, verify they are included in your Copilot subscription tier.

### Empty JSONL Output

**Symptom:** The log shows `JSONL output: 0 lines, 0 bytes` and the fail-safe triggers.

**Possible causes:**

- The `COPILOT_PAT` secret is missing or expired. Check **Settings > Secrets and variables > Actions** and verify the secret exists and has not expired.
- The Copilot CLI is not installed correctly. Check the "Install Copilot CLI" step for npm errors.
- A network issue prevented the CLI from reaching the Copilot API. Re-run the workflow to see if it is transient.

### Verdict Extraction Fails Despite Non-Empty Output

**Symptom:** The log shows extracted text with a non-zero character count, but the fail-safe still triggers.

**Possible causes:**

- The model wrapped its JSON response in markdown code fences (`` ```json ... ``` ``). The balanced-brace extractor handles this in most cases, but unusual formatting can break it.
- The model returned a verdict value other than `SAFE` or `UNSAFE`. The workflow strictly checks for these two exact strings.
- The model returned multiple JSON objects and the first one with a `"verdict"` key was malformed.

**How to diagnose:** Expand the matrix job log and search for "Extracted text" to see exactly what the model returned. If the JSON is present but in an unexpected format, you may need to adjust the extraction logic or the prompt instructions.

### Reading the CI Logs

Each matrix job logs diagnostic information at every stage:

| Log Line                              | What It Tells You                                      |
|---------------------------------------|--------------------------------------------------------|
| `Evaluating with X lens (N chars)...` | The total prompt size sent to the model                |
| `Copilot CLI exit code: N`            | 0 = success, non-zero = CLI failure                    |
| `Copilot CLI stderr:`                 | Error messages from the CLI                            |
| `JSONL output: N lines, M bytes`      | Whether the CLI produced any response                  |
| `Event types:`                        | The types of events in the JSONL stream                |
| `Extracted text: N chars`             | How much text was recovered from the event stream      |
| `Verdict: SAFE` or `Verdict: UNSAFE`  | The final parsed verdict (absent if fail-safe triggered)|
| `FAIL-SAFE: No valid verdict...`      | Extraction failed; this evaluator votes UNSAFE by default|

### The Fail-Safe Mechanism

The scanner is designed to fail closed. Any failure in the evaluation pipeline (CLI error, parsing error, unexpected model output, missing artifact) results in an UNSAFE vote for that evaluator. This means:

- If one evaluator fails and the other two return SAFE, the quorum is PASS (1 UNSAFE out of 3).
- If two evaluators fail, the quorum is FAIL regardless of the third evaluator's result.
- If all three evaluators fail, the quorum is FAIL.

This ensures that infrastructure issues do not silently allow unsafe agent definitions to be merged. If you see repeated fail-safe triggers, investigate the root cause rather than treating UNSAFE as the normal state.

### Workflow Does Not Trigger

If the workflow does not run when you open a PR:

- Verify the PR modifies files under `.github/agents/`, `.github/skills/`, `.claude/agents/`, or `.claude/skills/`.
- Verify the workflow file is on the default branch (the `pull_request` trigger requires the workflow to exist on the base branch).
- Check that GitHub Actions is enabled for the repository.
- Look at the Actions tab for any workflow errors or disabled-workflow warnings.
