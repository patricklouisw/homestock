# Phase 2 — HTTP and FastAPI, In-Memory CRUD

## What exists at the end

A FastAPI application with six working endpoints, storing spaces in a Python list
in memory. No database. Correct HTTP status codes, Pydantic validation, separate
request and response schemas, and 404 handling.

```text
GET    /health
GET    /spaces              200   list, in an envelope
GET    /spaces/{space_id}   200 / 404
POST   /spaces              201 / 422
PATCH  /spaces/{space_id}   200 / 404 / 422   partial update
PUT    /spaces/{space_id}   200 / 404 / 422   full replace
DELETE /spaces/{space_id}   204 / 404
```

---

## Concepts

### Framework vs. server

FastAPI is a **library**. It defines routes and validates data. It does not
listen on a port.

Uvicorn is an **ASGI server**. It owns the socket, parses HTTP, and calls your
application.

ASGI is the contract between them: the server turns a request into a dict and
calls your app object with it. Uvicorn knows nothing about FastAPI — only that
`app` satisfies ASGI.

```bash
uvicorn homestock_backend.main:app --reload
#       └──── module ────┘ └─┬─┘
#                        variable
```

That argument is an **import path**, not a file path. `src/` never appears in it,
because the build backend strips `src/` when installing the package.

### The routing table

```python
@app.get("/spaces")
def get_all_spaces(): ...
```

The decorator runs **once, at import time**. Its job is registration — it adds a
row to a table on your `app` object:

```text
method   path              handler
GET      /spaces           get_all_spaces()
GET      /spaces/{id}      get_a_space()
```

When a request arrives, FastAPI matches `(method, path)` against that table.

**Route order matters.** Starlette matches in declaration order, first match
wins. A parameterized route declared above a literal one swallows it — declare
`/spaces/search` *before* `/spaces/{space_id}`, or `search` gets captured as an
id and your endpoint becomes unreachable, silently.

### `async def` vs `def`

- `async def` runs on the event loop. A blocking call inside it (a synchronous DB
  query, `requests.get`, `time.sleep`) freezes the server **for every concurrent
  user**.
- plain `def` is run in a threadpool by FastAPI, so blocking is contained.

Use `async def` only when you actually `await` something. In Phase 3, SQLAlchemy's
normal session is synchronous, so those routes should be plain `def`.

### Status codes

| Code | Means |
|---|---|
| 200 | OK, body attached |
| 201 | Created — a new resource now exists |
| 204 | No Content — succeeded, deliberately empty body |
| 404 | Client asked for something that does not exist |
| 422 | Body failed validation (FastAPI's default for Pydantic errors) |

404 vs 500 is not a cosmetic difference. 4xx means "you sent something wrong,"
5xx means "I broke." Returning 500 for a missing resource tells the client to
retry and tells your monitoring you have a bug.

### Request and response schemas are different

Three models, deliberately not one:

```text
SpaceRequest        name required            POST and PUT — full representation
SpacePatchRequest   name optional            PATCH — partial update
Space               id + name                what goes back out
```

**The client must never be able to set `id`.** `SpaceRequest` has no `id` field,
so FastAPI drops it during validation and the handler never sees it. A client
POSTing `{"id": "999", "name": "Garage"}` gets a server-generated UUID.

This matters far more in Phase 9, where the same mechanism prevents a client from
setting `user_id` and claiming another user's data.

`response_model` is also an **allowlist**, not just documentation — FastAPI
returns only the declared fields and silently drops the rest. That is what keeps
`hashed_password` out of API responses later.

### PATCH vs PUT

```text
PUT     replace the whole resource. Every field required.
PATCH   merge. Omitted fields are left unchanged.
```

Implementing PATCH correctly needs one non-obvious thing: distinguishing
*"field omitted"* from *"field explicitly set to null"*.

```python
updates = payload.model_dump(exclude_unset=True, exclude_none=True)
```

Pydantic tracks which fields were actually present in the incoming JSON, in
`model_fields_set`, separately from which hold a value:

| body | `fields_set` | `model_dump()` | with both flags |
|---|---|---|---|
| `{"name": "Galley"}` | `{'name'}` | `{'name': 'Galley'}` | `{'name': 'Galley'}` |
| `{}` | `set()` | `{'name': None}` | `{}` |
| `{"name": null}` | `{'name'}` | `{'name': None}` | `{}` |

Without `exclude_unset`, row 2 would wipe the name on every `PATCH {}`.

### Optional does not mean optional

```python
name: Optional[str]                 # required AND nullable
name: Optional[str] = None          # optional
name: str | None = None             # same thing, modern spelling
```

**A field is required purely because it has no default.** `Optional[X]` only
means "may be `None`".

For a constrained optional field, use `Annotated` so the constraint attaches to
the `str` branch rather than the nullable union:

```python
name: Annotated[str, Field(min_length=1, max_length=100)] | None = None
```

---

## Steps

### 1. Create the project

```bash
cd backend
uv init --package .
uv add "fastapi[standard]" uvicorn
```

`--package` produces a `src/` layout with a `[build-system]`, so your code is
installed into the venv as a real package.

### 2. Package layout

```text
backend/
├── pyproject.toml
├── uv.lock
├── .venv/                    gitignored
└── src/
    └── homestock_backend/
        ├── __init__.py
        ├── main.py           routes
        ├── schemas.py        Pydantic models
        └── store.py          the in-memory list
```

**Why `src/` layout**, rather than files at `backend/` root:

- Alembic's `env.py` can `from homestock_backend.models import Base` without
  `sys.path` hacks (Phase 3)
- pytest imports the **installed** package, the same way production does, which
  removes a whole class of "passes locally, fails in CI" bugs (Phase 5)
- imports stay identical from the app, tests, and migration scripts

### 3. Write the modules

`schemas.py` — Pydantic models only, imports nothing of yours.
`store.py` — the list, imports `schemas`.
`main.py` — routes, imports both.

Dependencies flow one direction. A cycle (`main` → `store` → `main`) fails with a
partially-initialized module error, which is why models live in their own file.

### 4. Run it

```bash
uv run uvicorn homestock_backend.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`.

`/docs` is generated from your routing table and your Pydantic models. It cannot
drift from the code, because it is derived from it. `/openapi.json` is the raw
document.

---

## Gotchas

### Import names are not file paths

A module inside a package is **never** importable by its bare name:

```python
from schemas import Space                     # ✗ ModuleNotFoundError
from homestock_backend.schemas import Space   # ✓
```

`schemas.py` sitting next to `main.py` does not put `schemas` on `sys.path`. Its
real name is `homestock_backend.schemas`.

But **third-party packages are top-level**, because site-packages is directly on
`sys.path`:

```python
from fastapi import FastAPI                   # ✓ correct as-is
from homestock_backend.fastapi import FastAPI # ✗ over-applying the rule
```

Same rule, different answers, because the packages sit at different depths
relative to a `sys.path` entry.

### Pydantic models are not dicts

```python
space["name"] = value    # ✗ TypeError — no __setitem__
space.name = value       # ✓
```

### Architecture mismatch on Apple Silicon

`import fastapi` failed with, at the **bottom** of a long traceback:

```text
ImportError: dlopen(.../pydantic_core/_pydantic_core.cpython-314-darwin.so):
  (mach-o file, but is an incompatible architecture (have 'x86_64', need 'arm64'))
```

Cause: `uv` was an Intel binary at `/usr/local/bin/uv`, running under Rosetta. It
installed x86_64 wheels. Running the venv's Python natively (arm64) could not
load them.

Fix: reinstall uv natively, delete the venv, `uv sync`.

```bash
rm /usr/local/bin/uv
curl -LsSf https://astral.sh/uv/install.sh | sh
which uv && file "$(which uv)"     # must be arm64
rm -rf .venv && uv sync
```

Two lessons:

1. **Read the whole traceback.** Python puts the proximate cause last. The top
   said "import fastapi failed," which looked like "not installed."
2. **"It works when I run it" is not proof.** `uv run python` and
   `.venv/bin/python` differed by architecture, invisibly, until something needed
   a compiled extension. When two ways of invoking the same tool behave
   differently, the environment difference *is* the bug.

### VS Code cannot find the interpreter

The Python extension only auto-discovers `.venv` at the **workspace root**. In a
monorepo the venv is at `backend/.venv`, so it is missed.

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.venvPath": "${workspaceFolder}/backend",
  "python.analysis.extraPaths": ["${workspaceFolder}/backend/src"]
}
```

Then **Developer: Reload Window** — the extension caches the selection.

Do **not** add the package's own directory (`backend/src/homestock_backend`) to
`extraPaths`. It makes Pylance approve bare imports that fail at runtime. An
editor config that accepts imports Python rejects is worse than no config.

### Do not install stdlib names from PyPI

`uv add uuid` installs an abandoned 2006 backport that shadows the standard
library module. `uuid`, `json`, `datetime`, `pathlib`, `typing`, `logging`,
`sqlite3` are all built in. Attackers squat stdlib names on PyPI precisely
because people reflexively install whatever matches a failed import.

---

## Verify

```bash
uv run uvicorn homestock_backend.main:app --reload
```

In `/docs`, or with curl:

```bash
curl -X POST http://127.0.0.1:8000/spaces \
  -H "Content-Type: application/json" \
  -d '{"name": "Bathroom"}'
```

| Request | Expected |
|---|---|
| `POST /spaces {"name":"Bathroom"}` | 201, server-generated uuid |
| `POST /spaces {"name":""}` | 422 |
| `POST /spaces {"id":"999","name":"X"}` | 201, `id` is a uuid, **not** 999 |
| `GET /spaces` | 200, `{"spaces": [...]}` |
| `PATCH /spaces/{id} {}` | 200, unchanged |
| `PATCH /spaces/{id} {"name":"X"}` | 200, updated |
| `PUT /spaces/{id} {}` | 422 — PUT requires all fields |
| `DELETE /spaces/{id}` | 204, empty body |
| `DELETE` same id again | 404 |

If Postman returns
`"Input should be a valid dictionary or object to extract fields from"`, the body
was sent as a **JSON string** rather than a JSON object — Body → raw → **JSON**,
no surrounding quotes.

The `input` field in a 422 body shows what the server actually received. It is
the most useful part and the one people skip.
