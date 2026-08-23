---
name: china-policy-document-search
description: 中国政策文件检索。Use when 用户询问中国税收/财政/金融政策变动或需要官方文件。
---

# 中国政策文件检索 (China Policy Document Search)

## 触发条件
- 用户询问中国政策变动："税收/财政/关税/金融政策有哪些改动" "有没有官方文件/通知/公告"
- 财经政策类问题需要引用权威官方源回答
- 按用户偏好：经济金融财政学问题先搜 fact_store（holographic memory），再按本 skill 检索官方源

## 首选：中国政府网站内搜索（browser_navigate 访问）
端点：
```
https://sousuo.www.gov.cn/sousuo/search.shtml?code=17da70961a7&searchWord={关键词}
```
- 结果直接渲染在无障碍树 snapshot 里（标题+摘要+发布时间），无需解析 JS，无需 curl
- 覆盖国务院/部委政策文件、新华社通稿、国务院公报，权威性最高；文号、发布日期一应俱全
- 搜索词要短（2-6 字）：`离境退税` ✓；`减税降费 2026` → 0 结果 ✗，拆成 `减税` 再筛年份
- 全文类文件（如政府工作报告）在 gov.cn/gongbao/ 国务院公报栏目；用 browser_console 提取 `document.body.innerText` 后按关键词切上下文段（如搜"税""赤字"定位段落）

## 备用：JSON API 在浏览器里提取
- 终端 curl 可用时直接用；终端被限制时：browser_navigate 到 API URL，然后 browser_console 执行 `JSON.parse(document.body.innerText)` 提取结构化数据
- 华尔街见闻 API 适用财经新闻/市场事件，**政策文件类覆盖极弱**（搜"税收政策"仅 0-2 条不相关结果）

## 陷阱（2026-08 实测）
1. cn.bing.com 对中文政策查询返回与查询无关的缓存结果集（日历、世界杯等），换关键词结果不变 → 政策检索不要依赖搜索引擎
2. baidu.com headless 请求触发 CAPTCHA（302 → 安全验证页）
3. 官方站静态首页是旧缓存/JS 动态加载：chinatax.gov.cn、mof.gov.cn、gov.cn/zhengce 索引页 curl 到的是多年前旧内容；fgk.chinatax.gov.cn 法规库有 WAF 拦截
4. 澎湃新闻 searchResult 接口对部分政策词返回 0 结果
5. 结论：**政策类检索直接走 gov.cn 站内搜索**，搜索引擎和新闻站只作补充

## 流程
1. fact_store 搜关键词（用户偏好：经济金融问题先搜，2026-08 确认无相关事实时继续外部检索）
2. gov.cn 站内搜索（browser_navigate）
3. 点开官方文件，browser_console 提取正文关键段落
4. 回答必须注明：文件名称、文号、发布日期、出处站点；不确定的细节（如具体税率品目）如实说明，不编造

## 参考文件
- references/2026-h1-tax-policy.md — 2026 上半年税收政策变动已核实清单（含文号/日期/来源），下次用户追问可直接引用
