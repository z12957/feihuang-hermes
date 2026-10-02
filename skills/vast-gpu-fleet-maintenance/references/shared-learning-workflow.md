# Shared skill learning loop

Hermes skills are procedural memory. A node can improve a local skill after a reliable solution, a repeated pitfall, or a user correction. GitHub is the reviewed, versioned distribution point for knowledge that all nodes should share.

## Roles

- **Node Hermes:** uses the installed skill and captures a reusable lesson locally.
- **Publisher:** compares the local skill with the shared version, scans it, and opens a draft PR on a node-specific branch.
- **Curator:** reviews for correctness, duplicate guidance, conflicts, and private fleet details; merges approved changes to `main`.
- **Node sync timer:** polls GitHub main and updates an installed skill only when it has no local edits. It leaves local edits alone and reports conflicts.

The publisher never pushes to `main`. Give each node a generic public contributor label such as `node-a`; do not use the site or machine name in branch names or PR metadata.

## First-time setup on each Hermes node

Use a dedicated clone for synchronization. This repository is public, so fetching it needs no token; publishing requires the node owner's normal GitHub CLI authentication with permission to create branches and PRs.

```bash
git clone https://github.com/z12957/feihuang-hermes.git ~/feihuang-hermes
python3 ~/feihuang-hermes/scripts/shared_skills.py sync \
  --repo ~/feihuang-hermes --hermes-home ~/.hermes
```

The sync command installs each shared skill under `~/.hermes/skills/<skill-name>` and saves a local baseline manifest at `local/shared-skill-sync.json`. The manifest is ignored by Git. Do not edit or commit it by hand.

To poll every 15 minutes on Linux with a user systemd manager:

```bash
mkdir -p ~/.config/systemd/user
cp ~/feihuang-hermes/deploy/systemd/hermes-shared-skills-sync.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now hermes-shared-skills-sync.timer
systemctl --user list-timers hermes-shared-skills-sync.timer
```

The supplied unit assumes the clone is at `~/feihuang-hermes` and Hermes home is `~/.hermes`. Edit the unit paths for a different location. On systems without a persistent user systemd manager, schedule the same `sync` command with that system's task scheduler.

## Publish a learned procedure

After Hermes updates a skill, review the complete local diff and remove private or one-off details. Install `gh` and `gitleaks`, authenticate `gh` with the repo's write access, then run:

```bash
python3 ~/feihuang-hermes/scripts/shared_skills.py publish \
  --repo ~/feihuang-hermes \
  --hermes-home ~/.hermes \
  --skill vast-gpu-fleet-maintenance \
  --node-slug node-a
```

The publisher uses a temporary Git worktree based on current `origin/main`, copies only the selected skill, skips local database/credential files, scans staged changes with Gitleaks, and opens a draft PR. It does not alter the installed skill or the clone's current branch. Read the PR diff yourself; automated secret scanning cannot establish that a lesson is correct or safe to publish.

A curator reviews the procedure, folds it into the right skill/reference, checks it against the existing playbook, and merges it. Do not auto-merge generated skill changes.

## Conflicts and local changes

- If only `main` changed, sync updates the installed shared skill.
- If only the local installed skill changed, sync preserves it so it can be published.
- If both local and `main` changed, sync leaves the installed files untouched and reports a conflict. Publish the local candidate, let the curator merge/reconcile it, then sync again.
- A local skill absent from `main` is not deleted automatically.
- Keep model health, GPU utilization, queue depth, endpoints, host IDs, tenant state, and incident-specific measurements in the node-local database.

Hermes upstream also has an opt-in skill sync client for its own sync service. That is a separate transport and permission model from this GitHub workflow. The upstream source currently describes an organization/admin-gated sync path; do not assume it is enabled on a node or that it synchronizes this GitHub repository.
