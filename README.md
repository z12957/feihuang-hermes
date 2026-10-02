# feihuang-hermes

Shared Hermes skills for the multi-node fleet-ops group. This repo is a **Hermes skills tap** — any node can pull it into its own Hermes instance and get a ready-to-use GPU fleet maintenance playbook.

## Adopting this tap (any node)

```bash
# 1. Make sure Hermes reads GITHUB_TOKEN from .env (this node's token, read-only on this repo)
echo 'GITHUB_TOKEN=***' >> ~/.local/share/hermes/.env   # Windows: %LOCALAPPDATA%/hermes/.env

# 2. Register the tap (does NOT fetch yet — just records the source)
hermes skills tap add <owner>/feihuang-hermes

# 3. Verify the tap can see the skill (real fetch path — will 404 if repo is private & token lacks access)
hermes skills list | grep -i vast
```

> `tap add` only writes the source into `skills/.hub/taps.json`; it does **not** validate or clone. The first real proof is a fetch (clone/tarball). If the repo is `private`, the token's account must be a collaborator with Contents:Read, and `/repos/<owner>/<repo>` must return `200` before any skill install will work.

## What's in this repo

| Path | What it is |
|---|---|
| `SKILL.md` (root) | The generic **Vast GPU Fleet Maintenance** skill — processes, rules, CLI patterns. No node-specific data. |
| `references/fleet-template.md` | Fill-in template for **your** fleet inventory (machine IDs, hosts, GPUs, BMCs). Keep this filled copy local; commit only the empty template. |
| `references/maintenance-gate.md` | The maintenance-window gate, step by step + the Vast CLI JSON/exit-code traps. |
| `references/gpu-fault-playbook.md` | Single-GPU fault identification checklist (identity → location → fault mode → incident note). |
| `scripts/fleet_health_check.sh` | Portable read-only health loop across SSH aliases. |
| `SECURITY.md` | **What must never be committed** and why — read this before adding anything. |

## Hard rule (applies to every node)

**Credentials never leave the node.** Vast API keys, BMC passwords, SSH private keys, and hostnames/IPs of your own fleet stay on the node that owns them (DPAPI/keystore/owner-provided). This repo contains **processes, not secrets** — a working skill should require you to supply your own local values at runtime. If a value in a file here looks like a real credential or a real IP/hostname of a specific fleet, treat it as a leak and remove it.
