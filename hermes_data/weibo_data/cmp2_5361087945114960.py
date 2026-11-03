import json, re

v = json.load(open('/home/coordinate35/hermes_data/weibo_data/wb_verify_5361087945114960.json'))
rt_text = v['retweeted_status']['text_stripped']
art = open('/home/coordinate35/hermes_data/weibo_data/articles/关于组建中国资本市场投资基金的建议_2026-11-01.md', encoding='utf-8').read()

start = art.find('一、当前我国资本运行的核心问题')
end = art.find('*注：')
body = art[start:end]

def norm(s):
    s = s.replace('\u3000', '')
    s = re.sub(r'\s+', '', s)
    return s

n_rt = norm(rt_text)
n_body = norm(body)
print('rt_len', len(n_rt), 'body_len', len(n_body))
print('body in rt:', n_body in n_rt)
print('rt in body:', n_rt in n_body)
# 逐段比对：按段（文章空行分段）检查每段规范化后是否在 rt 中
paras = [p for p in body.split('\n\n') if p.strip()]
missing = []
for p in paras:
    np_ = norm(p)
    if np_ and np_ not in n_rt:
        missing.append(np_[:40])
print('paras', len(paras), 'missing', len(missing))
for m in missing:
    print('MISS:', m)
# rt 中多出的部分（去掉文章段落后）
tail = n_rt[n_rt.find(n_body):] if n_body in n_rt else None
print('tail_after_body:', repr(tail[:60]) if tail else None)
print('rt tail 40:', repr(n_rt[-40:]))
