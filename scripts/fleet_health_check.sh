#!/usr/bin/env bash
# fleet_health_check.sh — portable, read-only, no credentials required.
# Usage: fleet_health_check.sh host-a host-b host-c
#   (pass your SSH host aliases/names; they must already resolve via your ~/.ssh/config or sshd)
# Safe to run any time. Prints per-host: uptime, GPU list, and service state.
# Anything deeper (journalctl, AER, Xid) needs root — see references/gpu-fault-playbook.md.

set -uo pipefail

HOSTS=("$@")
if [[ ${#HOSTS[@]} -eq 0 ]]; then
  echo "usage: $0 <host-alias> [host-alias ...]" >&2
  exit 1
fi

for h in "${HOSTS[@]}"; do
  echo "===== $h ====="
  if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$h" \
      'echo "hostname: $(hostname)"; echo "uptime:   $(uptime -p 2>/dev/null || uptime)"; \
       echo "GPUs:"; (nvidia-smi -L 2>/dev/null || echo "  nvidia-smi unavailable"); \
       echo "services: vastai=$(systemctl is-active vastai 2>/dev/null) \
docker=$(systemctl is-active docker 2>/dev/null) \
containerd=$(systemctl is-active containerd 2>/dev/null)"; \
       echo "GPU detail:"; nvidia-smi --query-gpu=index,name,power.limit,pstate,temperature.gpu,utilization.gpu,utilization.memory --format=csv,noheader 2>/dev/null || true'
  then
    echo "  [unreachable or ssh failed]"
  fi
  echo
done

echo "Read-only check complete. For fault isolation see references/gpu-fault-playbook.md."
