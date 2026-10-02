---
name: vast-gpu-fleet-maintenance
description: Generic playbook for maintaining and recovering a Vast.ai GPU fleet — maintenance gate, health checks, single-GPU fault isolation, and node handoff. Processes only; no node-specific IPs/IDs/credentials.
version: 1.0.0
author: feihuang-shared
license: MIT
metadata:
  hermes:
    tags: [vast-ai, gpu, bmc, redfish, ssh, fleet-ops]
    related_skills: [systematic-debugging, spike]
---

# Vast GPU Fleet Maintenance (shared playbook)

A node-agnostic playbook for operating a Vast.ai GPU fleet over LAN SSH + BMC/Redfish.
**This skill contains processes and commands — not secrets.** You supply your own machine
IDs, hostnames, IPs, SSH aliases, and credentials at runtime (see `references/fleet-template.md`
for the local inventory to keep, and `SECURITY.md` for what must never be committed here).

## When to use

- Monitoring / health-checking / diagnosing your LAN GPU hosts or their Vast machine records.
- Scheduling maintenance, rebooting, power-cycling, or resetting a Vast machine (**gate applies**).
- Fault isolation on a single GPU (Xid, PCIe replays, ECC, AER) or a reported missing card.
- BMC/Redfish sensor reads, or planning a handoff to another admin machine.

Do **not** use for other people's Vast accounts, generic Linux admin unrelated to a GPU fleet, or
hosts that are not in your inventory.

## Hard rules (never violate)

1. **Maintenance gate** — before ANY reboot / power-cycle / BMC reset / power-off-on on a Vast machine:
   (a) `schedule maint <machine_id> --sdate <UTC epoch> --duration <h>` via Vast CLI;
   (b) confirm `show machine <id> --raw` returns an accepted `machine_maintenance` window (non-null,
       matching your schedule);
   (c) wait until the window actually begins;
   (d) recheck host state + active instances, then act.
2. **No bypass** without explicit per-incident user authorization, and state expected tenant impact first.
3. `listed=false`, no tenants, or a platform delisting does **not** count as maintenance granted.
4. **Missing GPU = report only** (count + PCI bus). Never auto-reset, reload drivers, or reboot on that basis.
5. **Credentials are owner-provided / keychain-only.** Never write sudo/BMC passwords or API keys to
   files, logs, chat, or this repo. Never guess BMC IPs, accounts, or passwords.
6. **Don't copy one host's BMC config/creds to another machine's BMC.**

## Local access (fill in on your node — do NOT commit these values here)

Keep these in `references/fleet-template.md` **on the node that owns the fleet**:

- One SSH key per fleet (public-key auth only); verify the fingerprint before first use.
- `~/.ssh/config` aliases per host (IdentityFile + IdentitiesOnly).
- Vast CLI: run with a wrapper that decrypts your API key **in memory** and calls `vastai.exe`.
  If the stock wrapper's hard-coded CLI path doesn't exist in your shell, run the same decode logic
  against the CLI path that *does* exist. Never print the key.
- **Root on remote hosts:** a `Invoke-HostSudo`-style helper that passes one quoted command and a
  shared sudo password that lives **encrypted** (DPAPI/keystore) and is user+machine-bound (won't decrypt elsewhere).

> **Shell-visibility quirk:** a path that looks absent from one shell (e.g. a POSIX/bash view) may be
> present from another (e.g. `pwsh`). If a path check fails from one shell, re-test from the other
> before concluding it is broken. Don't "fix" paths based on a single shell's view.

## Vast CLI — maintenance (JSON parsing + exit-code traps)

```bash
# Schedule maintenance (notifies tenants to back up). Subcommand is `schedule maint` —
# `schedule maintenance` returns "invalid choice".
vastai schedule maint <machine_id> --sdate <UTC_epoch_seconds> --duration <hours> \
       --maintenance_category <power|internet|disk|gpu|software|other>

# Cancel a scheduled maintenance
vastai cancel maint <machine_id>

# List scheduled maintenance — `--ids` is REQUIRED. A bare `show maints` in some CLI versions
# crashes with AttributeError (empty ids).
vastai show maints --ids <machine_id>[,<id>...] --raw

# Confirm the platform ACCEPTED it: the `machine_maintenance` field in the machine record must be
# non-null and match your schedule. null = no accepted window yet.
vastai show machine <machine_id> --raw
```

Gotchas that will bite you:

- `--sdate` is **UTC epoch seconds**, not local time; `--duration` is **hours** (decimals OK, e.g. `0.5`).
- **CLI exit code is not trustworthy** — even when the API returns an error the CLI can still `exit 0`.
  Always parse the output JSON's `error` / `status_code`.
- A `401` on `show maints` (key missing the `api.machines.maintenances` route) does **not** mean you
  can't `schedule maint` — those are separate routes. Verify by actually scheduling and re-reading
  `machine_maintenance`.
- `schedule maint` has an interactive `Continue? [y/n]`; to automate, pipe `printf 'y\n' |`. There is
  no `--yes` flag. The platform may shift `start_time` to now.
- **Acceptance signal = `machine_maintenance` non-null and matching** (not the exit code, not `show maints`).

## Read-only health check (run first, any time — safe, no creds needed)

```bash
# Loop your host aliases (replace with YOUR aliases):
for h in host-a host-b host-c; do
  echo "== $h =="
  ssh -o ConnectTimeout=10 "$h" \
    "hostname; uptime -p; nvidia-smi -L; systemctl is-active vastai docker containerd"
done
```

Deeper, per host (kernel log / grep need root):

```bash
nvidia-smi --query-gpu=index,pci.bus_id,name,power.limit,pstate,temperature.gpu,utilization.gpu,utilization.memory --format=csv,noheader
sudo journalctl -k -b -p warning..alert --no-pager -n 100
sudo journalctl -b --no-pager | grep -Ei 'NVRM|Xid|AER|oom|out of memory|pcie|I/O error|fatal' | tail -n 100
```

- **BMC reach check (no creds):** `curl -sk https://<bmc>/redfish/v1/` → `200` = up; `/Systems` `401` = up + auth required.
- **SSH-only loss ≠ host failure:** before rebooting, check ICMP, sshd logs, `MaxStartups`, firewall,
  Vast forwarded ports, and BMC sensor/SEL.

## Single-GPU fault identification (mandatory checklist)

A card is not a slot — identity follows the card. Establish, in order:

1. **Card identity:** `lspci -nn -v -s <bus>` (Subsystem ID) + `nvidia-smi -q -i <n>`
   (Product Name, VBIOS, power limits). Cross-check Subsystem ID + VBIOS on TechPowerUp vgabios to
   name the exact model. Distinguish same-vendor cards by **Subsystem ID, not VBIOS** — different models
   can share the same VBIOS string.
2. **Physical location (as-of; re-verify after any repair):** PCI bus via
   `nvidia-smi -q -i <n> | grep 'Bus Id'`; parent host bridge from `lspci -tv`; board via
   `dmidecode -s baseboard-product-name`. Report bus + bridge — the OS cannot map to silkscreen labels.
3. **Fault-mode evidence (link vs VRAM vs thermal):**
   - sample `Replays Since Reset` twice ~60s apart for a rate (read from full `nvidia-smi -q -i <n>` —
     it is **not** a valid `--query-gpu` field);
   - `lspci -vv -s <bus>` → LnkCap vs LnkSta (a Gen4 link negotiated down to Gen1/x8 is a signal);
   - AER counters under `/sys/bus/pci/devices/0000:<bus>/aer_dev_*`;
   - Xid via `sudo journalctl -k --grep Xid`;
   - temps / ECC / remapped rows from `nvidia-smi -q`.
4. **Write a dated incident note** with the slot location marked "as of" that date.

## Node handoff (to a new admin machine)

1. Transfer the SSH key over an **encrypted channel** (never chat / plain files); verify the
   fingerprint with `ssh-keygen -lf` before first use; don't blindly accept first-run host-key prompts.
2. Reconfigure the Vast API key for that machine (a DPAPI/keystore blob is **user+machine-bound** and
   will not decrypt elsewhere — recreate it from the plaintext via an encrypted channel).
3. Reinstall this skill + any helper scripts and fix their hardcoded paths for the new machine.
4. Re-verify per host: `nvidia-smi -L` count matches **your** inventory.

## Contributing / improving this skill (per node)

When you learn a new pitfall or a process change on your node:

1. Update **your local** copy of this skill first (so you have a working version).
2. Generalize it: strip machine IDs, IPs, hostnames, credentials, and incident specifics (see `SECURITY.md`).
3. Commit the **generic** version back here:

```bash
cd <your clone of this repo>
# edit SKILL.md / references/ / scripts/
git add -A && git commit -m "skills: <what changed, generically>"
git push origin main   # needs a token with Contents:Write (fine-grained) on this repo
```

Keep the shared copy process-only. Keep the filled-in fleet inventory and all secrets on the node that owns them.
