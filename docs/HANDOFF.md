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
| `earth-senses-mvp.bundle` | Git bundle with the complete branch `feat/earth-senses-mvp` (all commits) |
| `earth-senses-final-delivery.mbox` | Only the FINAL DELIVERY commits, as patches — for the case where the first 11 commits are already on GitHub |
| `earth-senses-mvp.zip` | The working tree without history (fallback) |

## Route A — the branch is not on GitHub yet

```bash
# 0. look before changing anything
cd ~/path/to/nasa-space-app-2026          # your clone of the team repository
git status --short && git remote -v && git branch -a && git log --oneline -5
gh auth status                            # must show an account with write access (Alishka14 or RakamakadoN)

# 1. import the branch from the bundle under a temporary name
git fetch origin
git fetch ~/Downloads/earth-senses-mvp.bundle feat/earth-senses-mvp:earth-senses-import
git log --oneline earth-senses-import | head -20

# 2. start the public branch from the team's current main and merge ours into it
git switch -c feat/earth-senses-mvp origin/main
git merge --allow-unrelated-histories --no-ff --no-commit earth-senses-import
git status                                # conflicts can only be paths that exist on both sides
```

If `git status` lists conflicts (most likely `README.md` or `.gitignore`), keep the team's file and add ours beside
it. Do this for each conflicted path:

```bash
# example for README.md
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
git diff --stat origin/main...HEAD | tail -3      # review: additions only
git push -u origin feat/earth-senses-mvp          # an ordinary push; never --force

gh pr create --draft --base main --head feat/earth-senses-mvp \
  --title "EARTH SENSES MVP: evidence-first trend and relationship investigation" \
  --body-file docs/PR_BODY.md
```

If the repository is empty (no `main` yet): `git push origin earth-senses-import:feat/earth-senses-mvp` and open the
PR after the team has created `main`.

## Route B — the first 11 commits were already published with the import kit

```bash
cd ~/path/to/nasa-space-app-2026
git fetch origin && git switch feat/earth-senses-mvp && git pull --ff-only
git status --short                                 # must be clean
git am ~/Downloads/earth-senses-final-delivery.mbox
git push origin feat/earth-senses-mvp
gh pr create --draft --base main --head feat/earth-senses-mvp \
  --title "EARTH SENSES MVP: evidence-first trend and relationship investigation" \
  --body-file docs/PR_BODY.md                      # skip if the PR already exists
```

If `git am` stops, run `git am --abort` (the branch returns to its previous state) and use Route A into a new branch
name such as `feat/earth-senses-final`, then open the PR from that branch.

## After pushing

1. `python scripts/build_provenance.py` — prints `OK` four times.
2. `(cd backend && python -m pytest)` — `160 passed` with `requirements-dev.txt`.
3. Start the backend **without** `EARTH_SENSES_OFFLINE` and investigate a place that is not bundled (for example
   Astana). This is the first live request the backend makes to NASA; watch it once and note the result in the PR.
4. Make the repository public before submitting: the submission form requires a link that opens without login.
5. Do **not** merge the PR into `main` without the team's decision.
