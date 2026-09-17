"""Pytest suite for core/expense_tracker.py.

Covers happy paths for all four public functions, input validation edge
cases, corrupted/missing data file handling, case-insensitive category
filtering, and delete semantics (including double-delete and deleting a
nonexistent id).

Isolation: every test gets its own temporary data file via the autouse
``isolated_data_file`` fixture, which monkeypatches the module's private
``_DATA_FILE`` path so the real core/expenses.json (potentially used by a
CLI or another process) is never touched.
"""

import json

import pytest

import expense_tracker


@pytest.fixture(autouse=True)
def isolated_data_file(tmp_path, monkeypatch):
    """Redirect the module's data file to a fresh temp path for each test."""
    data_file = tmp_path / "expenses.json"
    monkeypatch.setattr(expense_tracker, "_DATA_FILE", str(data_file))
    return data_file


# ---------------------------------------------------------------------------
# Happy path: add_expense
# ---------------------------------------------------------------------------


def test_add_expense_returns_expected_fields():
    expense = expense_tracker.add_expense("Coffee", 4.5, "Food")

    assert expense["id"] == 1
    assert expense["description"] == "Coffee"
    assert expense["amount"] == pytest.approx(4.5)
    assert expense["category"] == "Food"


def test_add_expense_ids_increment():
    first = expense_tracker.add_expense("Coffee", 4.5, "Food")
    second = expense_tracker.add_expense("Bus ticket", 2.0, "Transport")
    third = expense_tracker.add_expense("Movie", 12.0, "Entertainment")

    assert [first["id"], second["id"], third["id"]] == [1, 2, 3]


def test_add_expense_persists_to_data_file(isolated_data_file):
    expense_tracker.add_expense("Coffee", 4.5, "Food")

    assert isolated_data_file.exists()
    on_disk = json.loads(isolated_data_file.read_text(encoding="utf-8"))
    assert len(on_disk) == 1
    assert on_disk[0]["description"] == "Coffee"


def test_add_expense_ids_never_reused_after_deletion():
    expense_tracker.add_expense("A", 1.0, "Food")
    second = expense_tracker.add_expense("B", 2.0, "Food")
    expense_tracker.add_expense("C", 3.0, "Food")

    expense_tracker.delete_expense(second["id"])
    fourth = expense_tracker.add_expense("D", 4.0, "Food")

    assert fourth["id"] == 4
    ids = [e["id"] for e in expense_tracker.list_expenses()]
    assert second["id"] not in ids


# ---------------------------------------------------------------------------
# Happy path: list_expenses
# ---------------------------------------------------------------------------


def test_list_expenses_empty_by_default():
    assert expense_tracker.list_expenses() == []


def test_list_expenses_returns_all_when_no_filter():
    expense_tracker.add_expense("Coffee", 4.5, "Food")
    expense_tracker.add_expense("Bus ticket", 2.0, "Transport")

    result = expense_tracker.list_expenses()

    assert len(result) == 2
    descriptions = {e["description"] for e in result}
    assert descriptions == {"Coffee", "Bus ticket"}


def test_list_expenses_filters_by_category():
    expense_tracker.add_expense("Coffee", 4.5, "Food")
    expense_tracker.add_expense("Bus ticket", 2.0, "Transport")
    expense_tracker.add_expense("Lunch", 10.0, "Food")

    result = expense_tracker.list_expenses("Food")

    assert len(result) == 2
    assert {e["description"] for e in result} == {"Coffee", "Lunch"}


def test_list_expenses_filter_case_insensitive():
    expense_tracker.add_expense("Coffee", 4.5, "Food")

    assert len(expense_tracker.list_expenses("food")) == 1
    assert len(expense_tracker.list_expenses("FOOD")) == 1
    assert len(expense_tracker.list_expenses("FoOd")) == 1


def test_list_expenses_filter_no_match_returns_empty_list():
    expense_tracker.add_expense("Coffee", 4.5, "Food")

    assert expense_tracker.list_expenses("Nonexistent") == []


# ---------------------------------------------------------------------------
# Happy path: get_total
# ---------------------------------------------------------------------------


def test_get_total_empty_is_zero():
    assert expense_tracker.get_total() == 0.0


def test_get_total_sums_all_without_filter():
    expense_tracker.add_expense("Coffee", 4.5, "Food")
    expense_tracker.add_expense("Bus ticket", 2.5, "Transport")

    assert expense_tracker.get_total() == pytest.approx(7.0)


def test_get_total_sums_with_category_filter():
    expense_tracker.add_expense("Coffee", 4.5, "Food")
    expense_tracker.add_expense("Lunch", 10.5, "Food")
    expense_tracker.add_expense("Bus ticket", 2.0, "Transport")

    assert expense_tracker.get_total("Food") == pytest.approx(15.0)


def test_get_total_filter_case_insensitive():
    expense_tracker.add_expense("Coffee", 4.5, "Food")

    assert expense_tracker.get_total("food") == pytest.approx(4.5)


def test_get_total_no_match_is_zero():
    expense_tracker.add_expense("Coffee", 4.5, "Food")

    assert expense_tracker.get_total("Nonexistent") == 0.0


# ---------------------------------------------------------------------------
# Happy path: delete_expense
# ---------------------------------------------------------------------------


def test_delete_expense_removes_correct_record_and_returns_true():
    first = expense_tracker.add_expense("Coffee", 4.5, "Food")
    second = expense_tracker.add_expense("Bus ticket", 2.0, "Transport")

    result = expense_tracker.delete_expense(first["id"])

    assert result is True
    remaining = expense_tracker.list_expenses()
    assert len(remaining) == 1
    assert remaining[0]["id"] == second["id"]


def test_delete_expense_id_no_longer_listed():
    expense = expense_tracker.add_expense("Coffee", 4.5, "Food")

    expense_tracker.delete_expense(expense["id"])

    ids = [e["id"] for e in expense_tracker.list_expenses()]
    assert expense["id"] not in ids


def test_delete_nonexistent_id_returns_false():
    expense_tracker.add_expense("Coffee", 4.5, "Food")

    assert expense_tracker.delete_expense(999) is False


def test_delete_on_empty_store_returns_false():
    assert expense_tracker.delete_expense(1) is False


def test_delete_same_id_twice_second_call_returns_false():
    expense = expense_tracker.add_expense("Coffee", 4.5, "Food")

    assert expense_tracker.delete_expense(expense["id"]) is True
    assert expense_tracker.delete_expense(expense["id"]) is False


# ---------------------------------------------------------------------------
# Validation: description
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_description", ["", "   ", "\t\n"])
def test_add_expense_rejects_empty_or_whitespace_description(bad_description):
    with pytest.raises(ValueError):
        expense_tracker.add_expense(bad_description, 10.0, "Food")


@pytest.mark.parametrize("bad_description", [123, None, 12.5, [], {}, True])
def test_add_expense_rejects_non_string_description(bad_description):
    with pytest.raises(ValueError):
        expense_tracker.add_expense(bad_description, 10.0, "Food")


# ---------------------------------------------------------------------------
# Validation: amount
# ---------------------------------------------------------------------------


def test_add_expense_rejects_zero_amount():
    with pytest.raises(ValueError):
        expense_tracker.add_expense("Coffee", 0, "Food")


@pytest.mark.parametrize("bad_amount", [-1, -0.01, -100])
def test_add_expense_rejects_negative_amount(bad_amount):
    with pytest.raises(ValueError):
        expense_tracker.add_expense("Coffee", bad_amount, "Food")


@pytest.mark.parametrize("bad_amount", ["10", None, [], {}, "abc"])
def test_add_expense_rejects_non_numeric_amount(bad_amount):
    with pytest.raises(ValueError):
        expense_tracker.add_expense("Coffee", bad_amount, "Food")


# ---------------------------------------------------------------------------
# Validation: category
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_category", ["", "   ", "\t\n"])
def test_add_expense_rejects_empty_or_whitespace_category(bad_category):
    with pytest.raises(ValueError):
        expense_tracker.add_expense("Coffee", 10.0, bad_category)


@pytest.mark.parametrize("bad_category", [123, None, 12.5, [], {}, True])
def test_add_expense_rejects_non_string_category(bad_category):
    with pytest.raises(ValueError):
        expense_tracker.add_expense("Coffee", 10.0, bad_category)


def test_add_expense_validation_failure_does_not_persist(isolated_data_file):
    with pytest.raises(ValueError):
        expense_tracker.add_expense("", 10.0, "Food")

    assert expense_tracker.list_expenses() == []


# ---------------------------------------------------------------------------
# Validation: delete_expense id type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_id", ["abc", 1.5, None, [], {}, True])
def test_delete_expense_rejects_non_int_like_id(bad_id):
    with pytest.raises(ValueError):
        expense_tracker.delete_expense(bad_id)


def test_delete_expense_accepts_numeric_string_id():
    expense = expense_tracker.add_expense("Coffee", 4.5, "Food")

    assert expense_tracker.delete_expense(str(expense["id"])) is True
    assert expense_tracker.list_expenses() == []


def test_delete_expense_accepts_whole_float_id():
    expense = expense_tracker.add_expense("Coffee", 4.5, "Food")

    assert expense_tracker.delete_expense(float(expense["id"])) is True
    assert expense_tracker.list_expenses() == []


# ---------------------------------------------------------------------------
# File corruption / missing file handling
# ---------------------------------------------------------------------------


def test_missing_data_file_treated_as_empty(isolated_data_file):
    assert not isolated_data_file.exists()
    assert expense_tracker.list_expenses() == []
    assert expense_tracker.get_total() == 0.0


def test_corrupted_json_list_expenses_returns_empty(isolated_data_file):
    isolated_data_file.write_text("{not valid json !!! [[[", encoding="utf-8")

    assert expense_tracker.list_expenses() == []


def test_corrupted_json_get_total_is_zero(isolated_data_file):
    isolated_data_file.write_text("not json at all", encoding="utf-8")

    assert expense_tracker.get_total() == 0.0


def test_corrupted_json_add_expense_still_works(isolated_data_file):
    isolated_data_file.write_text("}}} garbage {{{", encoding="utf-8")

    expense = expense_tracker.add_expense("Coffee", 3.5, "Food")

    assert expense["id"] == 1
    assert expense_tracker.list_expenses() == [expense]


def test_non_list_json_treated_as_empty(isolated_data_file):
    isolated_data_file.write_text(json.dumps({"not": "a list"}), encoding="utf-8")

    assert expense_tracker.list_expenses() == []


def test_empty_file_treated_as_empty(isolated_data_file):
    isolated_data_file.write_text("", encoding="utf-8")

    assert expense_tracker.list_expenses() == []
