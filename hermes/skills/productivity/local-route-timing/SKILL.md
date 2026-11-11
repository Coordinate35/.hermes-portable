---
name: local-route-timing
version: 1.0.0
author: Hermes Agent
license: MIT
description: Use when 查两地步行/骑行/公交耗时或选小区门。用百度地图网页版自动算路，分段相加，不编换乘时间。
metadata:
  hermes:
    tags: [maps, baidu, route, walking, transit]
    related_skills: [browser-exec-recovery]
---

# 本地出行耗时测算（百度口径）

## When to Use
「A 到 B 多久」「步行/骑车/坐地铁要多久」「哪个门最近」「换乘方案」类问题；以及需要逐段对比不同接驳方式的场景。

## 硬规则（用户明确要求）
1. **只用百度地图**，不用 OSM/OSRM 做主口径（用户拒绝过）。OSM 只在百度完全不可用时兜底，并注明。
2. **不自加换乘固定成本**：安检、等车、走站厅、找车还车，一概不加。只加运动段（百度给的距离与时间）。
3. **终点门按出行方式选**：全程步行/骑行 → 离起点最近的门；坐地铁/公交 → **离车站最近的门**（曾因选「离起点最近的南门」多算 6 分钟）。
4. 终点精确到楼（如「大钟寺广场-2号楼」），不要用「大钟寺」这种地名，**也不要用楼栋的某个门**（「2号楼-东门」）：实测同一路线 21 分 vs 20 分，1 分钟足以翻转达标判定。
5. POI 的地址字段可能是脏数据（例：南门标「北洼路77号」），以路线经过的街道为准。

## 浏览器前置
系统代理若指向 `127.0.0.1:2081`（Nekoray 未运行）浏览器全站打不开：
`gsettings set org.gnome.system.proxy mode 'none'`（用完问用户是否恢复 manual）。
Chrome 由 harness 自管，不要手工起。**tab 常在两次调用间被重置成 about:blank → 整个流程必须写在一次 browser_exec 里。**

## 百度地图自动化流程（实测可用）
```python
new_tab("https://map.baidu.com/"); wait_for_load(); time.sleep(6)
click_at_xy(368, 39)            # .route-button(39×38) → 展开 公交/驾车/步行/骑行；它是 toggle，面板开着再点会关掉
click_text('步行')              # 或 公交 / 骑行，tab 在 y≈38
fill_input('.route-start-input', '五道口站')
pick_first()                      # .ui3-suggest-item 直接点第 1 项；按名称 includes 匹配会被连字符/后缀搞失败
fill_input('.route-end-input', '展春园小区-西门')
pick('西门')
# 出现「请选择准确的起点/终点」时，点「选为起点」「选为终点」各一次（a/span/div 文本精确匹配，取第一个）
# 结果读 document.body.innerText，正则 r'(\d+)\s*分钟[约]?\s*([\d.]+)\s*公里'
```
结果首行形如 `21分钟 | 3.9公里 | 步行880米`（公交）或 `7分钟约1.1公里`（步行/骑行）。
公交面板的逐段明细要点**已选中**的 `ul.route li.on` 才展开：步行 X 米 → 站上车 → N 站 → 出口 → 步行 Y 米（列表行本身只有票价/时间/距离，不含站名）。

### 选中联想项必须真实点击，不要用 DOM click
`document.querySelectorAll('.ui3-suggest-item')[0].click()` 看着成功，实际会把「名称 + 区名」整串写进输入框（如「科育小区-东南门 北京市海淀区」）。百度随即判为歧义，界面停在「请选择准确的起点、途经点或终点」，此后 `分钟/公里` 正则恒为空数组——看起来像查询失败，其实根本没选中。

正确做法：取联想项 `getBoundingClientRect()` 的中心坐标，用 `click_at_xy` 点：
```js
(() => {const it=[...document.querySelectorAll('.ui3-suggest-item')];
 const h=it.find(e=>e.innerText.includes('北京市')&&e.innerText.includes(名称));
 if(!h)return null; const r=h.getBoundingClientRect();
 return [Math.round(r.x+r.width/2), Math.round(r.y+r.height/2)];})()
```
点完 `input.value` 应只剩干净名字；若仍带区名、或结果为空，先重设输入，别接着往下算。地图 POI 卡片上的「选为起点/选为终点」同样用坐标点掉。

**城市过滤**：`cid=131` 不保证结果都在北京——「科育小区-西门」的首条联想是「许昌市长葛市」。按 `includes('北京市')` 优先筛，否则整轮结论作废。

### 面板状态与端点复核（踩过的坑）
- 面板开关是 toggle，先判状态：`document.querySelector('.route-start-input').getBoundingClientRect().width > 0`。面板关着时所有输入都写进隐藏 DOM，联想列表恒为空。
- 百度会把端点回退成上一次的 POI：切 tab / 改出发时间 / 改另一端之后，先重读 `input.value` 再记数，否则会把上一个点的结果记到当前点名下的。
- `querySelectorAll('*')` 找文本节点要过滤 `e.innerText &&`：隐藏节点 innerText 为 undefined，整段 JS 直接抛 TypeError。

### 公交必须按工作日 08:00 重算
凌晨查「公交」只出夜班车（夜30路），27–28 分钟这种结果没有参考价值。面板 `th` 里 `#bs_start_time` 旁 `.droplist` → `li.hour[data-h="8"]` → `li.minute` 文本 `08:00`。
**改起点/终点会把出发时间重置为「现在」**，每换一个点都要重设。
百度显示的总分钟**含候车**：若口径是不计等车，点选中项 `ul.route li.on` 展开拿车程，再单独查两端接驳，`总时 = 接驳 + 车程 + 接驳`；两个数都给用户。
接驳段用独立「步行/骑行」查询的米数，不用方案自带的（实测方案 160 m、独立步行 270 m，差在过街天桥）。

## 枚举小区门（百度联想接口，无需浏览器）
`https://map.baidu.com/su?wd=<urlencode(前缀)>&cid=131&type=0&newmap=1&ie=utf-8&oue=1&fromproduct=jsapi&res=api`
返回 JSON `s` 数组，元素第 4 段是 POI 名。多试前缀：`展春园`、`展春园小区-`、`展春园小区北/南/东/西`。
口语名常不是 POI 名（「农影小区」在百度是「农影社区」）：按名字前缀过滤出 0 个门时，先看联想返回的真实 POI 名再换名重查，别急着下「没有门」的结论。
实测展春园小区有：北门、西门、南门、南1门（无东门）。

## 算法
- **端到端**：每种方式各查一条整段，直接采用。
- **分段相加**：逐段查（含地铁两端接驳），只加运动时间；与端到端结果互校，差异应可解释。
- **阈值经验**：接驳 <500 m 走路（骑行绕行更慢）；500–1200 m 骑行通常只省 1–2 分钟；>1200 m 或全程骑行才明显划算。

## 输出
表格（方式/距离/时间/步行接驳/票价）+ 关键路口或换乘站 + 查询时间与是否高峰 + 数据来源「百度地图」。

百度时间按整分钟显示：结果卡在阈值 ±1 分时要注明边际（显示 20 分实际可能 20.5），并提醒实地复核。
