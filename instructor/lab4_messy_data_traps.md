# Messy Anheuser-Busch data: instructor notes

Files
- `customer_service_Anheuser-Busch_messy.csv` — hand to students (28,816 lines)
- `customer_service_Anheuser-Busch_answer_key.csv` — 4,123 records x 21 variables; blank = genuinely missing
- `make_messy.py` — generator (seed 492, reproducible); `solve_messy.py` — reference solver, matches key exactly

## Traps and what they break

| Trap | Count | Breaks |
|---|---|---|
| Header variants: `RECORD 12`, `record 12`, `Record #12`, `Record: 12`, `  Record 12`, `Record 12 *`, `Rec. 12`, `Record No. 12`, `Record12` | 1,282 | `Left(x, 6) = "Record"`, `Mid(x, 8)` for the ID |
| Fake headers: title lines and `Records 351-700 (continued)` page breaks | 12 | Same test, the other way: they *pass* `Left(x,6)="Record"` |
| Page headers / footnote lines in column A | 16 | Anything that assumes col A is either a header or blank |
| Blank row inside a record | 560 | `.End(xlDown)` to find the record's last row |
| Two blank cells between pairs in a row | 1,930 | `.End(xlToRight)` to find the row's end |
| Name variants: extra spaces, UPPER/lower case, missing `*`, missing `.` | 4,316 | Exact string match against Sheet2 headers |
| `Name: value` in a single cell | 1,735 | Fixed name/value alternation; shifts every later pair in that row |
| Pair wrapped: name at end of one line, value at start of next | 52 | Row-by-row pair reading |
| Missing markers `N/A`, `n/a`, `NA`, `-`, `.` | 1,719 | Type mismatch on `Double`; `NA` looks like a name |
| Units in text: `43 mins`, `36 yrs`, `4.0 in`, `71.8K` | 1,270 | Type mismatch / silently stored as text |
| Percent text: `52.98%` | 458 | Must divide by 100 to match the other rows |
| Variable absent from a record | 198 | Must leave a blank, not shift columns |
| Exact duplicate records | 40 | Row count 4,163 instead of 4,123 |
| Orphan values after the last record (from the original file) | 60 lines | Naive code overwrites Record 1841's Month, Commute, etc. |

## Naive baseline

The L18 logic (`Left(A,6)="Record"`, pairs read until `.End(xlToRight)`, exact name match),
simulated: 3,623 rows produced, 3,478 type-mismatch errors, **53.5% of cells correct,
only 304 of 4,123 records fully correct.**

## Grading ideas
- Report row count, missing-cell count, and 3 records the instructor picks (e.g. 1841, plus two with traps).
- Ask for their checks, not just their output: how do they know they got 4,123?
