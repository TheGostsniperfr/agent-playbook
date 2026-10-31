# Standard setup items (Chantier 0)

| Item | Default | Why | Owner action |
|---|---|---|---|
| Ops repo `<org>/ops` (private) with `STATE.md` | on | A new chat resumes from one file; public repos stay free of live state | Create the private repo |
| Review stack page | on | One queue of chantiers instead of PR-by-PR review | None (agent publishes) |
| Audit per component | on | Evidence before changes; questions batched | Answer the batched questions |
| Foundation per repo | on | Every repo has the same verbs, so agents and humans run `make check` everywhere | Validate the foundation chantier |
| Docs as code + diagrams | on | Docs reviewed like code; diagrams regenerated, never stale | None |
| Org profile `.github` | on | First impression and shared issue forms | None if agents may push to `.github` |
| Agent-ready issues + board lanes | on | Agents pick ready work; the owner sees only chantiers | Grant a project token for board sync if GraphQL is blocked |
| Harness (org layer + overlays + review gate) | on | Rules enforced by hooks and checks, not by memory | Install the plugin locally |
| Deterministic guards per stack | on | Static and dynamic analysis catch what review misses, for free | None |
| Automations (weekly brief, monthly upkeep) | on, after two good runs | Work continues between sessions; skipped when nothing changed | Create the scheduled tasks |
| Licence | needs decision | Legal default differs per asset type | Pick |
| Paid services | off | Free tiers, open source, self-hosted only | Say otherwise explicitly |
