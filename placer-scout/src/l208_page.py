"""Print the Clark County part of given printed pages of one yearbook volume: python3 l208_page.py YEAR PAGE [PAGE...]"""
import sys, re, json, os
DATA = os.path.join(os.path.dirname(__file__), "..", "data", "l208")
y = int(sys.argv[1]); want = sys.argv[2:]
d = json.load(open(os.path.join(DATA, f"myb_{y}.json")))
KEY = re.compile(r"CLARK\s+COUNTY|Clark County|Searchlight|Goodsprings|Yellow Pine|Eldorado|El Dorado|Nelson|Crescent|Potosi", re.I)
for p in d["pages"]:
    if p["printed_page"] not in want: continue
    t = re.sub(r"\s+", " ", p["text"]); ms = list(KEY.finditer(t))
    if not ms: continue
    a, b = max(0, ms[0].start() - 300), min(len(t), ms[-1].end() + 900)
    print(f"\n##### {y} edition, printed p.{p['printed_page']} (scan leaf {p['leaf']}) #####\n{t[a:b]}")
