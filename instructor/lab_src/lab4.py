TITLE = "Trust, but Verify"
SLUG = "verify"

CELLS = [
("md", """
**Scenario.** A client sends a customer-service dataset exported from an old reporting system (`customer_service_messy.csv`). Their data description says:

> *4,123 unique records (county-months). Each record has 21 variables. All variables are numeric. Missing values are allowed where the source had none.*

Your job is to turn it into **one row per record with 21 variable columns**, and to **prove** that you did it right.

You may (and should) use AI to write the cleaning code. **You are graded on your checks, not on your code.**
"""),
("md", """
## Part 1: Look before you prompt (10 min)
Scroll through the raw file below. With your partner, list **at least six** things that could trip up cleaning code. Be specific ("some record labels look like `Rec. 12`", not "formatting issues").
"""),
("code", """
import csv, re
import pandas as pd
import numpy as np
import io, urllib.request
path = DATA + "customer_service_messy.csv"
text = urllib.request.urlopen(path).read().decode() if path.startswith("http") else open(path, encoding="utf-8").read()
raw = list(csv.reader(io.StringIO(text)))
print(len(raw), "lines")
for i in list(range(0, 40)) + list(range(2436, 2456)):
    print(i, [c for c in raw[i] if c != ""])
"""),
("code", """
things_that_could_go_wrong = \"\"\"
1.
2.
3.
4.
5.
6.
\"\"\"
"""),
("md", """
## Part 2: Write the checks *first* (15 min)
Before any cleaning code exists, write down how you would recognize a correct result. Implement each as a function that takes the cleaned DataFrame `clean` (one row per record, a `Record` column plus 21 variable columns) and **raises an error** if the check fails.

Starter checks are given. Add at least **four** of your own (ideas: ranges that make sense, the number of missing cells, a hand-checked record, the variable names).
"""),
("code", """
def check(name, test):
    \"\"\"Run one check. `test` is a function returning (passed, detail). A crash counts as FAIL.\"\"\"
    try:
        passed, detail = test()
    except Exception as e:
        passed, detail = False, f"check crashed: {type(e).__name__}: {e}"
    print(("PASS " if passed else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    return bool(passed)

def run_checks(clean):
    results = []
    results.append(check("4,123 rows", lambda: (len(clean) == 4123, f"got {len(clean)}")))
    results.append(check("Record IDs unique", lambda: (clean["Record"].is_unique, "")))
    results.append(check("22 columns (Record + 21 variables)", lambda: (clean.shape[1] == 22, f"got {clean.shape[1]}")))
    num = clean.drop(columns="Record").apply(pd.to_numeric, errors="coerce")
    bad = (num.isna() & clean.drop(columns="Record").notna()).sum().sum()
    results.append(check("every value numeric (or missing)", lambda: (bad == 0, f"{bad} non-numeric cells")))
    # --- add your own checks below ---

    print(f"\\n{sum(results)}/{len(results)} checks passed")
""", """
def check(name, test):
    try:
        passed, detail = test()
    except Exception as e:
        passed, detail = False, f"check crashed: {type(e).__name__}: {e}"
    print(("PASS " if passed else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    return bool(passed)

def run_checks(clean):
    results = []
    results.append(check("4,123 rows", lambda: (len(clean) == 4123, f"got {len(clean)}")))
    results.append(check("Record IDs unique", lambda: (clean["Record"].is_unique, "")))
    results.append(check("22 columns (Record + 21 variables)", lambda: (clean.shape[1] == 22, f"got {clean.shape[1]}")))
    num = clean.drop(columns="Record").apply(pd.to_numeric, errors="coerce")
    bad = (num.isna() & clean.drop(columns="Record").notna()).sum().sum()
    results.append(check("every value numeric (or missing)", lambda: (bad == 0, f"{bad} non-numeric cells")))
    # --- instructor's extra checks ---
    pct = [c for c in num if c.startswith("%") or c == "Unemployment Rate"]
    results.append(check("percent/rate columns within 0-1", lambda: (
        (((num[pct] >= 0) & (num[pct] <= 1)) | num[pct].isna()).all().all() and len(pct) == 5, f"{len(pct)} columns, max {num[pct].max().max():.3g}")))
    results.append(check("Month is 1..12", lambda: (num["Month"].dropna().between(1, 12).all(), "")))
    miss = num.isna().sum().sum()
    results.append(check("missing cells < 3% of cells", lambda: (miss < 0.03 * num.size, f"{miss} missing")))
    # hand-checked in the raw file: Record 1841 is the last record, followed by orphan lines.
    results.append(check("Record 1841 Month == 12 (hand-checked)", lambda: (
        float(clean.set_index("Record").loc[1841, "Month"]) == 12, f"got {clean.set_index('Record').loc[1841, 'Month']}")))
    results.append(check("no duplicate-looking columns", lambda: (len(set(c.strip().lower() for c in clean.columns)) == clean.shape[1], "")))
    print(f"\\n{sum(results)}/{len(results)} checks passed")
"""),
("md", """
## Part 3: Let AI clean it, then run your checks (20 min)
Give your AI assistant a **spec** (remember Lab 1): what one record looks like in the raw file, the output shape, and everything from your Part 1 list. Paste its code below. The code must produce a DataFrame called `clean`.

Then run your checks. **When a check fails:** don't just paste "it's wrong" back to the AI. Find **the exact raw lines** that cause the failure, and give the AI those lines plus the rule it broke. That is a *minimal reproducible example*, and it's the fastest way to fix code anyone wrote.
"""),
("code", """
# AI-written cleaning code goes here. It must create `clean`.

""", """
# --- First attempt: a typical AI answer to a one-line prompt (for demo in class) ---
rows, cur = [], None
for r in raw:
    if r[0].startswith("Record"):
        cur = {"Record": r[0].replace("Record", "").strip()}
        rows.append(cur)
    elif cur is not None:
        cells = [c for c in r[1:] if c != ""]
        for i in range(0, len(cells) - 1, 2):
            cur[cells[i]] = cells[i + 1]
naive = pd.DataFrame(rows)
print("NAIVE ATTEMPT"); run_checks(naive); print()

# --- Robust version (what the checks push you toward) ---
VARS = ["County", "Year", "Month", "Population (000s)", "Avg. Household Size", "Avg. Age", "% Female", "% White",
        "% Democrats", "Avg. Education (Yrs.)", "Avg. Income (000s)", "% Home Owners", "Unemployment Rate",
        "Avg. Commute (mins)", "Rainfall (Inches)", "Num. Starbucks", "Num. Microbreweries",
        "Avg. Worker Hours (per day)*", "Avg. Employee Wage (000s)*", "Log of Help Desk Employees*",
        "Log of Complaints (per day)*"]
canon = lambda s: re.sub(r"[^a-z0-9%()]", "", s.lower())
NAMES = {canon(v): v for v in VARS}
MISSING = {"n/a", "na", "-", "."}
HEADER = re.compile(r"^\\s*rec(?:ord)?\\.?\\s*(?:no\\.|#|:)?\\s*(\\d+)\\s*\\*?\\s*$", re.I)

def to_number(s):
    s = s.strip()
    if s.lower() in MISSING:
        return np.nan
    m = re.fullmatch(r"(-?[\\d.]+(?:[eE][-+]?\\d+)?)\\s*(%|mins|yrs|in|K)?", s)
    x = float(m.group(1))
    return x / 100 if m.group(2) == "%" else x

recs, cur, pending = {}, None, None
for r in raw:
    if r[0].strip():                                    # column A has text: a header or junk
        m = HEADER.match(r[0])
        cur, pending = (int(m.group(1)) if m else None), None
        if cur is not None:
            recs.setdefault(cur, {})
        continue
    if cur is None:
        continue
    for c in r[1:]:
        if not c.strip():
            continue
        if ":" in c:                                     # "Name: value" squeezed into one cell
            n, v = c.rsplit(":", 1)
            recs[cur].setdefault(NAMES[canon(n)], to_number(v))
        elif canon(c) in NAMES and c.strip().lower() not in MISSING:
            pending = NAMES[canon(c)]                    # a variable name; its value is the next cell (maybe next line)
        elif pending is not None:
            recs[cur].setdefault(pending, to_number(c))  # never overwrite: protects against orphan lines
            pending = None
clean = (pd.DataFrame.from_dict(recs, orient="index").reindex(columns=VARS)
           .rename_axis("Record").reset_index().sort_values("Record").reset_index(drop=True))
print("ROBUST VERSION")
"""),
("code", "run_checks(clean)"),
("md", """
## Part 4: Reflect (5 min, submit)
1. Which of your checks caught a problem the AI's code had? Which check would you *not* have thought of before today?
2. Your code passes all your checks. Name one error it could **still** contain that none of your checks would catch.
3. Save your result: `clean.to_csv("customer_service_clean.csv", index=False)`. Your instructor will compare it to the answer key.
"""),
("code", """
reflection = \"\"\"

\"\"\"
""", """
# INSTRUCTOR: compare to answer key (not distributed to students)
key = pd.read_csv("../customer_service_answer_key.csv") if os.path.exists("../customer_service_answer_key.csv") \\
      else pd.read_csv("instructor/customer_service_answer_key.csv")
k = key.sort_values("Record").reset_index(drop=True)
same = np.isclose(clean[k.columns[1:]].astype(float), k[k.columns[1:]].astype(float), equal_nan=True, rtol=1e-9)
print("cells matching answer key:", f"{same.mean():.2%}", "| records fully correct:", same.all(axis=1).sum(), "/", len(k))
"""),
]
