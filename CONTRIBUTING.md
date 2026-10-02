# Contributing — shared operations knowledge

This public repository is the shared Hermes skills tap for a multi-node GPU fleet. Its purpose is to distribute general procedures and skills. The operator currently describes three GPU compute machines and Hermes nodes that include a GPU-less LM Link client; this topology is not a remotely verified inventory.

## What belongs here

| Commit to this repository | Keep in the node-local database |
|---|---|
| Generic maintenance and fault-isolation procedures | Site labels, machine IDs, hostnames, SSH aliases, IPs and BMC URLs |
| Empty inventory templates and database schema | GPU serials, exact slot maps and host-specific PCI addresses |
| Read-only scripts that accept runtime host aliases | Model-server endpoints, active model configuration and local service names |
| Generalized lessons from incidents | Incident records, tenant details, credentials and node-specific measurements |
| Model routing and health-check guidance | Live load, request counts, GPU utilization and queue state |

Before committing, ask whether an unfamiliar reader could use the change to identify, reach, or authenticate to a particular machine or account. If yes, keep it local and generalize the method.

## Learning loop

1. A Hermes node improves a local skill after a reliable solution, repeated pitfall, or user correction.
2. The node owner reviews the local skill diff and removes secrets, host details, logs, and incident-specific measurements.
3. `scripts/shared_skills.py publish` copies the selected skill into a temporary worktree based on current `main`, scans the staged files with Gitleaks, and opens a draft PR on a per-contributor branch.
4. A curator checks correctness, overlap, conflicts, and privacy before merging to `main`.
5. Each node's timer polls `main`. It updates clean installed copies, preserves local edits, and reports conflicts without overwriting them.

The publisher must never push directly to `main`; generated PRs must not auto-merge.

## Structure

```
skills/<skill-name>/
├── SKILL.md
├── references/
└── scripts/
schemas/                       # shared schema only; no populated inventory
scripts/                       # publishing and sync utilities
deploy/systemd/                # optional Linux polling timer
README.md
SECURITY.md
CONTRIBUTING.md
```

Keep one main task per skill. Put detailed procedures in references and link them from the skill.

## Local inventory

Initialize a node-local SQLite database from `schemas/node-inventory.sql`:

```bash
mkdir -p local
sqlite3 local/fleet.db < schemas/node-inventory.sql
```

Each node records its own hardware and services. Share only schema or reusable procedures. Do not synchronize populated inventories through GitHub; they contain fleet-specific operational details.

## Safety

Never use a token pasted into chat or a command line. Use the node's approved credential store for Git operations. Do not commit a populated local inventory or database. A missing GPU is report-only until the maintenance gate is satisfied; any Vast machine power action requires a scheduled and accepted maintenance window.
