# HomeStock — Build Documentation

A record of how this project was built, phase by phase, written so it can be
**redone from an empty directory**.

Each phase document contains:

- **What exists at the end** — the concrete deliverable
- **Concepts** — the ideas you need before the commands make sense
- **Steps** — exact commands and file contents
- **Gotchas** — the things that actually went wrong, and why
- **Verify** — how to prove each step worked

## Phases

| Phase | Document | Status |
|---|---|---|
| 1 | [Git, GitHub, and repository structure](phase-1-git-and-repo.md) | complete |
| 2 | [HTTP and FastAPI — in-memory CRUD](phase-2-fastapi.md) | complete |
| 3 | [PostgreSQL and persistence](phase-3-postgresql.md) | complete |
| 4 | Inventory domain — foreign keys and relationships | next |

## Related

- [learning.txt](learning.txt) — end-of-phase checkpoint questions and debugging lessons

## Environment this was built on

```text
macOS (Apple Silicon, arm64)
Python 3.14.6
uv 0.12.5
Docker Desktop
PostgreSQL 16 (in Docker)
```

The architecture matters. Several problems in Phase 2 and 3 came from Intel
(x86_64) tools running under Rosetta on an Apple Silicon Mac. If you are
reproducing this on Apple Silicon, check `file $(which <tool>)` reports `arm64`
before trusting any toolchain.
