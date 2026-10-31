# Pattern: publish packages without a stored secret

**Problem.** A long-lived publish token (`NPM_TOKEN`, a PyPI token) in repository secrets can be
stolen, leaks into logs, and has to be rotated by a human.

**Pattern.** Trusted publishing: the registry trusts a specific CI workflow through OpenID Connect
(OIDC). In plain words, GitHub Actions hands the job a short-lived signed identity card ("I am
workflow `publish.yml` in repo X, run 123"); the registry checks it against what the owner
configured and accepts the upload. Nothing is stored, nothing to rotate. Provenance (a signed
statement of which commit and workflow built the package) comes with it.

| Registry | Workflow side | Registry side (owner, once per package) |
|---|---|---|
| npm | `permissions: id-token: write`; npm CLI 11.5.1 or later (`npm install -g npm@latest` in the job, or Node 24 which ships npm 11); `npm publish --provenance --access public`; no `NODE_AUTH_TOKEN`; `repository` in package.json must match the GitHub repo | npmjs.com > package > Settings (`/package/<name>/access`) > Trusted publisher > GitHub Actions: owner, repository, workflow file name (`publish.yml`), environment if any |
| PyPI | `permissions: id-token: write`; `pypa/gh-action-pypi-publish` with no password | pypi.org > project > Publishing > add a GitHub publisher |
| crates.io, RubyGems | same idea (OIDC trusted publishing) | registry settings |

Notes:
- A brand-new npm package must exist before a trusted publisher can be attached: publish the
  first version once by hand (or with a short-lived granular token, deleted right after).
- Keep the publish job on tag pushes only, in a protected environment if the repo has others
  with write access.
- Pin actions by full commit SHA in publish workflows.
Sources: https://docs.npmjs.com/trusted-publishers (npm docs, not reachable from the agent session on 2026-10-31; facts cross-checked in https://philna.sh/blog/2026/01/28/trusted-publishing-npm/ , Jan 2026), https://docs.pypi.org/trusted-publishers/ .
