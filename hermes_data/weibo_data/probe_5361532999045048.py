import json, requests
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
wid = "5361532999045048"
r = requests.get("https://m.weibo.cn/statuses/show?id=" + wid,
                 headers={"User-Agent": MOBILE_UA,
                          "X-Requested-With": "XMLHttpRequest",
                          "Referer": "https://m.weibo.cn/detail/" + wid}, timeout=25)
j = r.json()
d = j.get("data", {})
print("ok:", j.get("ok"), "keys:", sorted(d.keys()))
print("pic_num:", d.get("pic_num"), "pics:", d.get("pics"))
print("page_info:", json.dumps(d.get("page_info"), ensure_ascii=False)[:500])
print("retweeted_status:", "YES" if d.get("retweeted_status") else "NO")
print("raw_text:", repr(d.get("raw_text")))
