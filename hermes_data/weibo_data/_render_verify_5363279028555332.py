import json, re, sys, os
import requests
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
import weibo_monitor as w

WID = "5363279028555332"
RAW = "回复@几斤几两称了知道:[鲜花]//@几斤几两称了知道:刚刚预订！准备拜读！重回已经醍醐灌顶，渴望重温的洗礼//@卢麒元:[鲜花]"

for url in [f"https://m.weibo.cn/status/{WID}?_=4", f"https://m.weibo.cn/detail/{WID}?_=4"]:
    r = requests.get(url, headers=w.HEADERS, cookies=w.COOKIES, timeout=25, allow_redirects=True)
    txt = r.text
    print(url, r.status_code, "len", len(txt), "wall", "Sina Visitor System" in txt)
    print("occ(raw_text):", txt.count(RAW))
    print("occ(plain):", txt.count(RAW.replace("[鲜花]", "")))
    for kw in ["展开全文", "查看全文", "查看更多", "全文"]:
        print(f"  {kw}", txt.count(kw))
    i = txt.find(RAW)
    if i >= 0:
        print("CTX:", txt[max(0, i-160):i+len(RAW)+160].replace("\n", "\\n"))
    else:
        i2 = txt.find("几斤几两称了知道")
        print("CTX2:", txt[max(0, i2-200):i2+500].replace("\n", "\\n") if i2 >= 0 else "none")
    print("---")
