# Security / secret-handling policy

This repo is **public** (or shared) by design. The rule that keeps it safe:

> **Processes, not secrets.** Commit *how* to do the work. Never commit *what uniquely identifies* your fleet or *what authenticates* to it.

## Never commit (keep on the owning node only)

| Category | Examples | Where it should live |
|---|---|---|
| **API keys / tokens** | Vast API key, any GitHub token, cloud keys | DPAPI blob / OS keychain / env var at runtime. Never in a file, log, chat, or this repo. |
| **SSH keys** | private key `id_ed25519_*`, passphrases | Owner's `~/.ssh`, transferred only over an encrypted channel. Fingerprint may be shared *if* you choose to, but prefer not. |
| **BMC / IPMI credentials** | user + password | Owner-provided on demand. Never in a file. |
| **Fleet identifiers** | Vast machine IDs, hostnames, LAN IPs, BMC IPs, PCI bus addresses of *your* cards, tenant/instance IDs | `references/fleet-template.md` **on your node** (a filled copy). The committed template stays empty. |
| **Incident specifics** | your card's subsystem/VBIOS + replay counts tied to a machine ID, your SSD model/fw, crontab changes, your tenant case numbers | Your local notes / incident report files. |
| **Local machine facts** | your Windows/Linux box hostname, your user, your internal paths (`%USERPROFILE%`, absolute `/root/...`) | Local skill copies only. |

## Safe to commit

- The **maintenance gate** and every **Vast CLI** command pattern (`schedule maint`, `show machine --raw`, JSON parsing, exit-code caveat).
- **Read-only** health-check and fault-isolation **commands** and **checklists** (these are generic Linux/nvidia-smi/BMC methods).
- **Methodology** (identify a card before acting, write a dated incident note, handoff over an encrypted channel).
- **Generic** helper scripts that take host lists / keys as **runtime arguments** and never hard-code one.

## The one-line test

Before committing a line, ask: *"Would this let someone identify, reach, or authenticate to one specific person's machine or account?"*
- Yes → **remove it**, reference a placeholder instead.
- No (it's a method anyone could apply to any fleet) → fine to commit.

## If you find a real secret here

1. Stop, don't echo it anywhere (chat/logs).
2. `git rm --cached` it, and rotate the credential.
3. Check `git log` — if it was ever committed, the credential must be **revoked and reissued**, because git history is durable.
