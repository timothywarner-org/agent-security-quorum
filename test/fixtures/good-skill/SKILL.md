---
name: lint-check
description: Runs project linting and reports issues. Used after code changes to ensure style compliance.
allowed-tools:
  - shell
  - read
---

# Lint Check Skill

Run the project's configured linter and return results.

## Usage

This skill executes the project's lint command and formats the output for review.

## Constraints

- Only reads files; never modifies them
- Runs only the project's own lint configuration
- Does not install packages or modify dependencies
