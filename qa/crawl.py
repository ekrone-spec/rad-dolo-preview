#!/usr/bin/env python3
"""Live-site crawl. Checks what visitors and Google actually get.

    python3 qa/crawl.py                        # crawls https://www.raddolo.com
    python3 qa/crawl.py http://localhost:8899  # or a local preview

Follows internal links from the homepage, so unlinked pages (404.html) are out
of scope by design — qa/audit.py covers those. Exits non zero on failure.
"""
import json, re, sys, urllib.error, urllib.request
from urllib.parse import urljoin, urlparse

SITE = (sys.argv[1] if len(sys.argv) > 1 else "https://www.raddolo.com").rstrip("/")
HOST = urlparse(SITE).netloc
UA = {"User-Agent": "Mozilla/5.0 (compatible; TCStudioQA/1.0)"}
issues = []

def fetch(url, method="GET"):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA, method=method), timeout=30)
        return r.status, dict(r.headers), (r.read() if method == "GET" else b"")
    except urllib.error.HTTPError as e:
        # keep the body — error pages (404) are themselves worth checking
        return e.code, dict(e.headers), (e.read() if method == "GET" else b"")
    except Exception:
        return 0, {}, b""

# ---------- crawl ----------
seen, queue, html_pages = set(), [SITE + "/"], {}
while queue:
    u = queue.pop(0)
    if u in seen:
        continue
    seen.add(u)
    st, hd, body = fetch(u)
    if st != 200:
        issues.append("%s -> HTTP %s" % (urlparse(u).path, st))
        continue
    if "text/html" not in hd.get("Content-Type", ""):
        continue
    html_pages[u] = body.decode("utf-8", "replace")
    for m in re.findall(r'href="([^"]+)"', html_pages[u]):
        if m.startswith(("mailto:", "#", "data:", "javascript:")):
            continue
        full = urljoin(u, m).split("#")[0]
        if urlparse(full).netloc == HOST and full not in seen and "/admin" not in full:
            queue.append(full)

print("crawled %d pages from the homepage\n" % len(html_pages))

titles, descs, canons = {}, {}, {}
for u, h in sorted(html_pages.items()):
    path = urlparse(u).path
    t = (re.search(r"<title>(.*?)</title>", h, re.S) or [None, ""])[1].strip()
    d = (re.search(r'name="description" content="([^"]*)"', h) or [None, ""])[1]
    c = (re.search(r'<link rel="canonical" href="([^"]*)"', h) or [None, ""])[1]
    print("%-44s title %3d  desc %3d" % (path, len(t), len(d)))
    if not t: issues.append(path + ": no title")
    if not d: issues.append(path + ": no meta description")
    if not c: issues.append(path + ": no canonical")
    if len(t) > 60: issues.append("%s: title %d chars" % (path, len(t)))
    if d and not (110 <= len(d) <= 170): issues.append("%s: description %d chars" % (path, len(d)))
    if len(re.findall(r"<h1", h)) != 1: issues.append("%s: %d h1 tags" % (path, len(re.findall(r"<h1", h))))
    if not re.search(r'property="og:image"', h): issues.append(path + ": no og:image")
    for b in re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', h):
        try: json.loads(b)
        except Exception as e: issues.append("%s: invalid JSON-LD (%s)" % (path, str(e)[:40]))
    titles.setdefault(t, []).append(path)
    descs.setdefault(d, []).append(path)
    canons.setdefault(c, []).append(path)

for label, group in (("title", titles), ("description", descs), ("canonical", canons)):
    for val, paths in group.items():
        if val and len(paths) > 1:
            issues.append("duplicate %s: %s" % (label, ", ".join(paths)))

# ---------- assets ----------
assets = set()
for u, h in html_pages.items():
    for m in re.findall(r'(?:src|href)="([^"]+\.(?:jpe?g|png|svg|css|js|webp|ico))"', h):
        assets.add(urljoin(u, m))
    for m in re.findall(r"background-image:url\('([^']+)'\)", h):
        assets.add(urljoin(u, m))
for a in sorted(assets):
    st, hd, _ = fetch(a, "HEAD")
    if st != 200:
        issues.append("asset %s -> %s" % (a.split("/")[-1], st))
    elif hd.get("Content-Length", "").isdigit() and int(hd["Content-Length"]) > 600_000:
        issues.append("asset %s -> %d KB" % (a.split("/")[-1], int(hd["Content-Length"]) // 1024))
print("\nchecked %d assets" % len(assets))

# ---------- external links ----------
external = {m for h in html_pages.values() for m in re.findall(r'href="(https?://[^"]+)"', h)
            if HOST not in m and not m.rstrip("/").endswith(("fonts.googleapis.com", "fonts.gstatic.com"))}
for e in sorted(external):
    st, _, _ = fetch(e, "HEAD")
    if st in (0, 404, 410, 500, 503):
        st, _, _ = fetch(e)          # some hosts reject HEAD
    if st in (0, 404, 410, 500, 503):
        issues.append("external link %s -> %s" % (e[:70], st))
    elif st == 403:
        print("  note: %s returns 403 to bots (usually fine in a browser)" % urlparse(e).netloc)
print("checked %d external links" % len(external))

# ---------- headers, redirects, infra ----------
if SITE.startswith("https"):
    _, hd, _ = fetch(SITE + "/", "HEAD")
    for k in ["strict-transport-security", "content-security-policy", "x-frame-options",
              "x-content-type-options", "referrer-policy"]:
        if not any(kk.lower() == k for kk in hd):
            issues.append("missing security header: " + k)

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    op = urllib.request.build_opener(NoRedirect)
    for src, want in [("http://raddolo.com/", 301), ("https://raddolo.com/", 301),
                      (SITE + "/blank", 301), (SITE + "/blank-1", 301),
                      (SITE + "/reviews", 301), (SITE + "/contact", 301)]:
        try:
            code = op.open(urllib.request.Request(src, headers=UA), timeout=20).status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception:
            code = 0
        if code != want:
            issues.append("%s returned %s, expected %s" % (src, code, want))

    st, _, body = fetch(SITE + "/this-page-does-not-exist")
    if st != 404:
        issues.append("missing page returned %s, expected 404" % st)
    elif b"This look doesn" not in body:
        issues.append("404 page is not the branded one")

print("\n=== ISSUES (%d) ===" % len(issues))
for i in issues:
    print(" -", i)
if not issues:
    print(" none")
sys.exit(1 if issues else 0)
