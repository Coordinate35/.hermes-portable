import re, json, requests

MOBILE_UA = ("Mozilla/5.0 (Linux; Android 12; HarmonyOS; HUAWEI Mate XT) "
             "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
             "Chrome/114.0.0.0 Mobile Safari/537.36")

url = ("https://m.toutiao.com/video/7707761098446979645/"
       "?app=news_article&timestamp=1795152562&utm_campaign=client_share"
       "&is_hit_share_recommend=0&category_new=headline"
       "&upstream_biz=harmony_share_os&origin=system")

r = requests.get(url, headers={"User-Agent": MOBILE_UA}, timeout=30)
print("HTTP", r.status_code, "bytes", len(r.content))
html = r.text

t = re.search(r"<title>(.*?)</title>", html, re.S)
print("TITLE:", t.group(1).strip() if t else None)
for k in ["og:title", "og:description"]:
    m = re.search(r'<meta[^>]+property="%s"[^>]+content="([^"]*)"' % re.escape(k), html)
    print(k.upper() + ":", m.group(1) if m else None)

m = re.search(r'class="author-info-name"[^>]*>(.*?)<', html, re.S)
print("AUTHOR:", m.group(1).strip() if m else None)
m = re.search(r'class="author-info-desc"[^>]*>(.*?)<', html, re.S)
print("AUTHOR_DESC:", m.group(1).strip() if m else None)

for sm in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
    try:
        d = json.loads(sm.group(1))
    except Exception as e:
        print("LDJSON parse err", e)
        continue
    print("LDJSON type:", d.get("@type"))
    print("  name:", d.get("name"))
    print("  uploadDate:", d.get("uploadDate"))
    print("  duration:", d.get("duration"))
    if isinstance(d.get("author"), dict):
        print("  author:", d["author"].get("name"))
    print("  description:", (d.get("description") or "")[:300])

# save raw for reference
with open("/home/coordinate35/hermes_data/weibo_data/toutiao_7707761098446979645.html", "w", encoding="utf-8") as f:
    f.write(html)
