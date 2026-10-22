import requests, json
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
wid = "5356799538760842"
raw = "回复@源溪nice:[祈祷]//@源溪nice:老师，今天您也需要报平安的[给你小心心]"
page_txt = "回复@源溪nice://@源溪nice:老师，今天您也需要报平安的"
r = requests.get(f"https://m.weibo.cn/status/{wid}?_=3", headers={"User-Agent": MOBILE_UA, "Referer": f"https://m.weibo.cn/detail/{wid}"}, timeout=25)
print("status", r.status_code, "len", len(r.text), "visitor", "Sina Visitor System" in r.text)
h = r.text
# html-escaped variants
import html as H
variants = {raw, H.escape(raw), json.dumps(raw, ensure_ascii=False)[1:-1], json.dumps(raw, ensure_ascii=True)[1:-1]}
hits = {v: h.count(v) for v in variants}
print("raw_text hits:", hits)
print("pray img alt:", h.count('[祈祷]'), "| 给你小心心:", h.count('[给你小心心]'))
