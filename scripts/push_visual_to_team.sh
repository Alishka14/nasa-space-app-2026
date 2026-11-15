#!/usr/bin/env bash
# Brings the visual module from the development repo (remote "dev" = RakamakadoN/earth-senses) into the team repo
# (remote "origin" = Alishka14/nasa-space-app-2026) as a new branch and opens a Draft PR. Run it in your clone of the
# team repo on your own computer:
#
#   bash push_visual_to_team.sh            # dry run: shows what it would do, changes nothing
#   bash push_visual_to_team.sh --go       # creates the branch, pushes it (no force) and opens the Draft PR
#
# It never force-pushes, never touches main, and stops at the first conflict.
set -euo pipefail

BRANCH=feat/visual-onboarding
MVP=e13fb9b974ff0d6cb76a1a063a4a447c61e55adb     # the MVP merge commit, already in the team's main
GO=${1:-}
say() { printf '\n== %s\n' "$*"; }

git remote get-url origin | grep -q 'Alishka14/nasa-space-app-2026' || { echo "origin is not the team repo"; exit 1; }
git remote get-url dev    | grep -q 'RakamakadoN/earth-senses'      || { echo "add it first: git remote add dev https://github.com/RakamakadoN/earth-senses.git"; exit 1; }
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then echo "commit or stash your changes first"; exit 1; fi

say "Fetching"
git fetch origin
git fetch dev

say "Team main and dev main"
git log --oneline -3 origin/main
git log --oneline -3 dev/main
if git merge-base --is-ancestor "$MVP" origin/main; then
  ROUTE=merge
  say "The MVP commit is in team main (merged with a merge commit) — will merge dev/main into a new branch"
else
  ROUTE=pick
  say "The MVP commit is not in team main (squash or rebase merge) — will copy only the new commits"
fi
NEW=$(git rev-list --reverse --no-merges "$MVP"..dev/main)
echo "New commits from dev/main (authorship is kept):"
for c in $NEW; do git log -1 --format='  %h %an  %s' "$c"; done
[ -n "$NEW" ] || { echo "nothing new on dev/main — merge PR #1 in RakamakadoN/earth-senses first"; exit 1; }
if git show-ref --quiet "refs/remotes/origin/$BRANCH"; then echo "origin/$BRANCH already exists — stop"; exit 1; fi

if [ "$GO" != "--go" ]; then
  say "Dry run only. Run again with --go to create $BRANCH, push it and open the Draft PR."
  exit 0
fi

say "Creating $BRANCH from origin/main"
git switch -c "$BRANCH" origin/main
if [ "$ROUTE" = merge ]; then
  git merge --no-ff --no-edit dev/main -m "Merge visual onboarding from RakamakadoN/earth-senses" \
    || { echo "Conflict. Undo with: git merge --abort && git switch - && git branch -D $BRANCH"; exit 1; }
else
  git cherry-pick -x $NEW \
    || { echo "Conflict. Undo with: git cherry-pick --abort && git switch - && git branch -D $BRANCH"; exit 1; }
fi

say "Check before pushing"
git diff --stat origin/main..HEAD | tail -5
git diff --name-only --diff-filter=D origin/main..HEAD | sed 's/^/  DELETED: /' || true

say "Pushing (no force)"
git push -u origin "$BRANCH"

say "Opening the Draft PR"
git show "dev/main:docs/PR_BODY_VISUAL.md" > /tmp/pr_body_visual.md
gh pr create --draft --repo Alishka14/nasa-space-app-2026 --base main --head "$BRANCH" \
  --title "Visual module: 3D Earth onboarding and intro films (EN/RU/KK)" --body-file /tmp/pr_body_visual.md
