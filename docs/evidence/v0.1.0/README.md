# v0.1.0 teaching evidence

**Captured October 9, 2026 from public runs and retained local fixture reports.** These sanitized snapshots preserve the story beyond Actions retention. They are selected records, not raw-log archives or independent attestations.

| Story beat | Preserved record | Original evidence |
|---|---|---|
| Harmless proposal | [Four SAFE results, no evaluator errors, successful file gate](harmless.json) | [Run 37866087551](https://github.com/timothywarner-org/agent-security-quorum/actions/runs/37866087551), commit a524c53 |
| Risky proposal | [Four UNSAFE results and a failed file gate](risky-historical.json) | [Run 35445419741](https://github.com/timothywarner-org/agent-security-quorum/actions/runs/35445419741), commit ee80d84 |
| Operational dependency | [Accepted credential, failing expiry threshold, model checks skipped](maintenance-probe.json) | [Run 37864270825](https://github.com/timothywarner-org/agent-security-quorum/actions/runs/37864270825), commit 22e220d |
| Known detection limits | [Nine individual static fixture observations](static-fixtures.json) | Local static scans on October 8, 2026; Cisco 2.2.1; see [scorecard](../../fixture-scorecard.md) |

Run timestamps are UTC. The harmless run and probe occurred on **October 8 in America/Chicago**; the risky run occurred on September 19. The historical risky workflow predates the current ERROR policy and used older dependencies. Do not describe it as a new evaluation of v0.1.0.

The four-voter snapshots retain requested model/engine labels, verdicts, error flags, finding counts/IDs, job conclusions, source commits, version pins, and SHA-256 hashes of the source result artifacts. They omit finding text, raw prompts, event streams, and diagnostic logs. The probe snapshot contains no token. Model names identify requested configuration, not independently observed backend identity.

Request usage and monetary cost were **not measured**. These runs establish their own behavior, not a detection rate, general security guarantee, or independent service failover. The maintenance record does not prove the credential is valid today.

Use the [Actions walkthrough](../../demo-walkthrough.md) for the presentation route. The [v0.1.0 release](https://github.com/timothywarner-org/agent-security-quorum/releases/tag/v0.1.0) packages these files with source/check provenance and SHA-256 checksums. Verify downloaded assets using the release's SHA256SUMS.txt; GitHub also supplies the tagged source archive.
