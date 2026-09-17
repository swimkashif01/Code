## Architecture Summary

This is a small **Python 3 CLI expense tracker** — no web framework or server, just stdlib + JSON file storage.

**Layout:**
- `cli/cli.py` — entry point. Uses `argparse` for subcommands (`add`, `list`, `total`, `delete`), formats output, delegates all logic to `core`.
- `core/expense_tracker.py` — business logic: `add_expense`, `list_expenses`, `get_total`, `delete_expense`. Persists to `core/expenses.json`. Validates inputs (non-empty description/category, positive amount, valid id) and treats missing/corrupt JSON as an empty store.
- `tests/` — pytest suite (`test_expense_tracker.py`, `conftest.py`) covering happy paths, validation errors, id semantics, case-insensitive filtering, and corrupted-file recovery. Each test isolates its own temp data file.
- `requirements.txt` — a dev-environment freeze (pytest, Jupyter tooling, numpy, requests, etc.); only `pytest` is actually used by the app.
- `architecture.md` — present but empty; no doc exists yet.
- `.claude/` — Claude Code harness config plus two leftover agent worktrees, unrelated to the app itself.

**Flow:** `python cli/cli.py <command> ...` → `argparse` dispatches to a `cmd_*` handler → calls into `core.expense_tracker`, which loads/mutates/persists `expenses.json`. Clean two-layer separation: **cli** (presentation) → **core** (logic + persistence), no external services.

Want me to write this up into the empty `architecture.md` file?
