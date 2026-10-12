# 子代理精读任务 prompt 模板（可直接改书名/章节号复用）

用法：delegate_task 并行派 5 路。每路一个 task，改 `<书名>`、`<章节文件列表>`、`<该路内容提示>` 即可。
2026-09 用此模板精读《货币强权》74 节/24.8 万字，5 路中 4 路按约 90-130s 完成，1 路超时（启用兜底自读）。

## 模板正文（每个 task 原样改写）

context（背景，子代理看不到对话历史，必须自包含）：

```
你负责《<书名>》(<作者>著，<译者>译，<出版社>) 的第 <N> 部分：<章节范围>。
章节文件路径格式：/home/coordinate35/hermes_data/ebooks/<书名>/chapters/NNN.txt
（NNN 为三位数字，如 004.txt、005.txt）。用 read_file 逐个读取以下文件（必须先真正读取，
绝对不许凭书名猜测内容）：<列出文件号及标题，如 020.txt(先前的讨论) ...>。
<该路内容提示：2-3 句，说明各节主题、哪几节最长最该详读、章节间的逻辑关系。>
```

goal（任务要求）：

```
精读《<书名>》<章节范围>（即章节文件 <起> 到 <止>），输出详实的中文结构化笔记（<1500-3500>字），包括：
(1) 逐节主题与要点；(2) 本部分最重要的概念定义，必须用原文中的释义（引用原句）；
(3) 本部分的逻辑脉络（作者如何一步步推导）；(4) 作者在本部分的结论/主张。
要求：只写书中真实存在的内容；引用原文关键句用『』引号并注明出自哪个小节；
不得编造、不得添加书中没有的观点；若某个文件读不到需明确报告。
```

output_schema（会告诉子代理 final answer 需符合 JSON Schema）：

```json
{
  "properties": {
    "part": {"type": "string"},
    "sections": {
      "items": {
        "properties": {
          "file": {"type": "string"},
          "title": {"type": "string"},
          "summary": {"type": "string"},
          "key_quotes": {"items": {"type": "string"}, "type": "array"}
        },
        "required": ["file", "title", "summary"],
        "type": "object"
      },
      "type": "array"
    },
    "core_concepts": {"items": {"type": "string"}, "type": "array"},
    "logic_chain": {"type": "string"},
    "conclusions": {"items": {"type": "string"}, "type": "array"}
  },
  "required": ["part", "sections", "core_concepts", "logic_chain", "conclusions"],
  "type": "object"
}
```

## 经验值

- 每路子代理负责 15-18 个章节文件时耗时 90-130s；超过 18 个文件或内容 >8 万字时超时风险大（600s 上限），拆细或让其"重点读最长几节，其余快读"。
- 子代理若提示 "execute_code 需要批准不可用"——无碍，让其直接按 schema 输出 JSON 文本即可。
- 汇总结果里每路 summary 都会截断；完整 JSON 在 `~/.hermes/cache/delegation/subagent-summary-<N>-<时间戳>.txt`，用 read_file 或 python json.loads 获取。
