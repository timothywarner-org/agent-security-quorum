---
name: deploy-helper
description: Checks deployment readiness by verifying build status and test results before proceeding.
allowed-tools:
  - read
---

# Deploy Helper

Verify that the project is ready for deployment.

## Process

1. Check that all CI checks have passed
2. Verify the build artifact exists
3. Confirm version numbers are updated

## Constraints

- Read-only — never triggers a deployment directly
- Only checks status; does not modify configuration
- Reports findings back to the user for manual approval
