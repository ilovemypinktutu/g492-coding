import csv, random, re
import pandas as pd
random.seed(492)
clean = pd.read_csv("customer_service_Anheuser-Busch_clean.csv")
VARS = list(clean.columns[1:])
W = 29  # columns A..AC, same as original

# keep original record order from the source file
order = []
with open("/Users/seob/Downloads/customer_service_Anheuser-Busch.csv", encoding="utf-8-sig") as f:
    for row in csv.reader(f):
        m = re.fullmatch(r"Record\s*(\d+)", row[0].strip()) if row else None
        if m: order.append(int(m.group(1)))
by_id = {int(r.Record): r for r in clean.itertuples(index=False)}
key = clean.set_index("Record").astype(object)

def pad(cells): return (cells + [""] * W)[:W] if len(cells) <= W else cells

def header(rid):
    r = random.random()
    if r < .70: return f"Record {rid}"
    return random.choice([f"RECORD {rid}", f"record {rid}", f"Record #{rid}", f"Record: {rid}",
                          f"  Record {rid}", f"Record {rid} *", f"Rec. {rid}", f"Record No. {rid}", f"Record{rid}"])

def name_variant(n):
    return random.choice([n + " ", " " + n, n.upper(), n.lower(), n.replace("*", ""),
                          n.replace(". ", " "), n.replace(" ", "  ", 1)])

UNITS = {"Avg. Commute (mins)": " mins", "Avg. Age": " yrs", "Rainfall (Inches)": " in",
         "Avg. Income (000s)": "K", "Population (000s)": "K"}
def fmt(v):
    s = repr(float(v)) if isinstance(v, float) and v != int(v) else str(int(v)) if float(v) == int(v) else str(v)
    return s

rows, traps = [], {k: 0 for k in ["header variant","blank row in record","gap inside row","name variant",
    "percent text","unit text","missing marker","variable absent","name:value in one cell","pair wrapped to next line",
    "duplicate record","page header / note line","'Records ...' fake header"]}
title = ["Anheuser-Busch Customer Service Data", "Exported 09/30/2026 - DRAFT", "Records 1-4123 (unsorted)", ""]
for t in title: rows.append(pad([t]))
traps["'Records ...' fake header"] += 1

dup_pool = random.sample(order, 40)
seq = list(order)
for rid in dup_pool: seq.insert(random.randrange(seq.index(rid) + 1, len(seq) + 1), rid)
emitted = set()
page = 1
for i, rid in enumerate(seq):
    if i and i % 350 == 0:
        page += 1
        rows.append(pad([f"Anheuser-Busch Customer Service Data - Page {page}"]))
        rows.append(pad([f"Records {i+1}-{min(i+350, len(seq))} (continued)"]))
        traps["page header / note line"] += 1; traps["'Records ...' fake header"] += 1
    if i and i % 777 == 0:
        rows.append(pad(["* Starred variables are estimates. See data description."])); traps["page header / note line"] += 1
    is_dup = rid in emitted
    if is_dup:
        traps["duplicate record"] += 1
        rows.extend(emitted_rows[rid]); continue
    rec = by_id[rid]
    h = header(rid); traps["header variant"] += h != f"Record {rid}"
    block = [pad([h])]
    vars_ = VARS[:]; random.shuffle(vars_)
    if random.random() < .03:
        for v in random.sample(vars_, random.choice([1, 2])):
            vars_.remove(v); key.loc[rid, v] = None; traps["variable absent"] += 1
    tokens = []  # list of cells-lists per pair
    for v in vars_:
        val = getattr(rec, "_%d" % (VARS.index(v) + 2)) if False else rec[VARS.index(v) + 1]
        s = fmt(val)
        name = v
        if random.random() < .05: name = name_variant(v); traps["name variant"] += 1
        r = random.random()
        if r < .02:
            s = random.choice(["N/A", "n/a", "-", "", "NA", "."]); key.loc[rid, v] = None; traps["missing marker"] += 1
            if s == "": s = "N/A"
        elif r < .05 and v.startswith("%"):
            s = f"{float(val)*100:.6g}%"; key.loc[rid, v] = float(f"{float(val)*100:.6g}") / 100; traps["percent text"] += 1
        elif r < .08 and v in UNITS:
            s = s + UNITS[v]; traps["unit text"] += 1
        if random.random() < .02:
            tokens.append([f"{name}: {s}"]); traps["name:value in one cell"] += 1
        else:
            tokens.append([name, s])
    # split pairs into lines
    lines, j = [], 0
    while j < len(tokens):
        k = random.randint(1, 7); chunk = tokens[j:j+k]; j += k
        cells = []
        for t in chunk:
            if cells and random.random() < .03: cells += ["", ""]; traps["gap inside row"] += 1
            cells += t
        lines.append(cells)
    if len(lines) > 1 and random.random() < .015:
        a = random.randrange(len(lines) - 1)
        if len(lines[a]) >= 2 and not ":" in lines[a][-1] and len(lines[a]) % 2 == 0 and lines[a][-2] != "":
            val = lines[a].pop(); lines[a+1] = [val] + lines[a+1]; traps["pair wrapped to next line"] += 1
    for li, cells in enumerate(lines):
        block.append(pad([""] + cells))
        if li < len(lines) - 1 and random.random() < .03:
            block.append(pad([""])); traps["blank row in record"] += 1
    rows.extend(block); emitted.add(rid)
    emitted_rows = globals().setdefault("emitted_rows", {}); emitted_rows[rid] = block

# keep the original orphan tail (rows after last record)
with open("/Users/seob/Downloads/customer_service_Anheuser-Busch.csv", encoding="utf-8-sig") as f:
    src = list(csv.reader(f))
last = max(i for i, r in enumerate(src) if r and r[0].startswith("Record"))
tail = [r for r in src[last+1:] if not r[0].strip() and r[1:3] == ["", ""] and any(r)]
rows.extend(pad(r) for r in tail[:60])
rows.append(pad(["End of report"]))

with open("customer_service_Anheuser-Busch_messy.csv", "w", newline="") as f:
    csv.writer(f).writerows(rows)
key.reset_index().to_csv("customer_service_Anheuser-Busch_answer_key.csv", index=False)
print(len(rows), "lines"); [print(f"{v:5d}  {k}") for k, v in traps.items()]
