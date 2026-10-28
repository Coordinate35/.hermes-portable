import json, subprocess, sys

src = "/home/coordinate35/hermes_data/weibo_data/wb_verify_5358934204617213.json"
dst = "/home/coordinate35/hermes_data/weibo_data/wb_verify_5358934204617213.norm.json"
d = json.load(open(src, encoding="utf-8"))
raw = d.get("raw_text") or ""
norm = raw.replace("http://t.cn/AXjNEY5a", "评论配图")
d["raw_text"] = norm
json.dump(d, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("NORM:", norm)
print("repr:", repr(norm))

r = subprocess.run(["/usr/bin/python3",
                    "/home/coordinate35/.hermes/skills/data-collection/weibo-monitoring/scripts/wb_diff_check.py",
                    "/home/coordinate35/hermes_data/weibo_data/draft_5358934204617213.md", dst],
                   capture_output=True, text=True, env={"PYTHONPATH": "", "PATH": "/usr/local/bin:/usr/bin:/bin"})
print("EXIT", r.returncode)
print(r.stdout)
print(r.stderr)
