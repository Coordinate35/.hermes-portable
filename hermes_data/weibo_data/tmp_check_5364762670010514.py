import re, json, requests, sys

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
wid = sys.argv[1] if len(sys.argv) > 1 else "5364762670010514"
url = f"https://m.weibo.cn/status/{wid}?_=3"
r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
html = r.text
print("status", r.status_code, "len", len(html))

# 1) find contexts around 新数据
for m in re.finditer("新数据", html):
    s = max(0, m.start()-60); e = min(len(html), m.end()+60)
    print("CTX:", repr(html[s:e]))
    print("---")

# 2) pull render_data status text
m = re.search(r"var \$render_data = (\[.*?\])\[0\] \|\| \{\};", html, re.S)
if m:
    try:
        rd = json.loads(m.group(1))
        st = rd[0].get("status", {})
        print("RENDER raw_text:", repr(st.get("raw_text")))
        print("RENDER text:", repr(st.get("text")))
    except Exception as ex:
        print("parse err", ex)
else:
    print("no render_data block")
