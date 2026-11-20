import json, os, sys
from urllib.parse import unquote, urlparse, parse_qs

sys.path.insert(0, os.path.expanduser("~/.hermes/skills/data-collection/weibo-monitoring/scripts"))
import link_cache as lc

vj = json.load(open(os.path.expanduser("~/hermes_data/weibo_data/wb_verify_5367322716147946.json")))
sinaurl = [h for h in vj["hrefs"] if "sinaurl" in h][0]
inner = parse_qs(urlparse(sinaurl).query)["u"][0]
clean = inner.split("?")[0]

payload = {
    "url": clean,
    "sinaurl": sinaurl,
    "kind": "toutiao_video",
    "title": "#震惊！卢麒元震撼论断！# - 今日头条",
    "author": "王力",
    "date": "2026-11-14T04:51:32+08:00",
    "extra": "时长PT9M16S；标题与微博正文逐字一致；分享者@卢麒元 2026-11-20 13:35:18；完整分享URL:" + inner,
}
rec = lc.store(payload)
d = lc._load()
d["aliases"][lc._norm(inner)] = lc._norm(clean)
lc._save(d)
print("STORED", clean)
print("clean=%r" % clean)
print("inner_len", len(inner))
for u in (clean, inner, sinaurl):
    r = lc.lookup(u)
    print("HIT?" , bool(r), u[:70])
