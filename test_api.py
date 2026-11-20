"""API tests. Requires: pip install -r requirements.txt (fastapi, httpx)."""
import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from app.main import app

PAYLOAD = {"amount": 120.5, "category": "Food", "description": "Lunch", "date": "2026-11-10"}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["EXPENSE_DB"] = os.path.join(self.tmp.name, "test.db")
        self.client = TestClient(app)

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("EXPENSE_DB", None)

    def test_health(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})

    def test_total_endpoint(self):
        self.client.post("/expenses", json=PAYLOAD)
        self.client.post("/expenses", json={**PAYLOAD, "amount": 80})
        resp = self.client.get("/expenses/total")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"total": 200.5, "count": 2})

    def test_create_normalizes_category_and_returns_201(self):
        resp = self.client.post("/expenses", json=PAYLOAD)
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["category"], "food")
        self.assertIn("id", body)

    def test_create_rejects_invalid_input(self):
        for bad in (
            {**PAYLOAD, "amount": 0},
            {**PAYLOAD, "amount": -10},
            {**PAYLOAD, "date": "not-a-date"},
            {**PAYLOAD, "category": "   "},
        ):
            self.assertEqual(self.client.post("/expenses", json=bad).status_code, 422)

    def test_get_update_delete_flow(self):
        expense_id = self.client.post("/expenses", json=PAYLOAD).json()["id"]
        self.assertEqual(self.client.get(f"/expenses/{expense_id}").status_code, 200)

        changed = {**PAYLOAD, "amount": 999}
        self.assertEqual(self.client.put(f"/expenses/{expense_id}", json=changed).json()["amount"], 999)

        self.assertEqual(self.client.delete(f"/expenses/{expense_id}").status_code, 204)
        self.assertEqual(self.client.get(f"/expenses/{expense_id}").status_code, 404)

    def test_missing_expense_returns_404(self):
        self.assertEqual(self.client.get("/expenses/12345").status_code, 404)
        self.assertEqual(self.client.put("/expenses/12345", json=PAYLOAD).status_code, 404)
        self.assertEqual(self.client.delete("/expenses/12345").status_code, 404)

    def test_list_filter_and_summary(self):
        self.client.post("/expenses", json=PAYLOAD)
        self.client.post("/expenses", json={**PAYLOAD, "category": "travel", "amount": 300})
        self.assertEqual(len(self.client.get("/expenses?category=travel").json()), 1)
        summary = self.client.get("/summary").json()
        self.assertEqual(summary[0]["category"], "travel")
        self.assertEqual(summary[0]["total"], 300.0)

    def test_invalid_date_range_returns_422(self):
        resp = self.client.get("/expenses?start=2026-12-01&end=2026-01-01")
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
