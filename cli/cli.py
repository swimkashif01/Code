#!/usr/bin/env python3
"""Command-line interface for the expense tracker application.

This module is intentionally kept import-path independent: it locates the
sibling ``core`` directory relative to its own file location (not the
caller's current working directory) and adds it to ``sys.path`` before
importing the core engine module.
"""

import argparse
import os
import sys

# Make the sibling ../core directory importable regardless of the caller's
# current working directory.
_CORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core")
sys.path.insert(0, os.path.normpath(_CORE_DIR))

import expense_tracker  # noqa: E402  (import must follow sys.path setup)


def format_money(amount: float) -> str:
    """Format a numeric amount as a dollar string with 2 decimal places."""
    return "${:.2f}".format(amount)


def cmd_add(args: argparse.Namespace) -> None:
    expense = expense_tracker.add_expense(args.description, args.amount, args.category)
    print(
        "Added expense #{id}: {description} - {amount} ({category})".format(
            id=expense["id"],
            description=expense["description"],
            amount=format_money(expense["amount"]),
            category=expense["category"],
        )
    )


def cmd_list(args: argparse.Namespace) -> None:
    expenses = expense_tracker.list_expenses(category=args.category)

    if not expenses:
        if args.category:
            print("No expenses found in category '{}'.".format(args.category))
        else:
            print("No expenses found.")
        return

    id_width = max(len("ID"), max(len(str(e["id"])) for e in expenses))
    desc_width = max(len("Description"), max(len(e["description"]) for e in expenses))
    amount_strs = [format_money(e["amount"]) for e in expenses]
    amount_width = max(len("Amount"), max(len(a) for a in amount_strs))
    category_width = max(len("Category"), max(len(e["category"]) for e in expenses))

    header = "{id:<{id_w}}  {desc:<{desc_w}}  {amount:<{amount_w}}  {category:<{category_w}}".format(
        id="ID",
        id_w=id_width,
        desc="Description",
        desc_w=desc_width,
        amount="Amount",
        amount_w=amount_width,
        category="Category",
        category_w=category_width,
    )
    print(header)
    print("-" * len(header))

    for expense, amount_str in zip(expenses, amount_strs):
        print(
            "{id:<{id_w}}  {desc:<{desc_w}}  {amount:<{amount_w}}  {category:<{category_w}}".format(
                id=expense["id"],
                id_w=id_width,
                desc=expense["description"],
                desc_w=desc_width,
                amount=amount_str,
                amount_w=amount_width,
                category=expense["category"],
                category_w=category_width,
            )
        )


def cmd_total(args: argparse.Namespace) -> None:
    total = expense_tracker.get_total(category=args.category)
    if args.category:
        print("Total for category '{}': {}".format(args.category, format_money(total)))
    else:
        print("Total: {}".format(format_money(total)))


def cmd_delete(args: argparse.Namespace) -> None:
    deleted = expense_tracker.delete_expense(args.expense_id)
    if deleted:
        print("Deleted expense #{}.".format(args.expense_id))
    else:
        print("No expense found with id {}.".format(args.expense_id))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="A simple command-line expense tracker.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new expense.")
    add_parser.add_argument("description", type=str, help="Description of the expense.")
    add_parser.add_argument("amount", type=float, help="Amount of the expense.")
    add_parser.add_argument("category", type=str, help="Category of the expense.")
    add_parser.set_defaults(func=cmd_add)

    list_parser = subparsers.add_parser("list", help="List expenses.")
    list_parser.add_argument(
        "--category", type=str, default=None, help="Filter expenses by category."
    )
    list_parser.set_defaults(func=cmd_list)

    total_parser = subparsers.add_parser("total", help="Show the total of expenses.")
    total_parser.add_argument(
        "--category", type=str, default=None, help="Filter total by category."
    )
    total_parser.set_defaults(func=cmd_total)

    delete_parser = subparsers.add_parser("delete", help="Delete an expense by id.")
    delete_parser.add_argument("expense_id", type=int, help="ID of the expense to delete.")
    delete_parser.set_defaults(func=cmd_delete)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        args.func(args)
    except ValueError as exc:
        print("Error: {}".format(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
