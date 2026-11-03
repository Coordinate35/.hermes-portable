import json, re, sys

v = json.load(open('/home/coordinate35/hermes_data/weibo_data/wb_verify_5361087945114960.json'))
rt = v['retweeted_status']
rt_text = rt['text_stripped']

# 11-01 已推送的公众号/头条文章转录
art = open('/home/coordinate35/hermes_data/weibo_data/articles/关于组建中国资本市场投资基金的建议_2026-11-01.md', encoding='utf-8').read()
# 去掉 markdown 标题行与可能的注释
art_body = art

def norm(s):
    s = s.replace('\u3000', '')
    s = re.sub(r'\s+', '', s)
    return s

n_rt = norm(rt_text)
n_art = norm(art_body)
print('rt_len', len(n_rt), 'art_len', len(n_art))
print('rt_contains_art_norm:', n_art in n_rt)
print('art_contains_rt_norm:', n_rt in n_art)
# 找出首个差异
m = min(len(n_rt), len(n_art))
i = 0
while i < m and n_rt[i] == n_art[i]:
    i += 1
print('first_diff_idx', i)
print('rt_ctx:', repr(n_rt[max(0,i-40):i+60]))
print('art_ctx:', repr(n_art[max(0,i-40):i+60]))
print('rt_tail:', repr(n_rt[-80:]))
print('art_tail:', repr(n_art[-80:]))
print('rt_head:', repr(n_rt[:60]))
