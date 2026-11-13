import json, requests, re, os

wid = "5364762670010514"
p = os.path.expanduser("~/hermes_data/weibo_data/wb_verify_%s.json" % wid)
d = json.load(open(p))
for k in ("raw_text", "text_stripped", "long_text", "pc_longtext"):
    v = d.get(k)
    if v is None:
        print(k, "= None"); continue
    i = v.find("新数据")
    print(k, "len=%d" % len(v), "seg=", repr(v[max(0,i-25):i+12]))

print("\n=== refetch show ===")
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
h = {"User-Agent": UA, "X-Requested-With": "XMLHttpRequest",
     "Referer": "https://m.weibo.cn/detail/%s" % wid}
r = requests.get("https://m.weibo.cn/statuses/show?id=" + wid, headers=h, timeout=30)
j = r.json()
data = j.get("data", {})
rt = data.get("raw_text")
tx = data.get("text")
print("status", j.get("ok"), r.status_code)
for name, v in (("show.raw_text", rt), ("show.text(html)", tx)):
    if not v:
        print(name, "empty"); continue
    i = v.find("新数据")
    print(name, "len=%d" % len(v), "seg=", repr(v[max(0, i-25):i+12]))
