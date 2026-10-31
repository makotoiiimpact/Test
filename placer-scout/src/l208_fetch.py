"""Phase 2 Step A1: USBM Minerals Yearbooks 1939-1947 (archive.org scans, no login) -> page-indexed OCR text + Clark County passages.
Printed page numbers come from archive.org's page_numbers.json (leaf -> printed page)."""
import os, io, re, gzip, json, csv, hashlib, datetime, time, requests

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "l208")
YEARS = range(1939, 1948)
out = []
for y in YEARS:
    ident = f"pub_usgov-minerals-yearbook_{y}"
    if os.path.exists(os.path.join(DATA, f"myb_{y}.json")): out.append((y, ident, -1)); continue
    meta = requests.get(f"https://archive.org/metadata/{ident}", timeout=120).json()
    names = {f["name"] for f in meta["files"]}
    base = next(n[:-len("_hocr_searchtext.txt.gz")] for n in names if n.endswith("_hocr_searchtext.txt.gz"))
    def get(suffix):
        for _ in range(4):
            r = requests.get(f"https://archive.org/download/{ident}/{base}{suffix}", timeout=300)
            if r.status_code == 200 and r.content: return r.content
            time.sleep(10)
        raise RuntimeError(f"{ident}{suffix}: HTTP {r.status_code}")
    text = gzip.decompress(get("_hocr_searchtext.txt.gz")).decode("utf-8", "replace")
    idx = json.loads(gzip.decompress(get("_hocr_pageindex.json.gz")).decode())     # [[char_start, char_end, ...], ...] one per scanned leaf
    pn = json.loads(get("_page_numbers.json"))
    leaf2page = {p["leafNum"]: p.get("pageNumber", "") for p in pn.get("pages", [])}
    pages = [{"leaf": i, "printed_page": leaf2page.get(i, ""), "text": text[a:b]} for i, (a, b, *_) in enumerate(idx)]
    json.dump({"identifier": ident, "pdf": f"https://archive.org/download/{ident}/{base}.pdf",
               "confidence": pn.get("confidence"), "pages": pages}, open(os.path.join(DATA, f"myb_{y}.json"), "w"))
    hits = [p for p in pages if re.search(r"Clark\s+County", p["text"]) and re.search(r"Nevada|Searchlight|Goodsprings|Yellow Pine|Eldorado|Nelson", p["text"])]
    print(y, "pages", len(pages), "printed-page map confidence", pn.get("confidence"), "Clark County pages", [(h["leaf"], h["printed_page"]) for h in hits], flush=True)
    out.append((y, ident, len(pages)))
with open(os.path.join(DATA, "..", "PROVENANCE.csv"), "a", newline="") as f:
    for y, ident, n in [o for o in out if o[2] >= 0]:
        p = os.path.join(DATA, f"myb_{y}.json")
        csv.writer(f).writerow([f"USBM Minerals Yearbook {y} (OCR, page-indexed)", f"https://archive.org/details/{ident}", f"l208/myb_{y}.json", n,
                                hashlib.sha256(open(p, "rb").read()).hexdigest()[:16], datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")])
