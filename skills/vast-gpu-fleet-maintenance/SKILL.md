---
name: vast-gpu-fleet-maintenance
description: Generic playbook for maintaining and recovering a Vast.ai GPU fleet — maintenance gate, health checks, single-GPU fault isolation, and node handoff. Processes only; no node-specific IPs/IDs/credentials.
version: 1.1.0
author: feihuang-shared
license: MIT
metadata:
  hermes:
    tags: [vast-ai, gpu, bmc, redfish, ssh, fleet-ops, local-inference, lm-link]
    related_skills: [systematic-debugging, spike]
---

# Vast GPU Fleet Maintenance (shared playbook)

A node-agnostic playbook for operating a GPU fleet over LAN SSH and BMC/Redfish. It covers Vast maintenance, hardware fault isolation, and local model-service checks. **This skill contains processes and commands — not secrets.** Supply machine IDs, hostnames, IPs, SSH aliases, model endpoints, and credentials locally. Keep the filled inventory in a node-local database; see `references/fleet-template.md` and `schemas/node-inventory.sql`. See `SECURITY.md` for repository rules.

## When to use

- Monitoring or diagnosing GPU hosts and their Vast machine records.
- Scheduling maintenance, rebooting, power-cycling, or resetting a Vast machine (**gate applies**).
- Isolating a single-GPU fault (Xid, PCIe replays, ECC, AER) or a missing card.
- Checking BMC/Redfish sensors or handing the fleet to another admin machine.
- Diagnosing a local model endpoint, LM Link path, or multi-node gateway routing. See `references/model-serving-playbook.md`.

Do not use for other people's Vast accounts, generic Linux administration unrelated to an inventoried fleet, or hosts outside the local inventory.

## Hard rules (never violate)

1. **Maintenance gate** — before ANY reboot, power cycle, BMC reset, or power-off/on on a Vast machine:
   (a) `schedule maint <machine_id> --sdate <UTC epoch> --duration <h>` via Vast CLI;
   (b) confirm `show machine <id> --raw` returns an accepted, matching `machine_maintenance` window;
   (c) wait until the window begins;
   (d) recheck host state and active instances, then act.
2. **No bypass** without explicit per-incident user authorization, and state expected tenant impact first.
3. `listed=false`, no tenants, or a platform delisting does **not** count as maintenance granted.
4. **Missing GPU = report only** (count and PCI bus). Never auto-reset, reload drivers, or reboot on that basis.
5. **Credentials are owner-provided / keychain-only.** Never write sudo/BMC passwords, API keys, or access tokens to files, logs, chat, or this repository. Never guess BMC IPs, accounts, or passwords.
6. **Don't copy one host's BMC configuration or credentials to another host.**
7. **Routing is not recovery.** A gateway may stop sending new requests to an unhealthy endpoint; it must not trigger host reboot, driver reload, or power action automatically.

## Local access (fill in on your node — do NOT commit these values)

Keep machine-specific inventory in the local database initialized from `schemas/node-inventory.sql`. Keep SSH keys in the OS user's SSH directory and credentials in the approved encrypted store.

- Use one SSH key per fleet and verify its fingerprint before first use.
- Configure local SSH aliases with public-key authentication.
- Run Vast CLI through a local wrapper that reads its credential in memory; never print the key.
- Use a local helper for remote root commands; keep its password encrypted and user/machine bound.
- Record GPU compute machines separately from Hermes nodes. A Hermes node with no GPU may call a remote model service through LM Link.
- Confirm every API route and model name from the installed service before adding it to a local inventory; the shared playbook does not imply that LiteLLM, LM Link, or a model server is installed.

> **Shell-visibility quirk:** a path that looks absent from one shell may be present from another. Re-test in the shell that owns the executable before concluding it is broken.

## Vast CLI — maintenance

```bash
vastai schedule maint <machine_id> --sdate <UTC_epoch_seconds> --duration <hours> \
       --maintenance_category <power|internet|disk|gpu|software|other>
vastai cancel maint <machine_id>
vastai show maints --ids <machine_id>[,<id>...] --raw
vastai show machine <machine_id> --raw
```

- `--sdate` is UTC epoch seconds; `--duration` is hours.
- The subcommand is `schedule maint`; `schedule maintenance` returns “invalid choice”.
- The CLI exit code is not trustworthy. Parse JSON `error` and `status_code`.
- A `401` on `show maints` may mean the key lacks the read route; it does not prove scheduling failed. Verify the `machine_maintenance` field on the machine record.
- Some CLI versions require `--ids` on `show maints`.
- Scheduling may prompt for confirmation and the platform may shift the start time. Verify the accepted window instead of trusting the prompt or exit code.

## Read-only health check

Run the fleet script with local SSH aliases, or use:

```bash
for h in host-a host-b host-c; do
  echo "== $h =="
  ssh -o ConnectTimeout=10 "$h" \
    "hostname; uptime -p; nvidia-smi -L; systemctl is-active vastai docker containerd"
done
```

For deeper diagnosis (kernel log access may require root):

```bash
nvidia-smi --query-gpu=index,pci.bus_id,name,power.limit,pstate,temperature.gpu,utilization.gpu,utilization.memory --format=csv,noheader
sudo journalctl -k -b -p warning..alert --no-pager -n 100
sudo journalctl -b --no-pager | grep -Ei 'NVRM|Xid|AER|oom|out of memory|pcie|I/O error|fatal' | tail -n 100
```

- **BMC reach check:** `curl -sk https://<bmc>/redfish/v1/`; HTTP 200 means reachable, and 401 from an authenticated resource can mean reachable but authentication is required.
- **SSH-only loss is not proof of host failure.** Check network reachability, sshd logs, `MaxStartups`, firewall, forwarded ports, and BMC sensors/SEL before proposing power action.

## Single-GPU fault identification

A card is not a slot — identity follows the card. Establish, in order:

1. **Card identity:** `lspci -nn -v -s <bus>` (Subsystem ID) plus `nvidia-smi -q -i <n>` (product, VBIOS, power limits). Use Subsystem ID and VBIOS together; different models may share a VBIOS string.
2. **Physical location:** record PCI bus, parent bridge from `lspci -tv`, and board from `dmidecode -s baseboard-product-name`. Mark it “as of” a date and recheck after repairs. The OS may not map the bus to a silkscreen label.
3. **Fault evidence:** sample PCIe replay count twice about 60 seconds apart; compare `LnkCap` and `LnkSta` from `lspci -vv`; check AER counters, Xid, ECC/remapped rows, temperatures, and throttle reasons. Replay count is read from full `nvidia-smi -q`, not a `--query-gpu` field.
4. **Isolate one variable at a time.** A reseat is not proof of cure. If replay counts continue to rise after reseating, keep the fault open and compare controlled workloads (for example, storage-only and GPU pinned-memory tests).
5. **Write a dated, local incident note** with the evidence, action, and recheck date.

See `references/gpu-fault-playbook.md` for the detailed checklist and `references/maintenance-gate.md` before any power action.

## Node handoff

1. Transfer SSH keys only through an encrypted channel and verify the fingerprint with `ssh-keygen -lf`.
2. Recreate machine-bound credentials on the receiving host; encrypted blobs may not decrypt elsewhere.
3. Install the skill and local helper scripts; configure local paths for that host.
4. Recheck GPU count against the local inventory and confirm each service endpoint.

## Contributing a lesson

Update the local skill first, remove identifiers and incident-specific values, then contribute only the general method. Keep populated inventories and incident notes local. See `CONTRIBUTING.md` and `SECURITY.md`.
