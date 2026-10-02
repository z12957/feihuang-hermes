# Fleet inventory — fill in locally; never commit a populated copy

Use `schemas/node-inventory.sql` to create the node-local SQLite database. This page is a checklist for the fields each node owner should verify. Do not add filled values to the shared repository.

## For each machine

- Local node ID and display name
- Role: compute host, Hermes node, or both
- Operating system and version
- GPU count and model for compute hosts; record each GPU's index, PCI bus ID, subsystem ID, VBIOS, driver, memory, and physical location
- SSH alias and LAN address in the local access configuration
- BMC/Redfish URL and access method in the local credential store; never record a password here
- Installed services and versions, including Hermes, LM Link, model server, LiteLLM, and monitoring where present
- Exact model ID, API compatibility, and endpoint URL, held only in the local database/configuration

## Access checks

- Verify SSH key fingerprints before first use.
- Keep private keys in the operating system user's SSH directory.
- Keep Vast API keys and sudo/BMC credentials in an encrypted OS credential store; do not place secrets in the database.
- Verify each API endpoint from the client node that will use it.
- Mark the date each hardware or endpoint fact was last checked.

## Vast account scope

List machine IDs and listing state locally. Note if a machine belongs to another account and cannot be inspected with the current credential. Never guess ownership or credentials.

## Open gaps

Record unknown hardware, service, and connectivity facts as unknown. Do not infer that a service exists because the architecture expects it.
