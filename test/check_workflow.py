"""Run 36 deterministic workflow cases without secrets, models, or fixture execution.

Usage from the repository root: python test/check_workflow.py
Requires Python 3.11+, PyYAML, Git, Bash, jq, and Perl. Windows uses Git Bash.
The tests extract production shell from YAML so policy changes cannot drift
away from a separate Python reimplementation of the decision rule.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.safe_load((REPO / ".github/workflows/agent-scan.yml").read_text(encoding="utf-8"))
WINDOWS_BASH = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git/bin/bash.exe"
BASH = str(WINDOWS_BASH) if os.name == "nt" and WINDOWS_BASH.exists() else shutil.which("bash")


def shell_path(path):
    """Keep Git Bash paths explicit rather than relying on argument conversion."""
    path = Path(path).resolve()
    return "/" + path.drive[0].lower() + path.as_posix()[2:] if os.name == "nt" else str(path)


def step(job, name):
    """Read the named production step and fail if its contract was renamed."""
    return next(item["run"] for item in WORKFLOW["jobs"][job]["steps"] if item.get("name") == name)


def run_shell(script, cwd, variables=None):
    """Use GitHub's Bash error behavior, with bounded execution and local outputs."""
    if "${{" in script:
        raise ValueError("A GitHub expression needs an explicit test value")
    target = cwd / "step.sh"
    target.write_text(script, encoding="utf-8", newline="\n")
    env = dict(os.environ, GITHUB_OUTPUT=shell_path(cwd / "outputs.txt"),
               GITHUB_STEP_SUMMARY=shell_path(cwd / "summary.md"), RUNNER_TEMP=shell_path(cwd))
    env.update(variables or {})
    return subprocess.run([BASH, "--noprofile", "--norc", "-eo", "pipefail", shell_path(target)],
                          cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=30)


def git(cwd, *args, data=None):
    """Never modify the user's checkout, identity, hooks, or global Git settings."""
    result = subprocess.run(["git", *args], cwd=cwd, input=data, text=True,
                            capture_output=True, encoding="utf-8", timeout=30)
    if result.returncode:
        raise RuntimeError(f"Disposable Git operation failed: {result.stderr}")
    return result.stdout.strip()


class WorkflowTests(unittest.TestCase):
    """Exercise policy boundaries with inert reports in disposable directories."""

    def setUp(self):
        """Restrict cleanup to the unique test directory beneath the system temp root."""
        self.temporary = tempfile.TemporaryDirectory(prefix="asq-policy-")
        self.root = Path(self.temporary.name).resolve()
        if not self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()):
            raise RuntimeError("Unexpected temporary directory")
        self.addCleanup(self.temporary.cleanup)

    def case(self, name):
        """Separate outputs so one passing case cannot supply a missing later artifact."""
        target = self.root / name
        target.mkdir()
        return target

    def test_quorum(self):
        """An error is never counted as ordinary dissent that could still pass."""
        cases = [
            ("four-safe", ["SAFE"] * 4, "success", "PASS", 0, 0),
            ("one-dissent", ["UNSAFE", "SAFE", "SAFE", "SAFE"], "success", "PASS", 1, 0),
            ("two-unsafe", ["UNSAFE", "UNSAFE", "SAFE", "SAFE"], "success", "FAIL", 2, 0),
            ("four-unsafe", ["UNSAFE"] * 4, "success", "FAIL", 4, 0),
            ("failed-evaluator", ["ERROR", "SAFE", "SAFE", "SAFE"], "success", "FAIL", 0, 1),
            ("safe-with-error", ["SAFE_ERROR", "SAFE", "SAFE", "SAFE"], "success", "FAIL", 0, 1),
            ("missing-artifact", ["MISSING", "SAFE", "SAFE", "SAFE"], "success", "FAIL", 0, 1),
            ("malformed-artifact", ["MALFORMED", "SAFE", "SAFE", "SAFE"], "success", "FAIL", 0, 1),
            ("unknown-verdict", ["UNKNOWN", "SAFE", "SAFE", "SAFE"], "success", "FAIL", 0, 1),
            ("missing-findings", ["NO_FINDINGS", "SAFE", "SAFE", "SAFE"], "success", "FAIL", 0, 1),
            ("hard-stop", ["SAFE"] * 4, "failure", "FAIL", 0, 0),
            ("cancelled-gate", ["SAFE"] * 4, "cancelled", "FAIL", 0, 0),
            ("dissent-and-error", ["UNSAFE", "ERROR", "SAFE", "SAFE"], "success", "FAIL", 1, 1),
            ("no-artifacts", ["MISSING"] * 4, "success", "FAIL", 0, 4),
        ]
        for name, votes, gate, expected, unsafe, errors in cases:
            with self.subTest(case=name):
                case = self.case(name)
                (case / "results").mkdir()
                for lens, vote in zip(["security", "privilege", "compliance", "static"], votes):
                    target = case / "results" / (lens + ".json")
                    if vote == "MISSING":
                        continue
                    data = {"verdict": vote, "findings": [], "model": "test-engine", "lens": lens}
                    if vote in ("ERROR", "SAFE_ERROR"):
                        data.update(verdict="SAFE" if vote == "SAFE_ERROR" else "UNSAFE", error=True)
                    if vote == "NO_FINDINGS":
                        data = {"verdict": "SAFE"}
                    target.write_text("{bad json" if vote == "MALFORMED" else json.dumps(data), encoding="utf-8")
                script = step("aggregate", "Apply quorum").replace("${{ needs.test_file_gate.result }}", gate)
                result = run_shell(script, case)
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs = dict(line.split("=", 1) for line in (case / "outputs.txt").read_text().splitlines())
                self.assertEqual((outputs["result"], int(outputs["unsafe"]), int(outputs["errors"])),
                                 (expected, unsafe, errors))
                self.assertTrue(outputs["headline"].startswith("Scan passed:" if expected == "PASS" else "Scan failed:"))

    def test_final_decision(self):
        """Missing scope evidence must not be mistaken for a successful no-op."""
        for name, detection, scope, decision, success in [
            ("no-review", "success", "false", "", True),
            ("passed", "success", "true", "PASS", True),
            ("failed", "success", "true", "FAIL", False),
            ("no-decision", "success", "true", "", False),
            ("failed-detection", "failure", "", "PASS", False),
            ("missing-scope", "success", "", "PASS", False),
            ("cancelled-detection", "cancelled", "false", "PASS", False),
        ]:
            with self.subTest(case=name):
                result = run_shell(step("aggregate", "Enforce final decision"), self.case(name),
                                   {"DETECTION_RESULT": detection, "HAS_CHANGES": scope, "DECISION": decision})
                self.assertEqual(result.returncode == 0, success, result.stderr)

    def test_scope(self):
        """Use real Git diffs, including names that Windows cannot check out."""
        for scenario, wanted in [("docs", "false"), ("agent", "true"), ("workflow", "true"),
                                 ("deletion", "false"), ("symlink", "ERROR"), ("newline", "ERROR")]:
            with self.subTest(case=scenario):
                case = self.case(scenario)
                git(case, "init", "--quiet")
                for key, value in [("user.name", "Workflow verifier"), ("user.email", "verifier@example.invalid"),
                                   ("commit.gpgsign", "false"), ("core.autocrlf", "false"),
                                   ("core.hooksPath", str(case / "no-hooks"))]:
                    git(case, "config", key, value)
                agent = case / ".github/agents/reviewer.md"
                agent.parent.mkdir(parents=True)
                agent.write_text("Read files and report findings.\n", encoding="utf-8")
                (case / "README.md").write_text("Baseline\n", encoding="utf-8")
                git(case, "add", ".")
                git(case, "commit", "--quiet", "-m", "baseline")
                base = git(case, "rev-parse", "HEAD")
                if scenario == "docs":
                    (case / "README.md").write_text("Documentation update\n", encoding="utf-8")
                elif scenario == "agent":
                    agent.write_text("Report failed checks without bypassing them.\n", encoding="utf-8")
                elif scenario == "workflow":
                    changed = case / ".github/workflows/agent-scan.yml"
                    changed.parent.mkdir()
                    changed.write_text("# Updated scanner\n", encoding="utf-8")
                elif scenario == "deletion":
                    agent.unlink()
                else:
                    blob = git(case, "hash-object", "-w", "--stdin", data="../../outside-tree\n")
                    path = ".github/agents/link" if scenario == "symlink" else ".github/agents/new\nline.md"
                    mode = "120000" if scenario == "symlink" else "100644"
                    # The hostile name exists only in this disposable index.
                    git(case, "-c", "core.protectNTFS=false", "update-index", "--add", "--cacheinfo", f"{mode},{blob},{path}")
                if scenario not in ("symlink", "newline"):
                    git(case, "add", ".")
                git(case, "commit", "--quiet", "-m", scenario)
                result = run_shell(step("detect_changes", "Find changed agent/skill files"), case, {"BASE_SHA": base})
                if wanted == "ERROR":
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(f"has_changes={wanted}", (case / "outputs.txt").read_text())

    def test_static_reports(self):
        """Fake only the scanner process; production shell validates its evidence."""
        for scenario, verdict, error in [
            ("safe", "SAFE", False), ("high", "UNSAFE", False), ("partial", "UNSAFE", True),
            ("malformed", "UNSAFE", True), ("empty-object", "UNSAFE", True), ("empty-results", "UNSAFE", True),
            ("failed-analyzer", "UNSAFE", True), ("skipped-skill", "UNSAFE", True), ("process-error", "UNSAFE", True),
        ]:
            with self.subTest(case=scenario):
                case = self.case(scenario)
                (case / ".github/skills").mkdir(parents=True)
                (case / ".claude/skills").mkdir(parents=True)
                binary = case / "bin"
                binary.mkdir()
                stub = binary / "skill-scanner"
                stub.write_text('#!/usr/bin/env bash\n'
                                'if [ "$SCENARIO" = partial ] && [ "$2" = .claude/skills ]; then exit 2; fi\n'
                                'cat "$REPORT"\n'
                                'if [ "$SCENARIO" = process-error ]; then exit 2; fi\nexit 0\n',
                                encoding="utf-8", newline="\n")
                stub.chmod(0o755)
                report = {"summary": {}, "results": [{"findings": []}]}
                if scenario == "high":
                    report["results"][0]["findings"] = [{"severity": "HIGH", "title": "Policy violation", "file_path": ".github/skills/reviewer/SKILL.md"}]
                if scenario == "failed-analyzer":
                    report["results"][0]["analyzers_failed"] = [{"name": "static", "error": "incomplete"}]
                if scenario == "empty-results":
                    report["results"] = []
                if scenario == "skipped-skill":
                    report["summary"]["skills_skipped"] = [{"name": "reviewer", "reason": "unreadable"}]
                content = "{bad json" if scenario == "malformed" else "{}" if scenario == "empty-object" else json.dumps(report)
                (case / "report.json").write_text(content, encoding="utf-8")
                script = f'export PATH="{shell_path(binary)}:$PATH"\n' + step("static_scan", "Scan agent/skill directories")
                result = run_shell(script, case, {"SCENARIO": scenario, "REPORT": shell_path(case / "report.json")})
                self.assertEqual(result.returncode, 0, result.stderr)
                parsed = json.loads((case / "results/static.json").read_text())
                self.assertEqual((parsed["verdict"], parsed.get("error", False)), (verdict, error))


if __name__ == "__main__":
    if not BASH:
        raise SystemExit("Bash is required. On Windows, install Git for Windows.")
    subprocess.run([BASH, "-c", "command -v git jq perl >/dev/null"], check=True, timeout=10)
    unittest.main(verbosity=2)
