import sqlite3
import unittest

from app import store


def make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    store.init_db(conn)
    return conn


def sample(amount=100.0, category="food", date="2026-11-01", description="x"):
    return {"amount": amount, "category": category, "description": description, "date": date}


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()

    def tearDown(self):
        self.conn.close()

    def test_create_and_get(self):
        created = store.create_expense(self.conn, sample(250.5, "travel"))
        self.assertEqual(created["amount"], 250.5)
        self.assertEqual(store.get_expense(self.conn, created["id"])["category"], "travel")

    def test_get_missing_returns_none(self):
        self.assertIsNone(store.get_expense(self.conn, 999))
            
    def test_total_with_and_without_filter(self):
        store.create_expense(self.conn, sample(100, "food"))
        store.create_expense(self.conn, sample(50.5, "food"))
        store.create_expense(self.conn, sample(300, "rent"))
        self.assertEqual(store.total_expenses(self.conn), {"total": 450.5, "count": 3})
        self.assertEqual(store.total_expenses(self.conn, category="food"), {"total": 150.5, "count": 2})

    def test_total_on_empty_table_is_zero(self):
        self.assertEqual(store.total_expenses(self.conn), {"total": 0.0, "count": 0})

    def test_list_filters_by_category_and_dates(self):
        store.create_expense(self.conn, sample(10, "food", "2026-10-01"))
        store.create_expense(self.conn, sample(20, "food", "2026-11-01"))
        store.create_expense(self.conn, sample(30, "travel", "2026-11-02"))
        self.assertEqual(len(store.list_expenses(self.conn, category="food")), 2)
        self.assertEqual(len(store.list_expenses(self.conn, start="2026-11-01")), 2)
        self.assertEqual(len(store.list_expenses(self.conn, end="2026-10-31")), 1)
        self.assertEqual(len(store.list_expenses(self.conn, category="FOOD", start="2026-11-01")), 1)

    def test_list_is_newest_first_and_paginated(self):
        for day in ("2026-11-01", "2026-11-03", "2026-11-02"):
            store.create_expense(self.conn, sample(date=day))
        dates = [e["date"] for e in store.list_expenses(self.conn)]
        self.assertEqual(dates, ["2026-11-03", "2026-11-02", "2026-11-01"])
        page = store.list_expenses(self.conn, limit=1, offset=1)
        self.assertEqual(page[0]["date"], "2026-11-02")

    def test_update(self):
        created = store.create_expense(self.conn, sample(100))
        updated = store.update_expense(self.conn, created["id"], sample(175, "rent"))
        self.assertEqual(updated["amount"], 175)
        self.assertEqual(updated["category"], "rent")

    def test_update_missing_returns_none(self):
        self.assertIsNone(store.update_expense(self.conn, 42, sample()))

    def test_delete(self):
        created = store.create_expense(self.conn, sample())
        self.assertTrue(store.delete_expense(self.conn, created["id"]))
        self.assertFalse(store.delete_expense(self.conn, created["id"]))

    def test_summary_groups_and_sorts_by_total(self):
        store.create_expense(self.conn, sample(100, "food"))
        store.create_expense(self.conn, sample(50, "food"))
        store.create_expense(self.conn, sample(500, "rent"))
        result = store.summary_by_category(self.conn)
        self.assertEqual(result[0], {"category": "rent", "total": 500.0, "count": 1})
        self.assertEqual(result[1], {"category": "food", "total": 150.0, "count": 2})

    def test_database_rejects_non_positive_amount(self):
        with self.assertRaises(sqlite3.IntegrityError):
            store.create_expense(self.conn, sample(-5))


if __name__ == "__main__":
    unittest.main()
