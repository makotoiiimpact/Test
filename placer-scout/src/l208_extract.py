"""Phase 2 Step A1b: pull every Clark County mining passage (with printed page) from the yearbook OCR for reading."""
import os, re, json
DATA = os.path.join(os.path.dirname(__file__), "..", "data", "l208")
KEY = re.compile(r"clark\s+county|searchlight|goodsprings|yellow\s+pine|eldorado|el\s+dorado|nelson|crescent|newberry|sloan|potosi|jean\b", re.I)
for y in range(1939, 1948):
    d = json.load(open(os.path.join(DATA, f"myb_{y}.json")))
    out = []
    for p in d["pages"]:
        t = p["text"]
        if not re.search(r"nevada", t, re.I) or not KEY.search(t): continue
        if re.search(r"\bindex\b", t[:400], re.I): continue                 # skip back-of-book index pages
        if len(KEY.findall(t)) < 2: continue
        out.append(f"\n===== {y} | printed page {p['printed_page']} | scan leaf {p['leaf']} =====\n{re.sub(r'[ \t]+', ' ', t)}")
    open(os.path.join(DATA, f"passages_{y}.txt"), "w").write("".join(out))
    print(y, "pages", len(out), [l.split('|')[1].strip() for l in out])
