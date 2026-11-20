import json, re, subprocess, os

# reuse fetch_mblog_full-like show fetch via requests
import requests

COOKIE_FILE = os.path.expanduser("~/.hermes/scripts/weibo_cookie.txt")
cookie = ""
if os.path.exists(COOKIE_FILE):
    cookie = open(COOKIE_FILE).read().strip()

hdrs = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 "
                  "(KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://m.weibo.cn/detail/5367322716147946",
}
if cookie:
    hdrs["Cookie"] = cookie

r = requests.get("https://m.weibo.cn/statuses/show",
                 params={"id": "5367322716147946"}, headers=hdrs, timeout=25)
print("HTTP", r.status_code)
d = r.json()
data = d.get("data", {})
print("TEXT_HTML:", json.dumps(data.get("text"), ensure_ascii=False))
print("RAW_TEXT:", json.dumps(data.get("raw_text"), ensure_ascii=False))
print("isLongText:", data.get("isLongText"))
print("repost_type:", data.get("repost_type"))
print("pic_num:", data.get("pic_num"))
print("region:", data.get("region_name"))
# any img alt emoji?
html = data.get("text") or ""
print("IMG_ALTS:", re.findall(r'<img[^>]*alt="([^"]*)"', html))
