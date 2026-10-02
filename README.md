# feihuang-hermes

A shared Hermes skills tap for GPU fleet operations. It contains reusable procedures, troubleshooting guidance, and tools. It does not contain node credentials, live telemetry, or a running model gateway.

## Install and synchronize

This repository is public, so fetching approved skills requires no GitHub token. Use a dedicated clone for the Git-based publisher and periodic updater:

```bash
git clone https://github.com/z12957/feihuang-hermes.git ~/feihuang-hermes
python3 ~/feihuang-hermes/scripts/shared_skills.py sync \
  --repo ~/feihuang-hermes --hermes-home ~/.hermes
```

The first run installs shared skills in `~/.hermes/skills` and records local baselines under the ignored `local/` directory. On Linux, enable the supplied 15-minute user timer from `deploy/systemd/`; see the shared learning workflow for setup and conflict behavior.

Publishing requires `git`, GitHub CLI (`gh`) authenticated for this repository, and Gitleaks. After reviewing a local skill change, run the publisher to create an isolated branch and draft PR. Nodes never push skill changes to `main` directly.

## Repository contents

| Path | Purpose |
|---|---|
| `skills/vast-gpu-fleet-maintenance/SKILL.md` | Main Vast GPU fleet maintenance skill |
| `skills/vast-gpu-fleet-maintenance/references/maintenance-gate.md` | Tenant notification and verified maintenance sequence before power actions |
| `skills/vast-gpu-fleet-maintenance/references/gpu-fault-playbook.md` | GPU identity, PCIe, ECC, thermal and Xid diagnosis |
| `skills/vast-gpu-fleet-maintenance/references/model-serving-playbook.md` | Multi-node inference checks, LM Link and gateway routing guidance |
| `skills/vast-gpu-fleet-maintenance/references/shared-learning-workflow.md` | Skill proposal, review, conflict and periodic sync process |
| `skills/shared-skill-contributor/SKILL.md` | Hermes guidance for turning reusable lessons into PR candidates |
| `scripts/shared_skills.py` | Safe pull/update and Gitleaks-scanned draft PR publisher |
| `deploy/systemd/` | Optional periodic sync timer for Linux Hermes nodes |
| `schemas/node-inventory.sql` | SQLite schema for node-local hardware and service inventory |
| `SECURITY.md` | Secret handling and public-repository rules |
| `CONTRIBUTING.md` | Shared contribution and local-data policy |

## Shared operations and local facts

Keep common SOPs, generic troubleshooting methods, and reusable skills here. Each node keeps its filled hardware inventory, host identifiers, service URLs, incident records, and credentials in its local SQLite database under `local/`. The schema is shared; the populated database is not.

GitHub distributes reviewed knowledge. It is not the live fleet database or load-balancing state store. A model gateway uses a separate runtime service for current endpoint health and load.

## Fleet shape

The operator has described three GPU compute machines and Hermes nodes that include a GPU-less LM Link client. This is operator-provided context, not a live inventory verified by this repository. Record actual roles and hardware in each node's local database. Do not put site labels, hostnames, IPs, GPU serials, machine IDs, or service endpoints in this public repository.

## Safety rule

**Processes belong here; identifying or authenticating fleet details stay on the owning node.** See `SECURITY.md` before contributing. Before any reboot, power cycle, BMC reset, or other power action on a Vast machine, follow the maintenance gate and verify that the platform accepted the window.
