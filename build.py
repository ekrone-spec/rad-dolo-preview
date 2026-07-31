#!/usr/bin/env python3
"""Rad Dolo site build.

Reads editable content from content/ (managed by the CMS at /admin) and
assembles the deployable site into dist/:
  - index.html   : journal cards, shop cards, publication marquee, quotes
                   injected between BUILD markers
  - journal/*/   : article pages rendered from templates/article.html
  - feed.xml     : RSS of journal posts (drives the Buttondown emailer)
  - sitemap.xml  : homepage + all posts
Static assets are copied through; archive/dev files are excluded from
production. Runs on Netlify (see netlify.toml); testable locally with
`python3 build.py`.
"""
import json, os, re, shutil, sys, html
from email.utils import format_datetime
from datetime import datetime, timezone

try:
    import markdown
except ImportError:
    sys.exit("python-markdown missing: python3 -m pip install --user markdown")

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
SITE = "https://www.raddolo.com"

EXCLUDE = {
    "dist", ".git", ".gitignore", "content", "templates", "netlify", "build.py",
    "netlify.toml", "package.json",
    # archives / working docs — not for production
    "hero-video.html", "experimental.html", "Snap.mp4", "YOUR ENERGY.mp4",
    "VIDEO-BRIEF.md", "blog-drafts.md", "testimonials.md",
    # retired shop card photos (cards now use CMS links / springflats+springbags)
    "shop-1.jpg", "shop-2.jpg",
    # heavy photo originals (web versions are blog-*.jpg)
    "WelcomeToRadsJournal.png", "whygettingdressedfeelsexhausting.png", "KEEPDONATEMAYBE.JPG",
    "ShopYourClosetFirst.jpeg", "OneSuitcaseEveryDayHandled.jpeg", "WorseThanTheDentist.HEIC",
    # generated fresh below
    "feed.xml", "sitemap.xml", "journal",
}

# ---------- load content ----------
def load_posts():
    posts = []
    cdir = os.path.join(ROOT, "content", "journal")
    for fn in os.listdir(cdir):
        if not fn.endswith(".md"):
            continue
        raw = open(os.path.join(cdir, fn), encoding="utf-8").read()
        m = re.match(r"---\n([\s\S]*?)\n---\n?([\s\S]*)", raw)
        if not m:
            continue
        fm, body = m.groups()
        meta = {}
        for line in fm.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        date = str(meta.get("date", "2026-01-01"))[:10]
        posts.append({
            "slug": fn[:-3],
            "title": meta.get("title", "Untitled"),
            "date": date,
            "category": meta.get("category", "The journal"),
            "minutes": str(meta.get("minutes", "2")),
            "description": meta.get("description", ""),
            "image": (meta.get("image", "") or "").lstrip("/"),
            "body_md": body.strip(),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts

def prose_html(p):
    out = markdown.markdown(p["body_md"])
    # first paragraph becomes the lead
    return re.sub(r"<p>", '<p class="lead">', out, count=1)

posts = load_posts()
shop = json.load(open(os.path.join(ROOT, "content", "shop.json"), encoding="utf-8"))["items"]
pubs = json.load(open(os.path.join(ROOT, "content", "publications.json"), encoding="utf-8"))["items"]
quotes = json.load(open(os.path.join(ROOT, "content", "quotes.json"), encoding="utf-8"))["items"]

# ---------- dist skeleton ----------
if os.path.exists(DIST):
    shutil.rmtree(DIST)
os.makedirs(DIST)

for name in os.listdir(ROOT):
    if name in EXCLUDE or name.startswith("."):
        continue
    src = os.path.join(ROOT, name)
    dst = os.path.join(DIST, name)
    (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, dst)

# CMS uploads live in images/uploads (created on first upload)
os.makedirs(os.path.join(DIST, "images", "uploads"), exist_ok=True)

# ---------- helpers ----------
def urlenc(s):
    from urllib.parse import quote
    return quote(s, safe="")

def replace_region(doc, name, payload, comment=("<!-- BUILD:%s -->", "<!-- /BUILD:%s -->")):
    a, b = comment[0] % name, comment[1] % name
    i, j = doc.index(a), doc.index(b) + len(b)
    return doc[:i] + a.replace("BUILD", "BUILT") + "\n" + payload + "\n" + a.replace("BUILD:", "/BUILT:") + doc[j:]

def js_region(doc, name, payload):
    a, b = "// BUILD:%s" % name, "// /BUILD:%s" % name
    i, j = doc.index(a), doc.index(b) + len(b)
    return doc[:i] + "\n" + payload + "\n  " + doc[j:]

def shop_img_src(item):
    img = (item.get("image") or "").strip()
    if img:
        return img.lstrip("/") if not img.startswith("http") else img
    return "/.netlify/functions/shop-image?u=" + urlenc(item["url"])

# ---------- index.html ----------
doc = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

def post_img_ok(p):
    return bool(p["image"]) and os.path.exists(os.path.join(ROOT, p["image"]))

cards = []
for p in posts:
    pic = "<i style=\"background-image:url('%s')\"></i>" % html.escape(p["image"]) if post_img_ok(p) else "<i></i>"
    cards.append(
        '        <a class="post" href="journal/%s/">\n'
        "          <span class=\"pic\">%s</span>\n"
        "          <p class=\"meta\">%s · %s min</p>\n"
        "          <h3>%s</h3>\n"
        "          <p>%s</p>\n"
        "        </a>" % (p["slug"], pic, html.escape(p["category"]),
                          p["minutes"], html.escape(p["title"]), html.escape(p["description"])))
doc = replace_region(doc, "JOURNAL_CARDS", "\n".join(cards))

scards = []
for it in shop:
    scards.append(
        '        <a class="shop-card" href="%s" target="_blank" rel="noopener noreferrer">\n'
        '          <span class="pic"><img src="%s" alt="%s" loading="lazy"></span>\n'
        '          <span class="cap"><span>%s</span><span class="arw" aria-hidden="true"></span></span>\n'
        "        </a>" % (html.escape(it["url"]), html.escape(shop_img_src(it)),
                          html.escape(it["title"]), html.escape(it["title"])))
doc = replace_region(doc, "SHOP_CARDS", "\n".join(scards))

def mq(items, hidden=False):
    extra = ' aria-hidden="true" tabindex="-1"' if hidden else ""
    out = []
    for it in items:
        out.append('        <a class="mq-item" href="%s" target="_blank" rel="noopener noreferrer"%s>'
                   '<img src="%s" alt="%s" loading="lazy"></a>'
                   % (html.escape(it["url"]), extra, html.escape(it["logo"].lstrip("/")),
                      "" if hidden else html.escape(it["name"])))
    return "\n".join(out)
doc = replace_region(doc, "MARQUEE", mq(pubs) + "\n" + mq(pubs, hidden=True))

doc = js_region(doc, "QUOTES", ",\n".join("    '%s'" % q.replace("'", "\\'") for q in quotes))
open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(doc)

# ---------- article pages ----------
tpl = open(os.path.join(ROOT, "templates", "article.html"), encoding="utf-8").read()
for i, p in enumerate(posts):
    others = [q for q in posts if q["slug"] != p["slug"]][:3]
    more = "\n".join(
        '          <li><a href="../%s/">%s<i class="ar" aria-hidden="true"></i></a></li>'
        % (q["slug"], html.escape(q["title"])) for q in others)
    page = tpl
    if not post_img_ok(p):
        # photo not added yet: gray feature block, real hero as the share image
        page = page.replace("<i style=\"background-image:url('../../{{IMAGE_BASENAME}}')\"></i>", "<i></i>")
        page = page.replace("{{IMAGE_BASENAME}}", "hero.jpg")
    page = (page.replace("{{TITLE_JSON}}", p["title"].replace('"', '\\"'))
               .replace("{{TITLE_URL}}", urlenc(p["title"]))
               .replace("{{TITLE}}", html.escape(p["title"]))
               .replace("{{SLUG}}", p["slug"])
               .replace("{{DESCRIPTION}}", html.escape(p["description"]))
               .replace("{{CATEGORY}}", html.escape(p["category"]))
               .replace("{{MINUTES}}", p["minutes"])
               .replace("{{IMAGE_BASENAME}}", p["image"])
               .replace("{{PROSE}}", prose_html(p))
               .replace("{{MORE_ITEMS}}", more))
    d = os.path.join(DIST, "journal", p["slug"])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)

# ---------- feed.xml ----------
def rfc822(date):
    return format_datetime(datetime(*[int(x) for x in date.split("-")], 12, 0, 0, tzinfo=timezone.utc))

items = "\n".join("""  <item>
    <title>%s</title>
    <link>%s/journal/%s/</link>
    <guid>%s/journal/%s/</guid>
    <pubDate>%s</pubDate>
    <description>%s</description>
  </item>""" % (html.escape(p["title"]), SITE, p["slug"], SITE, p["slug"],
                rfc822(p["date"]), html.escape(p["description"])) for p in posts)
open(os.path.join(DIST, "feed.xml"), "w", encoding="utf-8").write(
"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>Rad Dolo — The Journal</title>
  <link>%s/</link>
  <description>Notes on getting dressed, from Minneapolis personal stylist Rad Dolo.</description>
  <language>en-us</language>
  <atom:link href="%s/feed.xml" rel="self" type="application/rss+xml"/>
%s
</channel>
</rss>
""" % (SITE, SITE, items))

# ---------- sitemap.xml ----------
urls = ["  <url>\n    <loc>%s/</loc>\n    <changefreq>monthly</changefreq>\n    <priority>1.0</priority>\n  </url>" % SITE]
urls += ["  <url>\n    <loc>%s/journal/%s/</loc>\n    <changefreq>yearly</changefreq>\n    <priority>0.8</priority>\n  </url>" % (SITE, p["slug"]) for p in posts]
open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8").write(
'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(urls))

print("build ok: %d posts, %d shop, %d publications, %d quotes" % (len(posts), len(shop), len(pubs), len(quotes)))
