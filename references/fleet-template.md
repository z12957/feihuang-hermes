# Fleet inventory — FILL THIS IN ON YOUR NODE (do NOT commit the filled copy)

This is the **template**. Keep a *filled* copy locally (e.g. in your local skill dir or your notes).
Only this empty template is safe to commit. Every `{{...}}` is a value **you** supply at runtime.

## Machines

| Vast machine ID | Host / board | GPU (count × model) | SSH alias | LAN SSH IP | BMC URL | Power limit |
|---|---|---|---|---|---|---|
| `{{machine_id}}` | `{{board_model}}` | `{{N}}× {{gpu_model}}` | `{{ssh_alias}}` | `{{10.x.y.z}}` | `https://{{bmc_ip}}` | `{{150}}W` |
| `{{machine_id}}` | `{{board_model}}` | `{{N}}× {{gpu_model}}` | `{{ssh_alias}}` | `{{10.x.y.z}}` | `https://{{bmc_ip}}` | `{{200}}W` |

## Access (your node)

- SSH key path: `{{~/.ssh/id_ed25519_<fleet>}}` — fingerprint: `{{...}}` (verify before first use)
- `~/.ssh/config` aliases: `{{alias_a}}`, `{{alias_b}}`, `{{alias_c}}`
- Vast CLI: `{{/path/to/vastai}}` (wrapper decrypts the API key in memory; never print it)
- Root-on-remote helper: `{{/path/to/Invoke-HostSudo-style-helper}}` (shared sudo password lives **encrypted**, owner-provided)

## Vast account scope (this API key)

List the machine IDs under **your** API key, and which are `listed=True`. Note any machine that is
**not** under this key (belongs to another account — you'd need that account's key to monitor it).

## BMC

Per host: BMC base URL, Redfish version, auth method (basic/none). **Passwords: never write them
here or anywhere in a file** — owner-provided on demand. Do not copy one host's BMC config to another.

## Open gaps (owner to fill; never guess)

- `{{...}}`
