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

Hermes skills are procedural memory. Turn successful, reusable operating lessons into shared candidates so other nodes can benefit.

## When to publish automatically

After `skill_manage` creates or changes a local skill, prepare a draft PR when at least one is true:

- The solution is not already documented and is likely to recur.
- A failed approach exposed a reliable pitfall or diagnostic signal.
- The operator corrected or clarified the procedure.
- The change materially improves the time or reliability of a recurring workflow.

Do not publish transient machine state, one-off incident logs, speculative fixes, or content that identifies a site, machine, account, tenant, endpoint, or credential. If a fact cannot be safely generalized or verified, keep it local and explain the gap.

## Prepare the candidate

1. Read the changed skill and relevant shared references; compare the full diff with current `main`.
2. Distill the lesson into an imperative rule and its reason. Remove transcripts, logs, host details, exact model endpoints, PCI addresses, tenant data, live measurements, credentials, and machine-specific paths.
3. If the lesson passes those checks, run the publisher without waiting for a separate user prompt. It creates a draft PR; a curator still reviews and merges it.
4. If the publisher or scanner is unavailable, leave the lesson local and report why.

```bash
python3 ~/feihuang-hermes/scripts/shared_skills.py publish \
  --repo ~/feihuang-hermes \
  --hermes-home ~/.hermes \
  --skill <skill-name> \
  --node-slug <generic-node-label>
```

Use a generic public contributor label such as `node-a`, never a site or machine name. The publisher uses a temporary worktree on current `main`, scans staged changes with Gitleaks, and opens a PR branch. It never writes to `main`. Inspect the complete PR diff after creation.

See `skills/vast-gpu-fleet-maintenance/references/shared-learning-workflow.md` for sync and conflict behavior.

## Keep node data local

Hardware inventory, exact model identifiers and endpoints, GPU telemetry, queue state, and incident records belong in that node's local database. Contribute only reusable schemas and diagnostic methods to the shared repository.
