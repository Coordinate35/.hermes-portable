import requests, re
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
s = requests.Session()
s.headers.update({"User-Agent": UA})

tcn = "http://t.cn/AXjNEY5a"
r = s.get(tcn, allow_redirects=True, timeout=25)
print("TCN final:", r.status_code, r.url, "len", len(r.text))
body = r.text
for kw in ["共", "张图片", "compic", "comment"]:
    print(kw, "count:", body.count(kw))
m = re.findall(r'共\s*(\d+)\s*张图片', body)
print("multi_count:", m)
imgs = re.findall(r'https?://[^"\'\s<>]+?\.(?:jpg|jpeg|png)', body)
print("imgs:", list(dict.fromkeys(imgs))[:6])
print("title_hint:", (re.search(r'<title>(.*?)</title>', body, re.S).group(1).strip() if re.search(r'<title>(.*?)</title>', body, re.S) else None))
print("text_snip:", re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', body))[:400])

img = "https://wx2.sinaimg.cn/large/007unzIely1iihsf06kj3j31c01s0kjm.jpg"
ri = s.get(img, timeout=25)
print("IMG:", ri.status_code, ri.headers.get("Content-Type"), ri.headers.get("Content-Length"))
