# Multi-node local inference operations

This playbook covers checks for a fleet where several GPU machines serve the same local model and one or more Hermes nodes send requests through LM Link or a model gateway. The described fleet shape is three GPU compute machines and a GPU-less Hermes client, based on operator-provided context. It has not been remotely inspected; record actual node names, services, endpoints, and model IDs only in the local inventory.

## Separate the roles

Record each machine as a compute host, Hermes client, or both. A client with no GPU can manage requests and call a remote inference endpoint; it does not add GPU capacity by itself. Record which compute host owns each endpoint and which Hermes node uses it.

Keep three data types separate:

- **Shared playbooks and schemas:** safe reusable material in this repository.
- **Node inventory:** hardware, exact model identifiers, API URLs, runtime names, and incident notes in the node-local database.
- **Live scheduling state:** current health, queue depth, in-flight requests, latency, and GPU metrics in a runtime service reachable by the routers.

GitHub synchronizes the first category. It is not a live database or a suitable place for service health and request counters.

## Confirm the serving path before routing

For each compute host, confirm locally:

1. The model process is running and the expected model is loaded.
2. The service exposes an API reachable from the Hermes nodes over the intended private network.
3. The route shape and model identifier match what the caller expects. For an OpenAI-compatible service, check `/v1/models` and make a small `/v1/chat/completions` request with the correct model name.
4. A health check reports the model server itself as ready, not merely that the host responds to ping or SSH.
5. The host's GPU count, memory use, temperature, and utilization agree with `nvidia-smi`.

LM Link may provide the remote model path, but its installed version and API behavior must be checked on the nodes. LiteLLM can route among backend model API deployments when they expose compatible APIs; adding a gateway does not automatically make an LM Link peer a valid backend. Verify that integration on the installed software before switching callers.

## Routing behavior and limits

- A `least-busy` policy can distribute new requests by the gateway's view of in-flight requests. It does not directly measure GPU utilization or free VRAM.
- If each Hermes node runs its own gateway, each gateway needs a consistent view of endpoint health and load to avoid all choosing the same apparently idle host. Use a shared, private runtime state/metrics service or route all callers through a common gateway.
- Keep model aliases and generation settings consistent across replicas: exact model ID, quantization, chat template, context length, and concurrency limit. A similar display name does not prove identical behavior.
- Include endpoint health and network latency in routing. Avoid sending work to an unreachable or unhealthy remote host.
- Failover applies to new requests. A request already streaming from a failed endpoint usually cannot continue on another host; clients should surface the error and retry only when the operation is safe to repeat.
- Set per-host concurrency limits from measured memory and throughput. One request can consume very different resources depending on context length and generation settings.

## Troubleshoot in order

1. **Caller:** note the error and timestamp; check the configured base URL and model name without logging tokens or prompt contents.
2. **Network:** from the Hermes node, resolve and connect to the backend over the private network; distinguish DNS, routing, timeout, TLS, and HTTP errors.
3. **Gateway:** inspect the selected deployment, health status, timeout, retry, and concurrency behavior. Confirm all gateway instances see the same intended backend set.
4. **Model API:** query the server's models/health endpoints and run a small request directly against that backend, bypassing the gateway.
5. **GPU:** inspect `nvidia-smi` utilization, memory, power, temperature, and process list; check kernel logs for Xid/AER/PCIe and OOM evidence.
6. **Compare replicas:** send the same small request to each endpoint and compare readiness, latency, model identity, and errors.
7. **Record locally:** capture timestamp, node role, model ID, endpoint alias, request size class, error class, GPU evidence, and action. Do not store credentials, prompt content, or tenant data in shared GitHub files.

Do not reboot, reset a GPU, or reload its driver to clear a model-server error. Hardware power actions on Vast machines require the maintenance gate in the main skill.
