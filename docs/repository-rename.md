# Racing Hub repository rename

On 2026-09-10, the existing GitHub repository was renamed in place from
`chwunderpers/motorsport-hub` to `chwunderpers/racing-hub`. The product name is
**Racing Hub** and the private VS Code agent is **Racing Review**.

## Preservation verification

The repository was not cloned, recreated or deleted. Its GitHub node ID remains
`R_kgDOUToKZg`. Immediately before and after the rename, the following matched:

- All 16 issues: node IDs, numbers, states and comment counts.
- All 3 pull requests (#17, #18, #19): node IDs, numbers, states, commit counts,
  comment counts and review counts.
- All 11 label IDs and names.
- Both branches and every advertised Git ref, with identical commit hashes.
- Public visibility, default branch, wiki/issues/discussions feature settings,
  star and fork counts. There were no tags, releases or milestones.

GitHub Pages was disabled and the repository had no Actions workflows. After
verification, exact product-name references in issue #1 and issue #15 were
updated to Racing Hub, along with the repository description. Historical
comments and commits were not rewritten.

This preserves records in place, including their existing links and history;
it does not attempt to manufacture replacement issues or replay comments under
a different author. The old GitHub repository URL resolves to the same repository.
Do not recreate a repository at the old name: that would break GitHub's redirects.

The local `origin` now points directly to
`https://github.com/chwunderpers/racing-hub.git`. Existing branches and PR #19
continue in the renamed repository; this rename does not authorize merging a PR.
Older commits, decisions and historical comments retain their original wording.

## Compatibility names

This is a product/repository rename, not a data-identity migration. The following
remain stable to protect existing publications and local data:

- The `https://w3id.org/motorsport-hub/` RDF namespace and resource/graph IRIs.
- PostgreSQL database/login and GraphDB repository identifiers named `motorsport`.
- Existing Docker volume names, local workspace location and operator configuration.
- The local architecture document filename `motorsport_events_schedule.md`, which
  describes the motorsport domain and is referenced by existing working notes.

New product-facing text, HTML metadata, the FastAPI title, frontend package name,
and review agent use Racing Hub/Racing Review. The GraphDB repository configuration
label uses Racing Hub for newly created repositories; already provisioned repository
metadata is not rewritten by bootstrap. Domain language such as "motorsport
knowledge" still describes the subject of the platform, not an obsolete product name.

Existing untracked workspace customization/spec files are preserved locally rather
than added wholesale to GitHub. The GitHub rename carries every existing remote
record; it does not implicitly publish previously untracked local files.

GitHub's [rename documentation](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository)
describes redirects and the exceptions for GitHub Pages URLs and reusable Actions.