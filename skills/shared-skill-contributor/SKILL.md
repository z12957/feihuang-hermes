---
name: shared-skill-contributor
description: Use after a reusable operational lesson, reliable fix, or user correction changes a local Hermes skill; prepare a safe GitHub draft PR for curator review.
version: 1.0.0
author: feihuang-shared
license: MIT
metadata:
  hermes:
    tags: [skills, github, fleet-ops, knowledge-sharing]
---

# Shared skill contributor

When a task produces a reliable procedure that should benefit other nodes, distill the reusable method into the relevant local skill. Do not copy chat transcripts, logs, credentials, host details, exact endpoints, tenant data, or live hardware measurements.

## Before publishing

1. Read the relevant skill and shared reference files first.
2. Keep the rule actionable: state what to do and why, and include a verification step.
3. Compare the local skill with the current shared repository version. Avoid duplicating existing guidance.
4. Review every changed file for site identifiers, hostnames, IPs, PCI addresses, tokens, passwords, environment files, and local paths.
5. Ask the operator to review the candidate when facts are uncertain or the change affects maintenance or recovery behavior.

## Open a candidate PR

Follow `skills/vast-gpu-fleet-maintenance/references/shared-learning-workflow.md`. It creates an isolated branch and a draft PR from current `main`; it never writes to `main`. Supply a generic contributor label, not a site or machine name. Confirm that Gitleaks passes, then inspect the complete PR diff before handing it to the curator.

## Keep node data local

Hardware inventory, exact model identifiers and endpoints, GPU telemetry, queue state, and incident records belong in that node's local database. Contribute only reusable schemas and diagnostic methods to the shared repository.
