# Phase 1 — Git, GitHub, and Repository Structure

## What exists at the end

A GitHub repository cloned locally, containing a monorepo folder structure, a
`.gitignore`, and a README — all of it landed through a full
issue → branch → commit → push → pull request → review → merge cycle rather than
committed straight to `main`.

---

## Concepts

### The four places your code lives

```text
Working Directory      files as they are on disk right now
        │ git add
        ▼
Staging Area (index)   changes you have selected for the next commit
        │ git commit
        ▼
Local Repository       the commit history on your machine
        │ git push
        ▼
Remote Repository      the commit history on GitHub
```

**Why a staging area exists.** It lets you commit *some* of your changes and not
others. You may have fixed a bug and started an unrelated experiment in the same
file; staging lets the commit contain only the bug fix. Without it, every commit
would be "everything I have touched since last time."

### What a commit actually is

A commit is a **full snapshot** of every tracked file, plus a pointer to its
parent commit. Not a diff — Git computes diffs on demand for display, but stores
snapshots.

Because a commit's hash is derived from its content (including its message and
its parent), **commits are immutable**. Changing anything produces a different
commit with a different hash. This is why `git commit --amend` does not edit a
commit; it builds a new one and moves your branch pointer to it.

A commit is also **not a backup**. It lives only on your machine until you push.

### `origin`

`origin` is just a name — an alias for a remote URL, created automatically when
you clone. Nothing is special about the word; `git remote rename origin github`
works fine, you would just then type `git push github main`.

### `git fetch` is not `git pull`

This one causes real confusion.

```text
git fetch    updates ONLY the remote-tracking pointer origin/main
             your local main does NOT move

git merge origin/main   moves your local main forward

git pull     = fetch + merge, in one command
```

After a fetch you have two separate refs:

```text
main         → old commit   (yours, unchanged)
origin/main  → new commit   (what GitHub has)
```

Knowing they are separate is useful: you can fetch, inspect what is incoming with
`git log main..origin/main`, and *then* decide whether to merge.

### `.gitignore` and secrets

`.gitignore` prevents Git from tracking files it is **not already tracking**.

It has no effect on a file that is already tracked. If you commit `.env` and then
add it to `.gitignore`, Git keeps tracking it. You need:

```bash
git rm --cached .env
```

And critically: **a committed secret is not made safe by deleting it later.** The
value sits in an old commit object; anyone who clones can check out that commit
and read it. Removing it means rewriting history (`git filter-repo`, BFG). If it
was ever pushed to a public remote, assume it was scraped and **rotate the
credential**.

> Rule: prevent secrets from entering a commit at all. A leaked secret is a
> rotation problem, not a Git problem.

---

## Steps

### 1. Create and clone

Create the repository on GitHub, then:

```bash
git clone https://github.com/<user>/homestock.git
cd homestock
```

### 2. Create an issue, then a branch

Every meaningful change starts as a GitHub issue, then a branch named after it:

```bash
git checkout -b chore/1-project-structure
```

Branch prefixes: `feature/`, `fix/`, `test/`, `docs/`, `refactor/`, `chore/`.
Include the issue number so the branch is traceable to its discussion.

### 3. Create the structure

```text
homestock/
├── .github/
├── backend/
├── docs/
├── frontend/
├── infrastructure/
├── .gitignore
├── CLAUDE.md
├── LICENSE
└── README.md
```

Git tracks files, not directories, so an empty folder cannot be committed. Put a
`.gitkeep` (an empty placeholder file, no special meaning to Git) in each empty
directory.

### 4. `.gitignore`

Must cover at minimum:

```text
.venv/
venv/
__pycache__/
*.pyc
.env
*.env
node_modules/
.DS_Store
.vscode/
```

Add this **before** the first commit. It is much easier than removing files later.

### 5. Commit

```bash
git status          # what changed
git diff            # what exactly changed
git add .
git commit -m "chore: set up initial project structure"
```

Conventional Commit prefixes: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`,
`chore:`. Avoid `update`, `stuff`, `changes`, `fix again`.

### 6. Push and open a pull request

```bash
git push -u origin chore/1-project-structure
```

`-u` sets the upstream so later pushes are just `git push`.

Open the PR on GitHub, **read the Files Changed tab yourself**, then merge.

### 7. Update local main

```bash
git checkout main
git pull
git branch -d chore/1-project-structure
```

Merging on GitHub does not touch your local `main`. This is the fetch-vs-pull
concept in practice.

---

## Gotchas

**Amending an already-pushed commit** puts you in a diverged state:

```text
## branch...origin/branch [ahead 1, behind 1]
```

You have one commit the remote does not; the remote has one you do not. They are
siblings, not a line, so a normal push is rejected. Fix:

```bash
git push --force-with-lease
```

Use `--force-with-lease`, never bare `--force`. With-lease refuses the push if
the remote moved since your last fetch, so you cannot silently destroy someone
else's work.

> Rewrite history freely **before** it is shared. Never after.
> Never force-push `main` or any branch someone else has pulled.

**Merged branches linger on the remote.** Delete them, or turn on
GitHub → Settings → General → *Automatically delete head branches*.

---

## Verify

```bash
git log --oneline --graph      # merge commits visible, history readable
git status                     # clean
git status --short             # no .env, no .venv, no __pycache__
```
