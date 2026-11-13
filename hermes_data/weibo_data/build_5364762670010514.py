import json, os, sys
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/data-collection/weibo-monitoring/scripts"))
import link_cache

WID = "5364762670010514"
BASE = os.path.expanduser("~/hermes_data/weibo_data")
vj = json.load(open(os.path.join(BASE, "wb_verify_%s.json" % WID)))
raw = vj["raw_text"]
TXT = raw.replace("http://t.cn/AXYQbbe7", "评论配图")
assert TXT != raw, "t.cn replacement failed"

# 1) normalized baseline for diff
norm = dict(vj)
norm["raw_text"] = TXT
json.dump(norm, open(os.path.join(BASE, "wb_verify_%s.norm.json" % WID), "w"), ensure_ascii=False, indent=1)

# 2) link cache store (image url + sinaurl alias + t.cn alias)
IMG = "https://wx2.sinaimg.cn/large/008YxVRsly1iizlecebikj61400u0qbm08.jpg"
SINA = "https://weibo.cn/sinaurl?u=https%3A%2F%2Fwx2.sinaimg.cn%2Flarge%2F008YxVRsly1iizlecebikj61400u0qbm08.jpg"
rec = link_cache.store({
    "url": IMG,
    "sinaurl": SINA,
    "kind": "weibo_compic",
    "title": "评论配图（书页照片：做大官·做大商·做大家）",
    "author": "真诚黄金",
    "date": "2026-11-13",
    "extra": "微博 %s 回复链内 @真诚黄金 评论附图；1440x1080 JPEG；t.cn/AXYQbbe7" % WID,
})
link_cache.store({"url": IMG, "sinaurl": "http://t.cn/AXYQbbe7", "kind": "weibo_compic"})
print("stored:", rec["url"], rec.get("kind"))

# 3) draft
draft = """**@正心以中and修身以和 · 新微博 · 11-13 12:02:36 · 来源 iPhone 16e**（转 0 · 评 0 · 赞 7）

📌 总结
回复@真诚黄金，回复内容仅一个[祈祷]；对方评论为「当然是卢先生啊」并附一张书页照片（谈做大官、做大商、做大家）。链上所引的两条本帖（11-11 17:45 回复帖、10-01 国庆帖）此前均已推送。

📄 完整原文
%s

📎 注
① 本帖为回复链帖（repost_type=4）：留言落在其本人 11-11 17:45「回复@小人12131」帖（5364124293792969）评论区；帖内转发卡片＝卢麒元 10-01 09:28:03 国庆帖（5349141099580843）。链内所引两帖均此前已推送，不重复附全文，微博端原样止于「…恭祝国庆快乐！」。
② 原文中「评论配图」为链接显示文案，实际指向 @真诚黄金 的评论附图：%s（HTTP 200，1440×1080 JPEG），原短链 http://t.cn/AXYQbbe7 。附图内容为书页照片，谈「做大官／做大商／做大家」三种选择，并称「大官和大商是不入史的」，只有「大家」能留在历史里。
""" % (TXT, IMG)

p = os.path.join(BASE, "draft_%s.md" % WID)
open(p, "w", encoding="utf-8").write(draft)
print("draft:", p, len(draft), "chars")
print("TXT len:", len(TXT))
