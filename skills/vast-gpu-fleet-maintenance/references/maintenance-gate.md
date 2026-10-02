# The maintenance gate (step by step)

**Rule:** before ANY reboot / power-cycle / BMC reset / power-off-on on a Vast machine, the gate is
fully satisfied. `listed=false`, no tenants, or a delisting do **not** count as granted.

## Sequence

1. **Decide + state impact.** Name the machine, the action, and the tenant impact. Get explicit
   per-incident authorization if the gate would otherwise be bypassed.
2. **Schedule** (this is the tenant-notification mechanism for planned-out maintenance):
   ```bash
   vastai schedule maint <machine_id> --sdate <UTC_epoch_seconds> --duration <hours> \
          --maintenance_category <power|internet|disk|gpu|software|other>
   ```
   - `--sdate` = **UTC epoch seconds**. `--duration` = **hours** (decimals OK).
   - Subcommand is `schedule maint` (`schedule maintenance` → "invalid choice").
   - Interactive `Continue? [y/n]`: pipe `printf 'y\n' |` to automate. No `--yes` flag.
3. **Verify acceptance** (this is the real signal, not the exit code):
   ```bash
   vastai show machine <machine_id> --raw
   ```
   The `machine_maintenance` field must be **non-null and match** your schedule. `null` = not accepted yet.
4. **Wait** until the window actually begins.
5. **Recheck before acting:** host state + active instances (who's running on it).
6. **Act.** Then re-verify (GPU count, services `vastai`/`docker`/`containerd` active).

## Traps that look like success but aren't

- **CLI exit code is unreliable** — a failed API call can still `exit 0`. Parse the JSON
  `error` / `status_code` every time.
- **`401` on `show maints`** = this key lacks the `api.machines.maintenances` *read* route. That does
  **not** mean `schedule maint` (a different route) will fail — actually try it and re-read
  `machine_maintenance`.
- **Bare `show maints`** (no `--ids`) crashes with `AttributeError` in some CLI versions — always pass
  `--ids <machine_id>[,...]`.
- **Cancel:** `vastai cancel maint <machine_id>`.

## What "granted" does NOT mean

- A delisted / `listed=false` machine, or one with zero tenants, has **no** maintenance window. You
  still need a scheduled + accepted window before a power action.
- A window that began is not a free pass — you still recheck active instances right before the action.
