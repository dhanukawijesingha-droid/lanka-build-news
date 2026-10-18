import json, re, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

QUERIES = [
    "Sri Lanka construction",
    "Sri Lanka highway OR expressway OR bridge construction",
    "Sri Lanka housing project OR apartment project",
    "Sri Lanka cement OR steel OR bitumen price",
    "Sri Lanka tender construction OR RDA OR UDA",
    "Sri Lanka CIDA OR NCASL OR contractors",
]
KEEP = re.compile(r"construct|build|road|highway|expressway|bridge|housing|apartment|cement|steel|bitumen|tender|contractor|infrastructure|RDA|UDA|CIDA|NCASL|real estate|engineer", re.I)
MAX_AGE_DAYS = 30
MAX_ITEMS = 150

def fetch(q):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q + " when:7d", "hl": "en-LK", "gl": "LK", "ceid": "LK:en"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return ET.fromstring(r.read())

def parse(root):
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        src = it.find("source")
        source = (src.text if src is not None else "").strip()
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3]
        try:
            d = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc)
        except Exception:
            continue
        yield {"title": title, "source": source or "News",
               "date": d.strftime("%Y-%m-%d"), "url": (it.findtext("link") or "").strip()}

try:
    old = json.load(open("news.json")).get("items", [])
except Exception:
    old = []

items = {i["title"].lower(): i for i in old}
for q in QUERIES:
    try:
        for i in parse(fetch(q)):
            if KEEP.search(i["title"]):
                items.setdefault(i["title"].lower(), i)
    except Exception as e:
        print("skip", q, e)

cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)).strftime("%Y-%m-%d")
out = sorted((i for i in items.values() if i["date"] >= cutoff), key=lambda i: i["date"], reverse=True)[:MAX_ITEMS]
json.dump({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "items": out},
          open("news.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "items")
