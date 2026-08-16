# Phase 3 — PostgreSQL and Persistence

**Status: in progress.**

| Task | State |
|---|---|
| PostgreSQL running in Docker | done |
| `home_inventory` database + non-superuser role | done |
| `.env` / `.env.example` | done |
| `psycopg` driver installed | done |
| `config.py` | done |
| `database.py` | done |
| `models.py` | done |
| Alembic migrations | done |
| Routes switched from `store.py` to the database | not started |

---

## Concepts

### A database is a server, not a library

`store.py` was a Python list inside the app's memory. PostgreSQL is a **separate
program**, possibly on another machine, reached over a network socket, with its
own authentication.

Your app is a *client*. That is why it needs a host, a port, a username, and a
password — none of which a Python list ever needed.

### How PostgreSQL is organized

```text
SERVER (cluster)          one Postgres process — what the container runs
 └── DATABASE             "home_inventory". A connection picks exactly one
      └── SCHEMA          a namespace. Default is "public"
           └── TABLE      "spaces", "inventory_items"
```

Separately, the server has **roles** — Postgres's word for users. Roles exist at
the *server* level, not inside a database, which is why access to a database has
to be granted explicitly.

### Least privilege

The `postgres` superuser can drop any database, read any table, and create more
superusers. The application only needs to read and write its own tables.

If the app is ever compromised — SQL injection, leaked connection string, bad
migration — the damage is bounded by what its role may do. Same principle as IAM
roles in Phase 13. On a laptop the stakes are low; the habit is the point.

### The connection string

```text
postgresql+psycopg://homestock_app:apppassword@localhost:5432/home_inventory
└───┬────┘ └──┬───┘  └─────┬─────┘ └─────┬────┘ └───┬───┘ └┬─┘ └──────┬─────┘
 dialect    driver        role       password      host   port    database
```

The scheme has **two** parts. `dialect` picks the SQL flavour; `driver` picks the
Python library. Omit the driver and SQLAlchemy uses the dialect default — which
for PostgreSQL is `psycopg2`, the older library. This project uses **psycopg 3**
(package `psycopg`, imported as `psycopg`), so the driver must be stated
explicitly or you get:

```text
ModuleNotFoundError: No module named 'psycopg2'
```

Six values in one string. In Phase 13 `host` becomes an RDS endpoint and
`password` comes from a secrets manager; everything else is unchanged. That is
why it is a single configurable value rather than six hardcoded ones.

### `.env` vs `.env.example`

```text
.env           real values, gitignored, never leaves the machine
.env.example   same KEYS, placeholder values, committed
```

`.env.example` is the contract. It documents *which* variables exist without
revealing *what* they are.

### Image vs container vs volume

```text
IMAGE       read-only template. "postgres:16". Downloaded once.
CONTAINER   a running instance. Its filesystem is DISCARDED when deleted.
VOLUME      storage outside any container, managed by Docker. Survives deletion.
```

Container filesystems are disposable. Without a volume mounted at Postgres's data
directory, `docker rm` destroys the database silently.

### Port publishing

```text
-p 127.0.0.1:5432:5432
   └───┬────┘ └┬─┘ └┬─┘
   host iface  host container
```

Bare `-p 5432:5432` binds to `0.0.0.0` — every interface — so anyone on your WiFi
can reach the database. Binding to `127.0.0.1` limits it to your machine. Same
lesson as `host="0.0.0.0"` on a dev server.

Inside a container, `localhost` means *that container*. This is why the backend
container will connect to `db:5432` in Phase 11, not `localhost:5432`.

### ORM vs raw SQL

An ORM maps rows to Python objects, so you write `space.name` instead of
`row[1]`, and it generates SQL for you.

What you give up is visibility. An ORM will happily emit a query inside a loop —
the N+1 problem — and you will not notice unless you look. Hence `echo=True`
below. **An ORM is not a reason to stop understanding SQL.**

### Engine vs Connection vs Session

```text
ENGINE      created ONCE at startup. Holds the connection POOL.
            Not a connection itself. Lazy — opens nothing until asked.

CONNECTION  an actual socket to Postgres. Expensive; hence the pool.
            Postgres allows ~100 by default.

SESSION     a unit of work. Wraps a connection, tracks loaded/pending
            objects, and defines a TRANSACTION. Created PER REQUEST.
```

Lifetimes are the whole point: **one engine per application, one session per
request.** Sharing a session across requests leaks one user's uncommitted
changes into another's transaction.

### A session is a transaction

```python
session.add(space)      # nothing has happened in the database
session.commit()        # NOW it is durable, and the transaction closes
```

Until `commit()`, nothing is written and no other connection can see it. On an
exception, `rollback()` undoes everything staged since the transaction began,
atomically. A Python list could never offer that.

### SQLAlchemy model vs Pydantic schema

Both are classes with typed fields. They describe different things:

| | Pydantic (`schemas.py`) | SQLAlchemy (`models.py`) |
|---|---|---|
| purpose | JSON in / JSON out | rows in a table |
| validates | untrusted client input | nothing — you own this data |
| knows about | HTTP | columns, types, indexes, foreign keys |
| lives for | one request | forever, on disk |

`SpacePatchRequest` exists because a *client* may send a partial update. That
idea is meaningless to a table — a row always has every column. Conversely a
table has indexes and foreign keys, which mean nothing to JSON.

Keeping them separate is also a security boundary: in Phase 9 the `User`
**model** has `hashed_password`; the `User` **schema** does not.

### Dependency injection with `yield`

```python
def get_db():
    db = SessionLocal()
    try:
        yield db          # route runs here
    finally:
        db.close()        # runs after the response, even on exception
```

FastAPI runs everything before `yield`, injects the value, then guarantees the
`finally` block runs.

That guarantee is why sessions are done this way. Without it, a route that raises
leaks a connection. A hundred errors and Postgres refuses new connections — a
real outage mode whose symptom looks nothing like its cause.

---

## Steps

### 1. Start PostgreSQL

```bash
docker run --name homestock-db \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=home_inventory \
  -p 127.0.0.1:5432:5432 \
  -v homestock-pgdata:/var/lib/postgresql/data \
  -d postgres:16
```

| Flag | Purpose |
|---|---|
| `--name` | stable name for `docker stop/logs/exec` |
| `-e POSTGRES_PASSWORD` | superuser password, read on **first boot only** |
| `-e POSTGRES_DB` | database created on first boot |
| `-p 127.0.0.1:5432:5432` | publish to loopback only |
| `-v homestock-pgdata:...` | named volume — this is what makes data survive |
| `-d` | detached |
| `postgres:16` | **pin the version**; `latest` changes under you |

Verify:

```bash
docker ps
docker logs homestock-db     # look for "ready to accept connections"
```

`docker run -d` succeeds even if Postgres dies a second later, because the
*container* started. `docker ps` shows only running containers.

### 2. Create the application role

```bash
docker exec -it homestock-db psql -U postgres -d home_inventory
```

```sql
CREATE ROLE homestock_app WITH LOGIN PASSWORD 'apppassword';
GRANT CONNECT ON DATABASE home_inventory TO homestock_app;
GRANT USAGE, CREATE ON SCHEMA public TO homestock_app;
\du
\q
```

- `WITH LOGIN` — can authenticate. Without it, a role is just a permission group.
- `GRANT CONNECT` — without it, login succeeds but the connection is refused.
- `CREATE ON SCHEMA public` — Alembic needs it to build tables.

In `\du`, `homestock_app` should have an **empty** Attributes column. `postgres`
being a superuser is correct and expected — the goal is that the *application*
does not connect as one.

### 3. Configuration files

`backend/.env` (gitignored):

```text
DATABASE_URL=postgresql+psycopg://homestock_app:apppassword@localhost:5432/home_inventory
```

`backend/.env.example` (committed):

```text
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/home_inventory
```

Confirm immediately, while the password is still a throwaway:

```bash
git status                        # .env must NOT appear
git check-ignore -v backend/.env  # shows which rule ignores it
```

### 4. Install packages

```bash
cd backend
uv add "psycopg[binary]" sqlalchemy pydantic-settings
```

`psycopg` is the driver — compiled C, so check it has a wheel for your Python
version before building on it. `pydantic-settings` was split out of Pydantic in
v2 and must be installed separately.

Expect SQLAlchemy `2.x`. Version 2 changed the model syntax; tutorials using
`Column(...)` without `Mapped[...]` are pre-2.0.

### 5. `config.py`

```python
"""Application configuration, loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Values the app needs at runtime, read from .env or the environment."""

    model_config = SettingsConfigDict(env_file=".env")

    database_url: str


settings = Settings()  # type: ignore[call-arg]
```

- `BaseSettings` reads from the environment and `.env`, so `Settings()` takes no
  arguments and still comes back populated.
- Field name → env var is automatic: `database_url` reads `DATABASE_URL`.
- **No default means required.** A missing value crashes at import — that is,
  at application startup, with a clear message — rather than at 2am on the first
  database call.
- `model_config` is a fixed name Pydantic v2 looks for. Misspell it and `.env`
  is silently ignored.
- The `type: ignore` is for a known Pylance/pydantic-settings false positive:
  static analysis sees a required constructor argument and cannot model the fact
  that `BaseSettings` fills it from the environment before validating.

Nothing else in the codebase should read `os.environ` directly.

### 6. `database.py`

```python
"""Database engine, session factory, and the declarative base for models."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from homestock_backend.config import settings


engine = create_engine(settings.database_url, echo=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Parent class for every SQLAlchemy model."""


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for one request, then close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- `SessionLocal` is a **factory** — capitalized because calling it produces a
  session. `SessionLocal` is one object; `SessionLocal()` is a new session.
- `autocommit=False` is what makes a session a transaction.
- `autoflush=False` stops SQLAlchemy silently writing pending changes before a
  query. See the decision note below.
- `Base` has an empty body on purpose. It exists to be inherited from and to
  carry `Base.metadata`, the registry every model adds itself to.
- `get_db` manages only the session's *lifetime*. Committing belongs to the
  route, because only the route knows whether the work succeeded.

#### Decision: `autoflush=False`

SQLAlchemy's default is `autoflush=True` — before any query, the session
automatically flushes pending changes. This project turns it **off**. Both
choices are defensible; here is the trade.

**Flush is not commit:**

```text
FLUSH    send pending INSERT/UPDATE/DELETE inside the current transaction.
         Not durable. Rollback undoes it. Other connections cannot see it.
COMMIT   end the transaction. Durable and visible. Always flushes first.
```

**Why off:** with autoflush on, a `SELECT` is also, invisibly, a write — so
reading a line no longer tells you whether it touches the database. Worse, errors
surface in the wrong place:

```python
space = Space(id="1")     # no name, and name is NOT NULL
db.add(space)
# ... 40 unrelated lines ...
db.query(Space).filter_by(name="Kitchen").first()
# IntegrityError raised HERE, pointing at the SELECT. The bug is in the add().
```

**What it costs:** you must flush explicitly when a query needs to see pending
changes. The failure mode is *silent* — a query returns nothing and looks correct:

```python
db.add(space)
db.query(Space).filter_by(id=space.id).first()   # → None
db.flush()                                        # the fix
```

Also needed to obtain a database-generated value before commit:

```python
db.add(item)
db.flush()               # INSERT runs; item.id is populated by Postgres
child.parent_id = item.id
db.commit()              # both rows land together, or neither does
```

**The counter-argument**, which is a good one: forgetting a manual flush produces
a silently wrong answer, while autoflush produces a loud confusing traceback — and
loud beats silent. The middle path is to leave autoflush on globally and disable
it only where it hurts:

```python
with db.no_autoflush:
    ...   # multi-step object construction, temporarily invalid state
```

Note the FastAPI ecosystem leans the other way from SQLAlchemy's own default: the
widely-copied FastAPI SQL tutorial uses `autoflush=False`, which is where most
FastAPI projects inherit this setting from.

**Revisit this** if "my data isn't there" bugs start costing more time than
misplaced tracebacks.

### 7. `models.py`

```python
"""SQLAlchemy models — the database tables."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from homestock_backend.database import Base


class Space(Base):
    """A room or area that holds inventory items."""

    __tablename__ = "spaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
```

Two type systems on one line:

```text
Mapped[str]     the PYTHON type   → editors and type checkers see a str
String(36)      the SQL type      → VARCHAR(36) in Postgres
```

- `__tablename__` is required and **plural** by convention — the class describes
  one row, the table holds many.
- `primary_key=True` creates an index automatically. Lookups by `id` are fast;
  lookups by `name` are not, because nothing indexes it.
- `String(36)` because a UUID in text form is 36 characters. Postgres has a
  native `UUID` type that is smaller and type-checked — a good later migration
  exercise; `String(36)` keeps the existing Pydantic `Space.id: str` working now.
- `nullable=False` becomes `NOT NULL`. There are now **two** independent layers
  enforcing a name exists — Pydantic at the HTTP boundary, Postgres at storage.
  That is deliberate: the database does not assume every writer came through
  your API.

### 8. Alembic migrations

#### Why not `Base.metadata.create_all()`

It works exactly once. It creates tables that do not exist and **silently ignores
tables that do**. Add a column to an existing table and it does nothing at all —
it understands absence, not change. Fine for throwaway test databases, useless
for anything holding data you care about.

#### What a migration is

A Python file with two functions — `upgrade()` applies a change, `downgrade()`
undoes it. Each file is a **revision** with a pointer to the one before it, so
they form a linked list:

```text
None ──▶ 2ea785dfaa7e ──▶ (next) ──▶ (head)
         down_revision=None
```

- **`head`** — the newest revision
- **`down_revision`** — pointer to the previous revision; this defines the order
- **`base`** — the empty database, before any migration

Alembic records where the *database* currently sits in a table called
`alembic_version`, holding exactly one row:

```text
database says:  "I am at 2ea785dfaa7e"
repo says:      "head is <newest file>"
upgrade head →  runs everything in between, updates the row
```

That is why migrations work across machines. A fresh database says "I am at
nothing," so `upgrade head` replays every migration in order.

#### Setup

```bash
cd backend
uv add alembic
uv run alembic init alembic     # second arg = directory name for scripts
```

Produces:

```text
backend/
├── alembic.ini
└── alembic/
    ├── env.py            ← edit this
    ├── script.py.mako    template for generated migrations
    └── versions/         migration files land here
```

#### Keep the database URL out of `alembic.ini`

`alembic.ini` ships with:

```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

**Leave that placeholder alone.** `alembic.ini` is committed to Git; putting the
real URL there commits a password. Inject it at runtime in `env.py` instead,
where it comes from `.env`.

Verify before every push:

```bash
git diff --staged backend/alembic.ini
```

#### `alembic/env.py` changes

Add three imports:

```python
from homestock_backend.config import settings
from homestock_backend.database import Base
from homestock_backend import models  # noqa: F401 — registers tables on Base.metadata
```

The third looks unused and linters will flag it — hence the `noqa`. **It is
doing the essential work.** Remove it and every generated migration is empty.

After `config = context.config`, add:

```python
config.set_main_option("sqlalchemy.url", settings.database_url)
```

Change `target_metadata = None` to:

```python
target_metadata = Base.metadata
```

This is what autogenerate compares the live database against. Left as `None`,
Alembic has no idea what the schema should be.

#### Generate, inspect, apply

```bash
uv run alembic current                                      # no output = nothing applied
uv run alembic revision --autogenerate -m "create spaces table"
```

Autogenerate compares `Base.metadata` to the live database and writes the
difference. It is a **draft, not an oracle**. It reliably detects added and
removed tables and columns. It does **not** reliably detect:

- **renames** — it sees a drop plus an add, which means data loss
- server defaults, some constraint changes, most index details
- anything needing data transformation

**Always read the generated file before applying it.** Expected content for the
first one:

```python
revision: str = "2ea785dfaa7e"
down_revision = None                  # first migration

def upgrade() -> None:
    op.create_table(
        "spaces",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

def downgrade() -> None:
    op.drop_table("spaces")
```

Then:

```bash
uv run alembic upgrade head
```

Verify in Postgres:

```bash
docker exec -it homestock-db psql -U homestock_app -d home_inventory -c "\dt"
docker exec -it homestock-db psql -U homestock_app -d home_inventory -c "\d spaces"
docker exec -it homestock-db psql -U homestock_app -d home_inventory -c "SELECT * FROM alembic_version;"
```

Expect `spaces` **and** `alembic_version`, the right column types, and a
`version_num` matching the migration filename.

#### Test the downgrade path

```bash
uv run alembic downgrade -1      # back one revision
uv run alembic upgrade head      # forward again
```

A migration you cannot reverse is a deploy you cannot roll back. Testing
`downgrade()` is how you discover that autogenerate wrote one that does not
actually work — which happens more than you would like.

#### The reproducibility test

```bash
docker exec -it homestock-db psql -U postgres -d home_inventory \
  -c "DROP TABLE IF EXISTS spaces; DROP TABLE IF EXISTS alembic_version;"

uv run alembic upgrade head
```

A blank database brought to the correct schema by one command, no manual steps.
That is what makes the schema reproducible on a teammate's laptop, in CI, and on
RDS.

#### Gotcha: the empty migration

If autogenerate reports nothing and produces an empty `upgrade()`, `env.py` did
not import your models. `Base.metadata` fills as a **side effect of class
definitions executing** — no import, no classes, no tables in the registry, and
Alembic concludes the database is already correct.

This is the same mechanism as the `list(Base.metadata.tables)` check, now with
consequences.

#### Migration files are source code

Commit `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, and everything
in `alembic/versions/`. They are the history of your schema. `__pycache__/` in
those directories is already covered by `.gitignore`.

---

## Verify

```bash
cd backend    # required — env_file=".env" resolves from the CWD
```

```bash
# config loads
.venv/bin/python -c "from homestock_backend.config import settings; print(settings.database_url)"

# a real query
.venv/bin/python -c "
from sqlalchemy import text
from homestock_backend.database import engine
with engine.connect() as conn:
    print(conn.execute(text('SELECT version()')).scalar())
"

# the model is registered
.venv/bin/python -c "
from homestock_backend.database import Base
import homestock_backend.models
print(list(Base.metadata.tables))
"
```

Expected: your URL, a `PostgreSQL 16.x ...` string, and `['spaces']`.

`text()` is mandatory in SQLAlchemy 2.0 — bare strings are refused, so raw SQL is
explicitly marked and visible in review.

The `import homestock_backend.models` line is load-bearing. `Base.metadata` fills
up as a **side effect of class definitions executing**. Import `Base` alone and
the registry is empty. This is the reason Alembic generates an empty migration,
for everyone, the first time.

### Persistence test

The only thing that proves the volume mount works:

```bash
docker exec -it homestock-db psql -U homestock_app -d home_inventory \
  -c "CREATE TABLE smoke_test (id int); INSERT INTO smoke_test VALUES (1);"

docker restart homestock-db && sleep 5

docker exec -it homestock-db psql -U homestock_app -d home_inventory \
  -c "SELECT * FROM smoke_test;"

docker exec -it homestock-db psql -U homestock_app -d home_inventory \
  -c "DROP TABLE smoke_test;"
```

The row must survive the restart. This also proves the role has `CREATE`, which
Alembic will need.

---

## Failure reference

| Error | Cause |
|---|---|
| `ValidationError: database_url Field required` | not in `backend/` — `.env` not found |
| `connection refused` | container down — `docker ps` |
| `password authentication failed` | `.env` credentials ≠ what was created in psql |
| `ModuleNotFoundError: config` | bare import; needs `homestock_backend.config` |
| `ModuleNotFoundError: psycopg2` | URL says `postgresql://`; needs `postgresql+psycopg://` |
| `Base.metadata.tables` empty | the models module was never imported |
| `port is already allocated` | something owns 5432; use `-p 127.0.0.1:5433:5432` |

---

## Still to do

1. **Switch the routes** — replace `store.py` with database queries via
   `Depends(get_db)`. The endpoints, schemas, and status codes must not change.
   This is a refactor: if route *logic* needs editing, the layers were not as
   separate as they looked.
2. **Verify persistence across app restarts** — create a space, restart uvicorn,
   confirm it is still there. That is the thing the whole phase exists for.
