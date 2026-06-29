# Runbook — updating dependencies

## Python (uv workspace)

```bash
uv sync --upgrade            # refresh the lock to the latest allowed versions
uv run pytest                # prove the suite still passes
uv audit --preview-features audit-command   # OSV advisory scan (also a CI gate)
```

CI syncs with `--locked --preview-features malware-check` (aborts before running a package
flagged by an OSV MAL advisory) and runs `uv audit`. Commit the updated `uv.lock`.

## Frontend (npm)

```bash
cd frontend
npm update                   # or bump specific packages in package.json
npm run lint && npm run check && npm run typecheck && npm run test && npm run build
```

Commit the updated lockfile. Keep the pinned tool versions in `.github/workflows/ci.yml`
(uv, node) in step with what the project actually uses.
