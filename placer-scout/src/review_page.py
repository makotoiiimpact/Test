"""Phase 2 Step B4: build out/review/review.html, a one-clip-at-a-time review page.
Published as a private Artifact; answers save to its db (collection "labels", doc id = clip id) and are exported to labels.json.
Clip images come from out/review/clips_plain.json (src/review_clips.py); score/band stay hidden from the reviewer."""
import os, json
OUT = os.path.join(os.path.dirname(__file__), "..", "out", "review")
clips = json.load(open(os.path.join(OUT, "clips_plain.json")))
data = [{"id": c["id"], "c22": c["close22"], "c19": c["close19"], "w22": c["wide22"], "w19": c["wide19"]} for c in clips]

html = r"""<title>Ant Mound Clip Review</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">
<style>
/* layout: sticky progress bar; one clip per screen (2022 + 2019 side by side, stacked on phones); answer row; clip-number strip */
:root{--bg:#efece4;--card:#f8f6f0;--ink:#2b2a25;--muted:#6b675c;--line:#d6d0c2;--yes:#9a5b17;--yes-bg:#f3e3cc;--no:#4e5a62;--no-bg:#e1e6e8;--unsure:#7a6f2a;--unsure-bg:#ece7c9;--ring:#e8322a;--guide:#fff6a8;
--display:"IBM Plex Sans Condensed","Arial Narrow",system-ui,sans-serif;--body:"Atkinson Hyperlegible",system-ui,-apple-system,"Segoe UI",sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1d1e1a;--card:#262722;--ink:#e9e6dc;--muted:#a6a293;--line:#3a3b34;--yes:#e0a35c;--yes-bg:#3d2d18;--no:#a9b8c1;--no-bg:#2a3236;--unsure:#d6c873;--unsure-bg:#37341d;--ring:#ff5a4f;--guide:#fff6a8;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#1d1e1a;--card:#262722;--ink:#e9e6dc;--muted:#a6a293;--line:#3a3b34;--yes:#e0a35c;--yes-bg:#3d2d18;--no:#a9b8c1;--no-bg:#2a3236;--unsure:#d6c873;--unsure-bg:#37341d;--ring:#ff5a4f;--guide:#fff6a8;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font:16px/1.5 var(--body)}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}
.wrap{max-width:900px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:18px 40px;display:grid;gap:14px}
h1{font:600 1.6rem/1.15 var(--display);letter-spacing:.01em;margin:0;text-wrap:balance}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px}
summary{font-weight:700;cursor:pointer}
.rules{display:grid;gap:.5rem;margin-top:.6rem;max-width:68ch}
.rules p{margin:0}
.rules ol{margin:.2rem 0 0;padding-left:1.3rem;display:grid;gap:.2rem}
.bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding-block:8px;display:flex;flex-wrap:wrap;gap:6px 16px;align-items:center}
.count{font:600 .95rem var(--display);letter-spacing:.04em;text-transform:uppercase;font-variant-numeric:tabular-nums}
.track{flex:1 1 160px;height:8px;background:var(--line);border-radius:4px;overflow:hidden}.fill{height:100%;width:0;background:var(--yes);transition:width .2s}
.status{color:var(--muted);font-size:.88rem;flex-basis:100%}
.viewer{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;display:grid;gap:12px}
.vhead{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px}
.clipno{font:600 1.15rem var(--display);letter-spacing:.04em;font-variant-numeric:tabular-nums}
.toggles{display:flex;flex-wrap:wrap;gap:8px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.seg button{border:0;border-radius:0;padding:.35rem .7rem;font:600 .82rem var(--display);letter-spacing:.05em;text-transform:uppercase;background:transparent;color:var(--muted)}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;justify-items:center}
@media (max-width:560px){.pair{grid-template-columns:minmax(0,1fr)}}
figure{margin:0;width:100%;max-width:360px;min-width:0}
.frame{position:relative;width:100%;aspect-ratio:1;max-width:100%;border-radius:4px;overflow:hidden;background:#000}
.frame img{display:block;width:100%;height:100%;image-rendering:pixelated}
.smooth .frame img{image-rendering:auto}
.ring,.guide{position:absolute;left:50%;top:50%;border-radius:50%;transform:translate(-50%,-50%);pointer-events:none}
.ring{border:2px solid var(--ring)}
.guide{border:1.5px dashed var(--guide);opacity:.85}
.noring .ring,.noring .guide{display:none}
.scale{position:absolute;left:6px;bottom:8px;height:4px;background:#ffe14d;box-shadow:0 0 0 1px #000a;pointer-events:none}
.scale span{position:absolute;left:0;bottom:6px;font:600 .7rem var(--display);color:#ffe14d;text-shadow:0 0 2px #000,0 0 2px #000}
figcaption{font:600 .78rem var(--display);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-top:4px;display:flex;justify-content:space-between}
.answer{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
button{font:700 1rem var(--body);padding:.7rem .4rem;border-radius:6px;border:1px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}
button:hover{border-color:var(--muted)}button:focus-visible{outline:3px solid var(--yes);outline-offset:2px}
button:disabled{opacity:.45;cursor:default}
.answer button[aria-pressed="true"].yes{background:var(--yes-bg);border-color:var(--yes);color:var(--yes)}
.answer button[aria-pressed="true"].no{background:var(--no-bg);border-color:var(--no);color:var(--no)}
.answer button[aria-pressed="true"].unsure{background:var(--unsure-bg);border-color:var(--unsure);color:var(--unsure)}
.nav{display:flex;justify-content:space-between;gap:8px}.nav button{flex:0 1 140px;font-size:.92rem;padding:.5rem}
.keys{color:var(--muted);font-size:.82rem;text-align:center}
.chips{display:grid;grid-template-columns:repeat(auto-fill,minmax(2.4rem,1fr));gap:6px}
.chips button{padding:.35rem 0;font:600 .82rem var(--display);font-variant-numeric:tabular-nums}
.chips button[data-a="yes"]{background:var(--yes-bg);border-color:var(--yes);color:var(--yes)}
.chips button[data-a="no"]{background:var(--no-bg);border-color:var(--no);color:var(--no)}
.chips button[data-a="unsure"]{background:var(--unsure-bg);border-color:var(--unsure);color:var(--unsure)}
.chips button[aria-current="true"]{outline:2px solid var(--ink);outline-offset:1px}
#sync{background:var(--yes-bg);border-color:var(--yes);color:var(--yes);padding:.45rem .8rem;font-size:.9rem}
@media (prefers-reduced-motion:reduce){.fill{transition:none}}
</style>
<div class="wrap">
<h1>Ant mound clip review</h1>
<details id="help" open>
<summary>What to look for</summary>
<div class="rules">
<p>Look at the very centre of the red ring. A harvester-ant nest shows up as a small, bare, lighter disc with no bushes on it, about the size of the dashed circle (2.75 m). At this resolution it is only 4–5 pixels across, so expect a soft pale blob, not a crisp circle.</p>
<p><b>Yes</b> only if all four are true:</p>
<ol><li>A lighter patch sits right in the centre, about the size of the dashed circle.</li><li>It is round-ish, not a streak, track or line.</li><li>It stands on its own, not just part of a larger pale open area (switch to Wide to check).</li><li>You can see it in both 2022 and 2019.</li></ol>
<p><b>No</b> if nothing stands out, it is a streak or track, it is just open ground between bushes, or it is a dark spot. <b>Not sure</b> is always fine: it never counts as a yes.</p>
</div>
</details>
<div class="bar" role="status"><span class="count" id="count">0 of 50 reviewed</span><div class="track" aria-hidden="true"><div class="fill" id="fill"></div></div><button type="button" id="sync" hidden>Send my answers to Claude</button><span class="status" id="status">Connecting to saved answers…</span></div>
<section class="viewer" id="viewer" aria-label="Clip viewer">
<div class="vhead"><span class="clipno" id="clipno">Clip 01 of 50</span>
<div class="toggles">
<span class="seg" role="group" aria-label="View"><button type="button" id="v-close" aria-pressed="true">Close 30 m</button><button type="button" id="v-wide" aria-pressed="false">Wide 60 m</button></span>
<span class="seg" role="group" aria-label="Pixels"><button type="button" id="p-sharp" aria-pressed="true">Sharp</button><button type="button" id="p-smooth" aria-pressed="false">Smooth</button></span>
<span class="seg" role="group" aria-label="Ring"><button type="button" id="r-show" aria-pressed="true">Ring on</button><button type="button" id="r-hide" aria-pressed="false">Ring off</button></span>
</div></div>
<div class="pair" id="pair">
<figure><div class="frame"><img id="img22" alt=""><div class="ring" id="ring22"></div><div class="guide" id="guide22"></div><div class="scale" id="scale22"><span>5 m</span></div></div><figcaption><span>NAIP 2022</span><span>June 2022</span></figcaption></figure>
<figure><div class="frame"><img id="img19" alt=""><div class="ring" id="ring19"></div><div class="guide" id="guide19"></div><div class="scale" id="scale19"><span>5 m</span></div></div><figcaption><span>NAIP 2019</span><span>July 2019</span></figcaption></figure>
</div>
<div class="answer"><button type="button" id="a-yes" class="yes" aria-pressed="false">Yes</button><button type="button" id="a-no" class="no" aria-pressed="false">No</button><button type="button" id="a-unsure" class="unsure" aria-pressed="false">Not sure</button></div>
<div class="nav"><button type="button" id="prev">← Back</button><button type="button" id="next">Next →</button></div>
<p class="keys">Keys: Y yes · N no · U not sure · ← → move · W toggles Close/Wide</p>
</section>
<div class="chips" id="chips" aria-label="Jump to clip"></div>
</div>
<script>
const CLIPS = __DATA__;
const LABEL = {yes: "Yes", no: "No", unsure: "Not sure"};
const answers = {};
let idx = 0, view = "close", col = null, stored = new Set();
const $ = (id) => document.getElementById(id);
const pref = (k, d) => { try { return localStorage.getItem(k) || d; } catch (e) { return d; } };
const setPref = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
try { Object.assign(answers, JSON.parse(localStorage.getItem("mound-answers") || "{}")); } catch (e) {}
view = pref("mound-view", "close");
// overlay sizes as % of frame width: ring 6.6 m, target guide 2.75 m, scale bar 5 m
const SIZE = {close: {m: 30}, wide: {m: 60}};
function sizeOverlays() {
  const m = SIZE[view].m;
  for (const y of ["22", "19"]) {
    $("ring" + y).style.width = $("ring" + y).style.height = (6.6 / m * 100) + "%";
    $("guide" + y).style.width = $("guide" + y).style.height = (2.75 / m * 100) + "%";
    $("scale" + y).style.width = (5 / m * 100) + "%";
  }
}
const chips = $("chips");
CLIPS.forEach((c, i) => { const b = document.createElement("button"); b.type = "button"; b.id = "chip-" + c.id; b.textContent = c.id.slice(1); b.addEventListener("click", () => show(i)); chips.appendChild(b); });
function show(i) {
  idx = Math.max(0, Math.min(CLIPS.length - 1, i)); const c = CLIPS[idx];
  const k = view === "close" ? "c" : "w";
  $("img22").src = "data:image/png;base64," + c[k + "22"]; $("img19").src = "data:image/png;base64," + c[k + "19"];
  $("img22").alt = `2022 aerial photo, clip ${c.id.slice(1)}, ${SIZE[view].m} m across`; $("img19").alt = `2019 aerial photo, clip ${c.id.slice(1)}, ${SIZE[view].m} m across`;
  $("clipno").textContent = `Clip ${c.id.slice(1)} of ${CLIPS.length}`;
  $("prev").disabled = idx === 0; $("next").disabled = idx === CLIPS.length - 1;
  sizeOverlays(); paint();
}
function paint() {
  let n = 0, y = 0;
  for (const c of CLIPS) {
    const a = answers[c.id]; if (a) n++; if (a === "yes") y++;
    const b = $("chip-" + c.id); b.dataset.a = a || ""; b.setAttribute("aria-current", CLIPS[idx].id === c.id ? "true" : "false");
    b.setAttribute("aria-label", `Clip ${c.id.slice(1)}${a ? ", " + LABEL[a] : ""}`);
  }
  const cur = answers[CLIPS[idx].id];
  for (const k of ["yes", "no", "unsure"]) $("a-" + k).setAttribute("aria-pressed", cur === k ? "true" : "false");
  $("count").textContent = `${n} of ${CLIPS.length} reviewed · ${y} yes`;
  $("fill").style.width = (100 * n / CLIPS.length) + "%";
  const pending = col ? Object.keys(answers).filter((id) => !stored.has(id)).length : 0;
  $("sync").hidden = pending === 0; if (pending) $("sync").textContent = `Send my ${pending} answers to Claude`;
}
function setToggle(group, on) { for (const [id, v] of group) $(id).setAttribute("aria-pressed", v === on ? "true" : "false"); }
function setView(v) { view = v; setPref("mound-view", v); setToggle([["v-close", "close"], ["v-wide", "wide"]], v); show(idx); }
function setPixels(v) { document.body.classList.toggle("smooth", v === "smooth"); setPref("mound-px", v); setToggle([["p-sharp", "sharp"], ["p-smooth", "smooth"]], v); }
function setRing(v) { $("pair").classList.toggle("noring", v === "hide"); setPref("mound-ring", v); setToggle([["r-show", "show"], ["r-hide", "hide"]], v); }
$("v-close").onclick = () => setView("close"); $("v-wide").onclick = () => setView("wide");
$("p-sharp").onclick = () => setPixels("sharp"); $("p-smooth").onclick = () => setPixels("smooth");
$("r-show").onclick = () => setRing("show"); $("r-hide").onclick = () => setRing("hide");
$("prev").onclick = () => show(idx - 1); $("next").onclick = () => show(idx + 1);
const status = $("status");
async function answer(k) {
  const id = CLIPS[idx].id; answers[id] = k; paint();
  try { localStorage.setItem("mound-answers", JSON.stringify(answers)); } catch (e) {}
  if (col) {
    try { await col.doc(id).set({answer: k, at: new Date().toISOString()}); stored.add(id); status.textContent = `Saved clip ${id.slice(1)}`; }
    catch (err) { status.textContent = `Couldn't save clip ${id.slice(1)} (${(err && err.code) || "error"}). Answer it again to retry.`; }
  } else { status.textContent = "Saved on this device only. Open this page on claude.ai while signed in, then tap Send."; }
  paint();
  const nextOpen = CLIPS.findIndex((c, i) => i > idx && !answers[c.id]);
  setTimeout(() => show(nextOpen >= 0 ? nextOpen : Math.min(idx + 1, CLIPS.length - 1)), 180);
}
for (const k of ["yes", "no", "unsure"]) $("a-" + k).onclick = () => answer(k);
document.addEventListener("keydown", (e) => {
  if (e.target.closest("input,textarea") || e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (k === "y") answer("yes"); else if (k === "n") answer("no"); else if (k === "u") answer("unsure");
  else if (e.key === "ArrowLeft") show(idx - 1); else if (e.key === "ArrowRight") show(idx + 1);
  else if (k === "w") setView(view === "close" ? "wide" : "close");
});
$("sync").addEventListener("click", async () => {
  if (!col) return; $("sync").disabled = true; let ok = 0, fail = 0;
  for (const [id, a] of Object.entries(answers)) {
    if (stored.has(id)) continue;
    try { await col.doc(id).set({answer: a, at: new Date().toISOString()}); stored.add(id); ok++; } catch (e) { fail++; }
  }
  status.textContent = fail ? `Sent ${ok} answers; ${fail} failed. Tap Send again to retry.` : `Sent ${ok} answers to Claude.`;
  $("sync").disabled = false; paint();
});
setToggle([["v-close", "close"], ["v-wide", "wide"]], view); setPixels(pref("mound-px", "sharp")); setRing(pref("mound-ring", "show"));
const firstOpen = CLIPS.findIndex((c) => !answers[c.id]); show(firstOpen >= 0 ? firstOpen : 0);
if (Object.keys(answers).length) $("help").open = false;          // returning reviewers go straight to the photos
(async () => {
  const timer = setTimeout(() => { if (!col) status.textContent = "Saved answers aren't reachable here, so answers stay on this device."; }, 10000);
  const db = window.claude ? await window.claude.use("db") : null;
  if (!db) { clearTimeout(timer); status.textContent = "Saved answers aren't reachable here, so answers stay on this device."; return; }
  col = db.collection("labels");
  col.onSnapshot((snap) => {
    clearTimeout(timer); stored = new Set();
    for (const d of snap.docs) { const v = d.data(); if (v && v.answer) { stored.add(d.id); if (!answers[d.id]) answers[d.id] = v.answer; } }
    const pending = Object.keys(answers).filter((id) => !stored.has(id)).length;
    status.textContent = pending ? `${pending} answers are on this device but not sent yet. Tap Send.` : "Answers save as you click.";
    paint();
  }, (err) => { clearTimeout(timer); status.textContent = `Couldn't load saved answers (${(err && err.code) || "error"}).`; });
})();
</script>"""
open(os.path.join(OUT, "review.html"), "w").write(html.replace("__DATA__", json.dumps(data)))
print("review.html KB", os.path.getsize(os.path.join(OUT, "review.html")) // 1024)
