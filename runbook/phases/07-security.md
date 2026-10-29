# Phase 7 · Security

**Goal:** close exploitable weaknesses first without advertising them, get secrets out of git,
and give agents the least power that still lets them work.

## Decisions to take

| Decision | Arffornia default | Why |
|---|---|---|
| Disclosure on public repos | Unfixed exploitable issue: neutral title ("Harden IPC input validation"), no repro, fix in a PR with a neutral description. Exception: an already-public secret gets an issue saying rotation is needed | Repos are public; attackers read issues too |
| Secret rotation | Owner only; agents remove the value from defaults and say rotation is still required | Removing from git does not un-leak history |
| Eval cases about unfixed findings | Kept out of the public repo (git-ignored "held" folder) until the fix merges | Same disclosure rule applies to test data |
| Agent permissions | Deny rules (secrets, keys, merges, releases, force-push), sandbox on, `git push` asks; force-with-lease allowed on feature branches only | Deterministic limits beat instructions |
| Automations | Each scheduled agent has a **lethal trifecta card**: it may combine at most two of private data, untrusted content, external output | Prompt injection cannot be filtered reliably |
| Rollout of risky hardening | Report-only first (CSP), draft PRs with staged apply and rollback (NetworkPolicies) | Hardening that breaks production gets reverted and forgotten |

**The sandbox in one line:** shell commands run with writes limited to the project and caches,
reads of `~/.ssh`, `~/.aws`, `~/.kube`, `~/.config/gh` denied, and network limited to an
allow-list; hooks run outside it, deny rules apply before it.

## Steps (agent)

1. **Sweep:** list open `type: security` + `agent-ready` issues not covered by an open PR; fix them
   in priority order, each with tests that fail without the fix.
2. **Secrets:** gitleaks (pinned binary with checksum) in CI and pre-commit; move runtime secrets to
   server-only config or the secret store; placeholders in committed config.
3. **Supply chain:** temp file, verify hash, then rename, for every download (Java runtime,
   mod loader, mods); pin images by digest and actions by version.
4. **Boundaries:** validate every input crossing a trust boundary (HTTP, IPC, network packets,
   files from the network); constrain file paths under their base directory.
5. **Agents:** apply the deny rules and guard hook from [phase 5](05-harness-skills.md); write a
   trifecta card for each automation; never give one agent issue text, secrets and push rights
   at once without a human in the loop.

## Human touchpoints

- Rotate leaked secrets. Run the staged apply for network policies. Decide disclosure exceptions.

## Anti-patterns we hit

- **A service-account secret committed since the first commit** of a public repo. The PR only
  removes it from defaults; the owner must rotate. Put rotation at the top of the owner's actions.
- **Security fixes that must deploy together** (mod config split + provisioning templates).
  Say "merge and deploy together" on both PRs and in the chantier.
- **Debug pages live in production** via a ConfigMap; the pod does not restart on ConfigMap
  change. The PR must say "restart by hand" and how to check (error page shows no stack trace).
- **Default-deny network policies** can cut traffic: kept as a draft with a Hubble-based check.
- **Unpinned "latest" image**: pinning to the same digest still restarts pods (template change).
  Merge in a quiet window.
- **Shared Vault role for every namespace**: a prerequisite to fix before preview environments.

## Checklist

- [ ] No exploit details in public issues for unfixed weaknesses
- [ ] Every leaked secret has an owner action "rotate" with the exact steps
- [ ] gitleaks and dependency bots active; images and actions pinned
- [ ] Every download is hash-verified and atomic
- [ ] Every automation has a trifecta card; none holds all three
- [ ] Risky rollouts are report-only or draft with rollback steps
