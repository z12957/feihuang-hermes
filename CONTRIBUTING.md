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

## Structure

```
skills/<skill-name>/
├── SKILL.md
├── references/
└── scripts/
schemas/                       # shared schema only; no populated inventory
README.md
SECURITY.md
CONTRIBUTING.md
```

Keep one main task per skill. Put detailed procedures in references and link them from the skill.

## Contributing changes

1. Add the reusable method to your local copy and make sure it solves the operational problem.
2. Remove host-specific values, secrets, tenant details, and incident measurements.
3. Review the diff for credentials, IPs, machine names, and local filesystem paths.
4. Submit the generalized change through the repository's normal Git workflow.

Never use a token pasted into chat or a command line. Use the node's approved credential store for Git operations. Do not commit a populated local inventory or database.

## Local data

Initialize a local inventory database from `schemas/node-inventory.sql`, for example:

```bash
mkdir -p local
sqlite3 local/fleet.db < schemas/node-inventory.sql
```

Each node records its own hardware and services. Share only schema or reusable procedures. Do not synchronize populated inventories through GitHub; they contain fleet-specific operational details.

Before any Vast machine reboot, power cycle, BMC reset, or power-off/on, follow the maintenance gate in the skill and verify platform acceptance. A missing GPU is a report-only condition until that gate has been satisfied.
