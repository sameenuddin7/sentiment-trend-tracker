"""Creates reviews.db with sample feedback (12 months, with intentionally low-sentiment periods)."""
import random
import sqlite3
from datetime import date, timedelta

# Probability that a review is positive, by month. Mar/Apr 2026 simulate an outage.
MONTH_MOOD = {
    (2025, 10): 0.60, (2025, 11): 0.62, (2025, 12): 0.65, (2026, 1): 0.50,
    (2026, 2): 0.55, (2026, 3): 0.08, (2026, 4): 0.30, (2026, 5): 0.55,
    (2026, 6): 0.65, (2026, 7): 0.70, (2026, 8): 0.68, (2026, 9): 0.72,
}
POSITIVE = [
    "Great service and very friendly staff, I love it",
    "Excellent quality, fast delivery and easy checkout. Highly recommend",
    "The app is smooth and reliable, really impressive update",
    "Amazing support team, they were helpful and polite",
    "Perfect experience, happy and satisfied with the purchase",
]
NEGATIVE = [
    "Terrible experience, the app crashed and support was rude",
    "Slow delivery and a broken product, very disappointed",
    "Awful update, buggy and confusing. Total waste of money",
    "Worst service ever, my problem was ignored. I want a refund",
    "Frustrating outage again, the site was down and the error page was useless",
]
MIXED = [
    "Good product but the delivery was late",
    "Great design, however the app is slow and buggy",
    "Friendly staff but expensive and the checkout was confusing",
]
NEUTRAL = ["Received the order on Tuesday", "Switched to the new plan last week"]


def create(db_path="reviews.db", seed=42):
    rng = random.Random(seed)
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS reviews")
    conn.execute("""CREATE TABLE reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_date TEXT NOT NULL,      -- ISO 8601 timestamp
        customer TEXT,
        review_text TEXT NOT NULL)""")
    rows = []
    for (y, m), p_pos in MONTH_MOOD.items():
        days = (date(y + (m == 12), m % 12 + 1, 1) - date(y, m, 1)).days
        for _ in range(rng.randint(26, 34)):
            d = date(y, m, 1) + timedelta(days=rng.randrange(days))
            ts = f"{d.isoformat()}T{rng.randint(8, 21):02d}:{rng.randint(0, 59):02d}:00"
            r = rng.random()
            if r < p_pos * 0.8:
                text = rng.choice(POSITIVE)
            elif r < 0.8:
                text = rng.choice(NEGATIVE)
            elif r < 0.95:
                text = rng.choice(MIXED)
            else:
                text = rng.choice(NEUTRAL)
            rows.append((ts, f"user{rng.randint(100, 999)}", text))
    conn.executemany("INSERT INTO reviews (review_date, customer, review_text) VALUES (?,?,?)", rows)
    conn.commit()
    conn.close()
    return len(rows)


if __name__ == "__main__":
    print(f"Created reviews.db with {create()} reviews")
