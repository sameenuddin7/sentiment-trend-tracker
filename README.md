# Sentiment Trend Tracker

Reads customer reviews from SQLite, scores each one with a word list, averages the scores per month/week,
flags unusually negative periods, and draws the trend with D3.js.

## Run it
```
python create_database.py        # optional: builds sample reviews.db (359 reviews, Oct 2025 - Sep 2026)
python sentiment_tracker.py      # console summary + writes gsentiment.js
python -m unittest discover -s tests -v
```
Then open `mood_monitor.html` in a browser (it loads D3 from cdnjs, so it needs internet).
Use your own data: `python sentiment_tracker.py --db mydata.db` (needs one table with a date/time column and a review/feedback/comment text column).

## Files
| File | Role |
|---|---|
| `create_database.py` | Builds `reviews.db` (`reviews(id, review_date, customer, review_text)`) with positive, negative, mixed and neutral reviews, including an outage in Mar-Apr 2026 |
| `lexicon.py` | `positive_words` and `negative_words` lists |
| `sentiment_tracker.py` | Pipeline: schema discovery, scoring, aggregation, outliers, console summary, writes `gsentiment.js` |
| `chart_template.js` | D3 chart code appended to the generated `gsentiment.js` |
| `gsentiment.js` | Generated: `SENTIMENT_DATA` plus the D3 line chart |
| `mood_monitor.html` | Page that loads D3 and `gsentiment.js` |
| `tests/test_pipeline.py` | Scoring, aggregation, outlier and end-to-end tests |

## Methodology
1. Find the table with a timestamp column and a text column (`PRAGMA table_info`).
2. Lowercase the text and split into words (`[a-z']+`).
3. Score = (positive words) - (negative words); each match is +1 / -1.
4. Group by calendar month (`YYYY-MM`) and ISO week (`YYYY-Www`), then average the scores.
5. Outliers: z-score of each period's average against all period averages; `z <= -1.5` is flagged (adjustable with `--z`). Days are checked the same way with `z <= -2`.
6. Write the trend data to `gsentiment.js`; D3 draws the line (green above 0, red below 0), outlier rings, and tooltips.

## Sample result (seeded data)
Healthy months average about +0.3 to +1.4. March 2026 (-3.09) and April 2026 (-3.12) are flagged as outliers, along with seven weeks between W10 and W17. Add your screenshot of `mood_monitor.html` here.

## Verification (steps 22-26)
- Scoring: positive, negative, mixed, neutral, mixed-case and empty text.
- Aggregation: monthly averages, weekly Monday start dates, year boundaries.
- Outliers: a deliberately low month is flagged; flat data is not.
- End to end: the numbers embedded in `gsentiment.js` equal the Python results, which is what the chart plots.

## Limitations
- Word lists are small and general; domain slang and misspellings are missed.
- No negation or intensity handling ("not good" scores +1; "very bad" is the same as "bad").
- Longer reviews get larger scores; scores are not normalised by length.
- Periods with few reviews give noisy averages.
- The z-score rule assumes roughly normal period averages and needs several periods.

## Future enhancements
Negation and intensifier handling, VADER or a transformer model for comparison, length-normalised scores, rolling averages, confidence bands, filters by product or region, alerts for new outliers.
