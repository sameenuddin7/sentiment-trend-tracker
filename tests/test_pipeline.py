"""Steps 22-26: scoring, aggregation, outliers, graph-vs-numbers and full pipeline tests."""
import json
import re
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sentiment_tracker as st


def make_db(rows):
    path = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE feedback (id INTEGER PRIMARY KEY, created_at TEXT, comment TEXT)")
    conn.executemany("INSERT INTO feedback (created_at, comment) VALUES (?,?)", rows)
    conn.commit(); conn.close()
    return path


class ScoringTests(unittest.TestCase):          # Step 22
    def test_positive(self):  self.assertEqual(st.score_text("Great and amazing, I love it")[0], 3)
    def test_negative(self):  self.assertEqual(st.score_text("Terrible, slow and broken")[0], -3)
    def test_mixed(self):     self.assertEqual(st.score_text("Good product but the delivery was late")[0], 0)
    def test_neutral(self):   self.assertEqual(st.score_text("Received the order on Tuesday")[0], 0)
    def test_case_and_punctuation(self): self.assertEqual(st.score_text("GREAT!!! great, GrEaT.")[0], 3)
    def test_empty(self):     self.assertEqual(st.score_text("")[0], 0)


class AggregationTests(unittest.TestCase):      # Step 23
    SCORED = [(datetime(2026, 1, 5), 2), (datetime(2026, 1, 20), 4),
              (datetime(2026, 2, 3), -3), (datetime(2026, 2, 28), -1)]

    def test_monthly_average(self):
        rows = st.aggregate(self.SCORED, "month")
        self.assertEqual([(r["period"], r["avg"], r["count"]) for r in rows],
                         [("2026-01", 3.0, 2), ("2026-02", -2.0, 2)])

    def test_weekly_grouping(self):
        rows = st.aggregate(self.SCORED, "week")
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["start"], "2026-01-05")  # a Monday

    def test_year_boundary_sorted(self):
        rows = st.aggregate([(datetime(2026, 1, 2), 1), (datetime(2025, 12, 30), 1)], "month")
        self.assertEqual([r["period"] for r in rows], ["2025-12", "2026-01"])


class OutlierTests(unittest.TestCase):          # Step 24
    def test_low_period_flagged(self):
        rows = [{"avg": a} for a in (1, 1.2, 0.9, 1.1, 1.0, -4.0, 1.05, 0.95)]
        st.flag_outliers(rows)
        self.assertEqual([i for i, r in enumerate(rows) if r["outlier"]], [5])

    def test_flat_data_has_no_outliers(self):
        rows = [{"avg": 1.0} for _ in range(5)]
        st.flag_outliers(rows)
        self.assertFalse(any(r["outlier"] for r in rows))


class PipelineTests(unittest.TestCase):         # Steps 25-26
    def test_end_to_end_and_graph_matches_numbers(self):
        data = []
        for m in range(1, 9):
            for _ in range(5):
                data.append((f"2026-{m:02d}-10T10:00:00", "great amazing service, love it"))
        for _ in range(5):
            data.append(("2026-09-10T10:00:00", "terrible slow broken awful, hate it"))
        db = make_db(data)
        out = tempfile.mktemp(suffix=".js")
        trend = st.run(db, out, quiet=True)

        text = Path(out).read_text()
        embedded = json.loads(re.search(r"const SENTIMENT_DATA = (\{.*?\});\n", text, re.S).group(1))
        self.assertEqual(embedded["monthly"], trend["monthly"])      # JS data == Python numbers
        self.assertEqual(trend["monthly"][0]["avg"], 3.0)            # 3 positive words ("great amazing ... love")
        self.assertEqual(trend["monthly"][-1]["avg"], -5.0)          # terrible slow broken awful hate
        self.assertTrue(trend["monthly"][-1]["outlier"])
        self.assertIn("d3.scaleTime", text)                          # D3 chart code is attached
        self.assertEqual(st.discover_schema(sqlite3.connect(db)), ("feedback", "created_at", "comment"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
