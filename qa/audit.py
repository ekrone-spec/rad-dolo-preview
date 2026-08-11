#!/usr/bin/env python3
"""Build-output audit + regression suite.

Runs build.py, then checks the generated dist/ for the classes of defect a link
crawl cannot see (unlinked pages like 404.html are invisible to a crawler).

    python3 qa/audit.py

Exits non zero if anything fails, so it can gate a deploy.
"""
import glob, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
os.chdir(ROOT)

fails = []
def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (("  -> " + detail) if detail and not ok else ""))
    if not ok:
        fails.append(name)

# expected counts — update these when content is deliberately added or removed
EXPECT = {"posts": 6, "services": 4, "shop": 3, "marquee": 10, "quotes": 16, "sitemap": 12}

r = subprocess.run(["python3", "build.py"], capture_output=True, text=True)
check("build runs clean", r.returncode == 0, r.stderr[-200:])
print("      " + r.stdout.strip())

pages = [p for p in glob.glob(DIST + "/**/*.html", recursive=True) if "admin" not in p]
files = {os.path.relpath(os.path.join(rt, f), DIST).replace(os.sep, "/")
         for rt, _, fs in os.walk(DIST) for f in fs}

structural, long_t, long_d, no_og, dashes = [], [], [], [], []
for pg in pages:
    rel = "/" + os.path.relpath(pg, DIST).replace(os.sep, "/").replace("index.html", "")
    base = os.path.dirname(os.path.relpath(pg, DIST))
    s = open(pg, encoding="utf-8").read()

    structural += [rel + ": unreplaced token " + t for t in re.findall(r"\{\{[A-Z_]+\}\}", s)]
    if "<!-- BUILD:" in s:
        structural.append(rel + ": unprocessed build marker")

    for _, url in re.findall(r'(href|src)="([^"]+)"', s):
        u = url.split("#")[0].split("?")[0]
        if not u or u.startswith(("http", "mailto:", "data:", "//", "/.netlify")):
            continue
        p = u.lstrip("/") if u.startswith("/") else os.path.normpath(os.path.join(base, u)).replace(os.sep, "/")
        if p in ("", "."):
            continue
        if p.endswith("/") or "." not in os.path.basename(p):
            p = p.rstrip("/") + "/index.html"
        if p not in files:
            structural.append("%s: broken link %s" % (rel, url))

    for url in re.findall(r"background-image:url\('([^']+)'\)", s):
        if url.startswith(("http", "data:")):
            continue
        p = url.lstrip("/") if url.startswith("/") else os.path.normpath(os.path.join(base, url)).replace(os.sep, "/")
        if p not in files:
            structural.append("%s: missing image %s" % (rel, url))

    ids = re.findall(r'id="([^"]+)"', s)
    structural += ["%s: duplicate id #%s" % (rel, d) for d in {i for i in ids if ids.count(i) > 1}]
    if len(re.findall(r"<h1", s)) != 1:
        structural.append("%s: %d h1 tags" % (rel, len(re.findall(r"<h1", s))))

    for block in re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', s):
        try:
            json.loads(block)
        except Exception as e:
            structural.append("%s: invalid JSON-LD (%s)" % (rel, str(e)[:50]))

    title = (re.search(r"<title>(.*?)</title>", s, re.S) or [None, ""])[1].strip()
    desc  = (re.search(r'name="description" content="([^"]*)"', s) or [None, ""])[1]
    if len(title) > 60:
        long_t.append("%s (%d)" % (rel, len(title)))
    if not (110 <= len(desc) <= 170):
        long_d.append("%s (%d)" % (rel, len(desc)))
    if not re.search(r'property="og:image"', s):
        no_og.append(rel)

    # house rule: no em or en dashes, in metadata as well as visible copy
    for pat in (r"<title>(.*?)</title>",
                r'name="description" content="([^"]*)"',
                r'property="og:title" content="([^"]*)"',
                r'property="og:description" content="([^"]*)"'):
        if re.search(r"[—–]", (re.search(pat, s, re.S) or [None, ""])[1]):
            dashes.append(rel + " (metadata)")
    visible = re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[\s\S]*?</\1>", " ", s))
    if re.search(r"[—–]", visible):
        dashes.append(rel + " (visible copy)")

check("structure, links, images, ids, h1, schema", not structural, "; ".join(structural[:4]))
check("titles 60 chars or fewer", not long_t, ", ".join(long_t))
check("meta descriptions 110 to 170", not long_d, ", ".join(long_d))
check("og:image on every page", not no_og, ", ".join(no_og))
check("no em or en dashes anywhere", not dashes, ", ".join(sorted(set(dashes))))

# FAQ structured data must quote copy that is actually on the page
mismatch = []
for pg in glob.glob(DIST + "/services/*/index.html"):
    s = open(pg, encoding="utf-8").read()
    blocks = [b for b in re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', s)
              if json.loads(b).get("@type") == "FAQPage"]
    if not blocks:
        mismatch.append(os.path.basename(os.path.dirname(pg)) + ": no FAQPage")
        continue
    text = re.sub(r"<[^>]+>", "", s)
    for q in json.loads(blocks[0])["mainEntity"]:
        if q["name"] not in text:
            mismatch.append(q["name"][:30])
check("FAQ schema matches visible copy", not mismatch, "; ".join(mismatch[:3]))

home = open(os.path.join(DIST, "index.html"), encoding="utf-8").read()
check("journal cards", home.count('class="post" href="journal/') == EXPECT["posts"])
check("shop cards", home.count('class="shop-card"') == EXPECT["shop"])
check("press marquee", home.count('class="mq-item"') == EXPECT["marquee"])
check("rotating quotes", len(re.findall(r"^    '", home, re.M)) == EXPECT["quotes"])
check("service links", home.count('class="svc" href="services/') == EXPECT["services"])
for token in ["behold-widget", "gc.zgo.at", "maps.app.goo.gl", "curtain",
              'name="newsletter"', 'href="privacy/"', "BUILT:SERVICES"]:
    check("homepage retains " + token, token in home)
check("feed items", open(os.path.join(DIST, "feed.xml"), encoding="utf-8").read().count("<item>") == EXPECT["posts"])
check("sitemap urls", open(os.path.join(DIST, "sitemap.xml"), encoding="utf-8").read().count("<url>") == EXPECT["sitemap"])

css = open(os.path.join(ROOT, "article.css"), encoding="utf-8").read()
check("article.css braces balanced", css.count("{") == css.count("}"))
inline = re.search(r"<style>([\s\S]*?)</style>", home).group(1)
check("homepage css braces balanced", inline.count("{") == inline.count("}"))

for img in glob.glob(os.path.join(DIST, "*.jpg")) + glob.glob(os.path.join(DIST, "*.png")):
    check("%s under 600 KB" % os.path.basename(img), os.path.getsize(img) < 600_000,
          "%d KB" % (os.path.getsize(img) // 1024))

print("\n" + ("ALL CHECKS PASSED" if not fails else "FAILURES: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
