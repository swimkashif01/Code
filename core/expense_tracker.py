"""Core expense tracking engine.

Stores expenses in a JSON file (core/expenses.json) located next to this
module, so it works regardless of the current working directory. Intended
to be imported by a separate CLI module and exercised by a separate test
suite.
"""

import json
import os
from numbers import Number
from typing import List, Optional

_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.json")


def _load_expenses() -> List[dict]:
    """Load expenses from the JSON data file.

    Returns an empty list if the file doesn't exist, is empty, or contains
    invalid/corrupted JSON.
    """
    if not os.path.exists(_DATA_FILE):
        return []

    try:
        with open(_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(data, list):
        return []

    return data


def _save_expenses(expenses: List[dict]) -> None:
    """Persist the given list of expenses to the JSON data file."""
    with open(_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(expenses, f, indent=2)


def _coerce_int(value) -> int:
    """Coerce an int-like value (int, whole float, numeric string) to int.

    Raises ValueError if value cannot be treated as an integer id.
    """
    if isinstance(value, bool):
        raise ValueError("expense_id must be an int")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    raise ValueError("expense_id must be an int")


def add_expense(description: str, amount: float, category: str) -> dict:
    """Validate inputs and add a new expense, returning the created record."""
    if not isinstance(description, str) or not description.strip():
        raise ValueError("description must be a non-empty string")

    if isinstance(amount, bool) or not isinstance(amount, Number):
        raise ValueError("amount must be a positive number")
    if amount <= 0:
        raise ValueError("amount must be a positive number")

    if not isinstance(category, str) or not category.strip():
        raise ValueError("category must be a non-empty string")

    expenses = _load_expenses()
    next_id = max((e.get("id", 0) for e in expenses), default=0) + 1

    expense = {
        "id": next_id,
        "description": description.strip(),
        "amount": float(amount),
        "category": category.strip(),
    }

    expenses.append(expense)
    _save_expenses(expenses)

    return expense


def list_expenses(category: Optional[str] = None) -> List[dict]:
    """Return all expenses, or only those matching category (case-insensitive)."""
    expenses = _load_expenses()

    if category is None:
        return expenses

    category_lower = category.lower()
    return [e for e in expenses if str(e.get("category", "")).lower() == category_lower]


def get_total(category: Optional[str] = None) -> float:
    """Return the sum of expense amounts, optionally filtered by category."""
    expenses = list_expenses(category)
    return sum(e.get("amount", 0.0) for e in expenses) if expenses else 0.0


def delete_expense(expense_id: int) -> bool:
    """Delete the expense with the given id. Returns True if deleted."""
    expense_id = _coerce_int(expense_id)

    expenses = _load_expenses()
    remaining = [e for e in expenses if e.get("id") != expense_id]

    if len(remaining) == len(expenses):
        return False

    _save_expenses(remaining)
    return True
