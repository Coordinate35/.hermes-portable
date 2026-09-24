#!/usr/bin/env python3
"""生成 2026-09-24 15:51 轮交付稿（3 帖，时间升序）。raw_text 直接取自核验 JSON，零转录。"""
import json
import re

fn_json = '/home/coordinate35/hermes_data/weibo_data/verify_3posts_20260924_1551.json'
fn_out = '/home/coordinate35/hermes_data/weibo_data/delivery_20260924_1551.txt'
data = json.load(open(fn_json, encoding='utf-8'))

meta = [
    ('5346699084303732', '09-24 15:44:21', '转20 · 评1 · 赞47',
     '回复网友 @万里长城万里长-（问「老师，金是底了吗」）：这个问题的另一面是美元价值回归——美元重置的另一面是人民币价值回归，'
     '而人民币升值又面临广场协议的陷阱；极复杂的圈套型难题，解题思路不在经济层面：去殖、除阀、削藩、均田，下长安。'),
    ('5346699965104242', '09-24 15:47:50', '转10 · 评1 · 赞26',
     '回复网友 @韦羽田先生（问五道口论坛「中央化地方债、发债扩大投资基建」怎么看）：给出一套组合——水循环系统性建设、'
     '直接税立法、人民币发行立法、全体国民无差别社会保障；环环相扣即可解决问题，但需要大智慧与极强悍的执行力。'),
    ('5346700325816668', '09-24 15:49:17', '转3 · 评2 · 赞14',
     '回复网友 @惟精惟一和允执厥中（建议老师休息、将来讲讲毛选）：一直在读教员的年谱，将来闲时想讲一讲教员晚年的思考与努力。'),
]

preamble = ('核验完成：3 条原文与 show 端点逐字节一致（show / pc longtext / extend 三源交叉核验，'
            '渲染页展开全文=0）；第 1 级 TTS 成功。交付如下：')

parts = [preamble, '']
for wid, t, stats, summ in meta:
    raw = data[wid]['show']['raw_text']
    parts.append(f'**@卢麒元 · 新微博 · {t} · 华为Mate XT 非凡大师**（{stats}）')
    parts.append('')
    parts.append('📌 总结')
    parts.append(summ)
    parts.append('')
    parts.append('📄 完整原文')
    parts.append(raw)
    parts.append('')

note = ('📎 注\n'
        '三条「回复@」前缀均有；[祈祷][蜡烛][嘻嘻][作揖] 为微博端表情符（show raw_text / pc longtext / extend '
        '三源一致、渲染页展开全文=0）；三条引用链均按微博端原样照发、未延伸——第 1、2 条链完整止于「…看法[嘻嘻][嘻嘻]」，'
        '第 3 条微博端折叠止于「…不花眼不迷路。[祈祷]//」。三条帖内均挂同一转发卡片：卢麒元 09-22 帖（5345896352975977，'
        '此前已推送），卡片不并入正文；链中「@卢麒元/@唐山-12度」段此前已随相关帖推送，按微博端原样保留。')
parts.append(note)
parts.append('')
parts.append('🔧 例行维护：weibo-monitoring skill 已补记本轮 3 帖实例与「万里长城万里长-」口播读法。')
parts.append('')
parts.append('🎙️ 语音由 Windows TTS 生成（第1级）')
parts.append('MEDIA:/tmp/weibo_voice.wav')

text = '\n'.join(parts)
with open(fn_out, 'w', encoding='utf-8') as f:
    f.write(text)
print('WROTE', fn_out)
print('len', len(text))
bl = re.findall(r'📄 完整原文\n(.+?)(?:\n\n)', text)
print('blocks:', len(bl))
for b in bl:
    print('  head:', b[:22], '| tail:', b[-18:])
