---
name: lint-check
description: Runs the project linter and reports style issues. Used after code changes to ensure consistency.
allowed-tools:
  - shell
  - read
---

# Lint Check

Run the project's configured linter and return results.

## Usage

Execute the lint command defined in the project's package.json or Makefile and format the output.

## Constraints

- Only reads files and runs the lint command; never modifies source code
- Runs only the project's own lint configuration
- Does not install packages or modify dependencies
