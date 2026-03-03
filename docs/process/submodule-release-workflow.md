# Submodule Release Workflow (MT5 Bridge)

## Required Order

1. Commit changes inside `mt5-connection-bridge`.
2. Push `mt5-connection-bridge` branch/`main` first.
3. In parent repo, commit only the submodule pointer update.
4. Push parent repo `main`.

## Rules

- Do not run `git add -A` at parent repository root when the intent is only a submodule pointer bump.
- Validate submodule state with `git submodule status` before and after push.
- Keep bridge operational checks (`scripts/smoke_bridge.sh`) in the submodule release checklist.
- Preserve local `.env` secrets; never add `.env` files to git.

## Mistakes To Avoid

- Pushing parent repo before submodule commit is available remotely.
- Mixing unrelated root-level files into a submodule pointer commit.
- Assuming listener teardown succeeded without checking active ports.

