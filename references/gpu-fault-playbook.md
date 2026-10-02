# Single-GPU fault isolation playbook

A card is **not** a slot — identity follows the card. Before you act on a bad GPU (or hand it to a
technician), establish these four things **in order** and write a dated note.

## 1. Card identity

- `lspci -nn -v -s <bus>` → **Subsystem ID**.
- `nvidia-smi -q -i <n>` → Product Name, VBIOS, power limits.
- Cross-check **Subsystem ID + VBIOS** on TechPowerUp vgabios to name the exact model.
- Distinguish same-vendor cards by **Subsystem ID, not VBIOS** — different models of the same vendor
  can share an identical VBIOS string.

## 2. Physical location (record as "as of <date>"; re-verify after any repair)

- PCI bus: `nvidia-smi -q -i <n> | grep 'Bus Id'`
- Parent host bridge: `lspci -tv`
- Board: `dmidecode -s baseboard-product-name`
- Report **bus + bridge**. The OS cannot map a bus to a silkscreen label, so a technician needs both.

## 3. Fault-mode evidence (pinpoint link vs VRAM vs thermal)

| Signal | How to read it | What it suggests |
|---|---|---|
| **PCIe replays** | sample `Replays Since Reset` twice ~60s apart for a rate | link/connector/riser |
| **Link speed downgrade** | `lspci -vv -s <bus>` → `LnkCap` vs `LnkSta` | a Gen4 link negotiated down (e.g. to Gen1/x8) is a strong link signal |
| **AER errors** | `/sys/bus/pci/devices/0000:<bus>/aer_dev_*` | PCIe transport |
| **Xid** | `sudo journalctl -k --grep Xid` | GPU/driver class (92 = ECC, 48 = fallen off bus, etc.) |
| **VRAM** | `nvidia-smi -q` ECC + remapped-row counters | VRAM |
| **Thermal** | `nvidia-smi -q` temps, throttle reasons | thermal |

> `Replays Since Reset` is **not** a valid `nvidia-smi --query-gpu` field — read it from the full
> `nvidia-smi -q -i <n>` output (grep `Replays Since Reset`).

**Reseating is not proof of cure.** If the replay counter is still climbing after a reseat (even after a
reset to 0), the fault persists — isolate further (single-variable tests: disk-only vs GPU
pinned-memory load), don't declare it fixed.

## 4. Dated incident note

Record: date, machine (your local ID), card identity (subsystem/VBIOS/model), bus + bridge,
fault-mode evidence with numbers, action taken (or "report only"), and a re-verify date. Keep this
note **local** (it references your fleet). What's safe to share is the *method*, not the *numbers*.

## What "missing GPU" means

Report **only**: the count from `nvidia-smi -L` and the PCI bus. **Never** auto-reset, reload drivers,
or reboot a machine because a card is missing — that's a power action and needs the full maintenance
gate (see `maintenance-gate.md`), and the root cause may be a host-level issue you'd destroy evidence of.
