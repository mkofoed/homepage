#!/usr/bin/env bash
#
# Apply branch protection to main. Run once, from anywhere in the repo:
#
#     ./scripts/setup-branch-protection.sh
#
# Requires the GitHub CLI authenticated as a repo admin (`gh auth login`).
# Safe to re-run: the API call replaces the rule rather than appending to it,
# so this is the single source of truth for what main requires.
#
# Note: on a private repository, branch protection needs a paid GitHub plan.
# Public repositories have it on the free plan.
set -euo pipefail

command -v gh >/dev/null 2>&1 || {
  echo "error: gh is not installed — see https://cli.github.com" >&2
  exit 1
}
gh auth status >/dev/null 2>&1 || {
  echo "error: gh is not authenticated — run 'gh auth login'" >&2
  exit 1
}

repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
echo "Applying branch protection to ${repo}:main"

# The three contexts below are the `name:` values of the jobs in
# .github/workflows/ci.yml. Rename a job there and the rule silently stops
# requiring it, so change both together.
if ! gh api -X PUT "repos/${repo}/branches/main/protection" --input - >/dev/null <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Lint, type check, and test",
      "Tailwind build is committed",
      "Production Compose file is valid"
    ]
  },
  "required_pull_request_reviews": { "required_approving_review_count": 0 },
  "enforce_admins": false,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
then
  echo >&2
  echo "error: GitHub rejected the request. Common causes:" >&2
  echo "  - the token lacks admin rights on ${repo}" >&2
  echo "  - the repository is private on a plan without branch protection" >&2
  exit 1
fi

echo "Applied. Current rule:"
gh api "repos/${repo}/branches/main/protection" --jq '
  "  required checks    : " + (.required_status_checks.contexts | join(", ")),
  "  strict (up to date): " + (.required_status_checks.strict | tostring),
  "  PR required        : " + ((.required_pull_request_reviews != null) | tostring),
  "  enforce admins     : " + (.enforce_admins.enabled | tostring),
  "  force pushes       : " + (.allow_force_pushes.enabled | tostring),
  "  deletions          : " + (.allow_deletions.enabled | tostring)'
