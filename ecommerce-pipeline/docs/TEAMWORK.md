# Git workflow (stage 4)

## Rules
1. `main` is protected: **no direct pushes**. Everything goes through a Pull Request (PR).
2. Branch from an up-to-date `main`: `feature/<topic>` (e.g. `feature/api-extract`).
3. Small commits with clear messages: `Add retry logic to API client`.
4. Every PR needs **at least one teammate's review/approval** before merging (use "Squash and merge").
5. Reviewers comment on correctness, readability, tests; the author replies/fixes in the same branch.

## Setup (one person, once)
```bash
git init && git add . && git commit -m "Initial project skeleton"
git branch -M main
git remote add origin https://github.com/<team>/ecommerce-pipeline.git
git push -u origin main
```
GitHub → Settings → Branches → add rule for `main`: *Require a pull request before merging*, *Require 1 approval*.
Settings → Collaborators → add the other members.

## Daily cycle
```bash
git checkout main && git pull
git checkout -b feature/clean-sales
# ...work...
git add -A && git commit -m "Add price imputation"
git push -u origin feature/clean-sales      # then open a PR on GitHub
```

## Suggested split (3 students)
| Member | Branch(es) | PR contents |
|---|---|---|
| A | `feature/api-extract`, `feature/readme` | `extract_products.py`, config, README |
| B | `feature/sales-generator`, `feature/clean-sales` | `generate_sales.py`, `clean_sales.py`, tests |
| C | `feature/db-schema`, `feature/load-db` | `schema.sql`, `load_db.py`, `queries.sql`, docker-compose |

For 2 students, B takes sales + tests, and A takes everything else. Each member **reviews the other's PRs**
(A reviews B, B reviews C, C reviews A) so the history shows real code-review comments, requested changes and approvals.
Start with the PRs in order: A → B → C, as C needs the Parquet and CSV files.

## Evidence for assessors
Take screenshots of: the merged PR list, one PR with review comments, the commit graph (Insights → Network), and the branch protection rule.
