# Handoff: getting this branch into the team repository

The build session could not reach `Alishka14/nasa-space-app-2026`, so the branch `feat/earth-senses-mvp` was built in a
fresh local repository. It shares no history with the remote and the remote's current content was not seen. Nothing
was pushed; nothing on the remote was changed.

## Option A — from the bundle (keeps the commit history)

```bash
git clone https://github.com/Alishka14/nasa-space-app-2026 && cd nasa-space-app-2026
git fetch /path/to/earth-senses-mvp.bundle feat/earth-senses-mvp:earth-senses-import

# put the commits on top of the remote default branch (replace main if it is named differently)
git checkout -b feat/earth-senses-mvp origin/main
git cherry-pick $(git rev-list --reverse earth-senses-import)
# if a file already exists on main with the same path, git stops: resolve by keeping the team's file
# or merging by hand, then `git cherry-pick --continue`. Do not force anything.

git push -u origin feat/earth-senses-mvp          # then open a pull request; do not merge without the team
```

If the remote repository is empty, `git push origin earth-senses-import:feat/earth-senses-mvp` is enough.

## Option B — from the zip (one commit)

Unzip over a clone on a new branch `feat/earth-senses-mvp`, review `git status`, commit, push, open a pull request.

## After pushing

1. `python scripts/build_provenance.py` — must print `OK` three times (SHA-256 of the NASA files).
2. `cd backend && python -m pytest` — 126 tests.
3. Start the backend without `EARTH_SENSES_OFFLINE` and investigate a place that is not bundled (for example Astana).
   This is the first live request the backend makes to NASA; watch it once.
4. Work through "Not done" in `KNOWN_LIMITATIONS.md`, starting with a data source from the challenge's Resources tab.
