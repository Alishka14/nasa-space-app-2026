# Handoff: publishing this branch to the team repository

**Why this is needed.** The build session cannot reach `Alishka14/nasa-space-app-2026`: the repository is not in the
session's list of accessible repositories, the GitHub connector refuses it, the `gh` token in the sandbox is not
valid, and `git ls-remote` asks for a username (the repository is private or not shared with this session). Nothing
was pushed and nothing on the remote was changed. The remote's content was not seen.

The branch `feat/earth-senses-mvp` was built in a separate local repository, so it has **no common history** with
the team's `main`. The steps below put it on top of the current `main` with an ordinary merge commit. They never
rewrite history, never force-push, never touch `main`, and never delete a file that is already there.

**Кратко по-русски.** Опубликовать ветку из этой среды нельзя: нет доступа к репозиторию. Ниже — команды для Mac.
Они не делают force-push, не трогают `main` и не удаляют чужие файлы; если путь уже есть в `main`, остаётся версия
команды, а наша кладётся рядом.

## Files you received

| File | What it is |
|---|---|
| `earth-senses-mvp.bundle` | Git bundle with the complete branch `feat/earth-senses-mvp` (all commits, including the earlier eleven) |
| `earth-senses-mvp.zip` | The same working tree without history (fallback only) |

Both routes below were rehearsed against a stand-in repository with its own unrelated `main`, a `README.md` and a
`.gitignore`: the team's files stayed intact and `main` was not touched.

## Step 0 — look before changing anything (both routes)

```bash
cd ~/path/to/nasa-space-app-2026          # your clone of the team repository
git status --short && git remote -v && git branch -a && git log --oneline -5
gh auth status                            # must show an account with write access (Alishka14 or RakamakadoN)
git fetch origin
git fetch ~/Downloads/earth-senses-mvp.bundle feat/earth-senses-mvp:earth-senses-import
git log --oneline earth-senses-import | head -20

# paths that exist both on main and in our branch: the only places where a decision is needed
comm -12 <(git ls-tree -r --name-only origin/main | sort) <(git ls-tree -r --name-only earth-senses-import | sort)
```

Rule for every path that list shows: **the team's version stays**, ours is added beside it under another name.

## Route A — the branch is not on GitHub yet

```bash
git switch -c feat/earth-senses-mvp origin/main
git merge --allow-unrelated-histories --no-ff --no-commit earth-senses-import
git status                                # conflicts can only be the paths listed in step 0
```

If `git status` lists conflicts (most likely `README.md` and `.gitignore`):

```bash
# README.md: keep the team's, add ours beside it
git show earth-senses-import:README.md > EARTH_SENSES_README.md
git checkout --ours -- README.md
git add README.md EARTH_SENSES_README.md

# .gitignore: keep the team's lines and append ours
git checkout --ours -- .gitignore
git show earth-senses-import:.gitignore >> .gitignore
git add .gitignore
```

Then:

```bash
git commit -m "Merge EARTH SENSES MVP on top of main (no files on main changed or removed)"
git diff --name-status origin/main HEAD | grep -v '^A'     # expected: nothing, or only .gitignore
git push -u origin feat/earth-senses-mvp                   # an ordinary push; never --force

gh pr create --draft --base main --head feat/earth-senses-mvp \
  --title "EARTH SENSES MVP: evidence-first trend and relationship investigation" \
  --body-file docs/PR_BODY.md
```

If the repository is empty (no `main` yet): `git push origin earth-senses-import:feat/earth-senses-mvp` and open the
PR after the team has created `main`.

## Route B — an earlier version of the branch is already on GitHub (import kit)

```bash
git switch feat/earth-senses-mvp && git pull --ff-only
git status --short                                         # must be clean
git merge --allow-unrelated-histories --no-ff --no-commit earth-senses-import

# EARTH SENSES directories: take the new version
git checkout --theirs -- backend frontend data scripts docs 2>/dev/null
git add backend frontend data scripts docs
# anything else that still conflicts (README.md, .gitignore): keep what is on the branch
for P in $(git diff --name-only --diff-filter=U); do git checkout --ours -- "$P"; git add "$P"; done
git show earth-senses-import:README.md > EARTH_SENSES_README.md && git add EARTH_SENSES_README.md

git commit -m "Merge EARTH SENSES final delivery"
git diff --stat earth-senses-import HEAD -- backend frontend data scripts docs   # expected: no output
git push origin feat/earth-senses-mvp
gh pr create --draft --base main --head feat/earth-senses-mvp \
  --title "EARTH SENSES MVP: evidence-first trend and relationship investigation" \
  --body-file docs/PR_BODY.md                              # skip if the PR already exists
```

If step 0 showed team-owned files inside `backend`, `frontend`, `data`, `scripts` or `docs`, restore each of them
after the `--theirs` line with `git checkout --ours -- <path>` before committing.

## After pushing

1. `python scripts/build_provenance.py` — prints `OK` four times.
2. `(cd backend && python -m pytest)` — `160 passed` with `requirements-dev.txt` (`151 passed, 9 skipped` without `pymannkendall`).
3. Start the backend **without** `EARTH_SENSES_OFFLINE` and investigate a place that is not bundled (for example
   Astana). This is the first live request the backend makes to NASA; watch it once and note the result in the PR.
4. Make the repository public before submitting: the submission form requires a link that opens without login.
5. Do **not** merge the PR into `main` without the team's decision.
