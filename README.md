# feihuang-hermes

A shared Hermes skills tap for GPU fleet operations. It contains reusable procedures, troubleshooting guidance, and tools. It does not contain node credentials, live telemetry, or a running model gateway.

## Install on a node

This repository is public, so a GitHub token is not required to read it.

```bash
hermes skills tap add z12957/feihuang-hermes
hermes skills install z12957/feihuang-hermes/vast-gpu-fleet-maintenance
hermes skills list | grep -i vast
```

Use a node's normal Hermes credential store only if that node needs authenticated access to a private repository. Never paste a token into a shell command, chat, script, or repository file.

## Repository contents

| Path | Purpose |
|---|---|
| `skills/vast-gpu-fleet-maintenance/SKILL.md` | Main Vast GPU fleet maintenance skill |
| `skills/vast-gpu-fleet-maintenance/references/maintenance-gate.md` | Tenant notification and verified maintenance sequence before power actions |
| `skills/vast-gpu-fleet-maintenance/references/gpu-fault-playbook.md` | GPU identity, PCIe, ECC, thermal and Xid diagnosis |
| `skills/vast-gpu-fleet-maintenance/references/model-serving-playbook.md` | Multi-node local inference checks, LM Link and gateway routing guidance |
| `skills/vast-gpu-fleet-maintenance/references/fleet-template.md` | Blank local inventory template |
| `schemas/node-inventory.sql` | SQLite schema for node-local hardware and service inventory |
| `skills/vast-gpu-fleet-maintenance/scripts/fleet_health_check.sh` | Read-only health check over configured SSH aliases |
| `SECURITY.md` | Secret handling and public-repository rules |
| `CONTRIBUTING.md` | Shared contribution and local-data policy |

## Shared operations and local facts

Keep common SOPs, generic troubleshooting methods, and reusable skills here. Each node keeps its filled hardware inventory, host identifiers, service URLs, incident records, and credentials in its local SQLite database under `local/`. The schema is shared; the populated database is not. The repository ignores that local directory and SQLite database files.

GitHub distributes reviewed knowledge and configuration templates. It is not the live fleet database or load-balancing state store. A model gateway must use a separate, reachable runtime service for current endpoint health and load.

## Fleet shape

The operator has described three GPU compute machines and Hermes nodes that include a GPU-less LM Link client. This is operator-provided context, not a live inventory verified by this repository. Record actual roles and hardware in each node's local database. Do not put site labels, hostnames, IPs, GPU serials, machine IDs, or service endpoints in this public repository.

## Safety rule

**Processes belong here; identifying or authenticating fleet details stay on the owning node.** See `SECURITY.md` before contributing. Before any reboot, power cycle, BMC reset, or other power action on a Vast machine, follow the maintenance gate and verify that the platform accepted the window.
