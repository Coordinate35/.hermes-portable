# 百度地图网页版路线自动化配方（browser_exec）

百度 `map.baidu.com` 的**路线规划不需要登录**，路线结果在 `document.body.innerText` 里，可直接读。这是拿「国内口径」距离与耗时的唯一低成本入口。

## 前置：浏览器能联网
系统代理指向未运行的本地代理（Nekoray 127.0.0.1:2081）会导致全站 `ERR_PROXY_CONNECTION_FAILED`，高德/百度一起打得开才继续。处置见 skill `browser-exec-recovery`：`gsettings set org.gnome.system.proxy mode 'none'`，改完**直接重试 browser_exec**，harness 会自己拉起 Chrome。用完问用户要不要改回 `manual`。

## 关键约束：一次 browser_exec 调用跑完整流程
调用之间 tab 会被重置成 `about:blank`，下一次 `js()` / `fill_input` 直接 `element not found`。所以把「导航 → 开面板 → 填起终点 → 选联想项 → 选歧义项 → 读结果」全部写进同一个 code 块，中间只用 `time.sleep()`。

## 点击序列（实测可用）
1. `new_tab("https://map.baidu.com/")` → `wait_for_load()` → `time.sleep(6)`。
2. **打开路线类型面板**：`click_at_xy(369, 45)`，即搜索框右侧那个圆按钮。DOM 里 `innerText==='路线'` 的元素是 `.tooltip`（直接挂在 BODY 上），点它没有任何反应——必须用坐标点真实按钮。
3. 面板出现 `公交 / 驾车 / 步行 / 骑行 / 地铁图 / 公交线路查询`；按文本找 `span/div` 叶子节点、取 `getBoundingClientRect()` 中心坐标点击（不要用 `el.click()`）。
4. 面板出现 `.route-start-input`、`.route-end-input` 两个输入框。
5. `fill_input('.route-start-input', '大钟寺广场2号楼')` → `time.sleep(2)` → 联想项在 `.ui3-suggest-item`，用 js 找匹配项 `.click()`；要**确认选中**就回读 `input.value`。
6. 终点同理。**不要选带「-南门 / -北门」后缀的联想项**，除非已确认该门就是这次交通方式应该走的门（见 SKILL.md §3）。选小区整体 POI 即可。
7. 若弹出「请选择准确的起点、途经点或终点」，按文本找 `选为起点` / `选为终点` 并坐标点击；随后才会算路。
8. 读结果：`js("document.body.innerText")`。公交页会直接给出多条：`票价¥N 最快 地铁13号线` / `21分钟 | 3.9公里 | 步行880米`。
9. 展开细节：点该行的 `.route-head`（`innerText` 以 `票价¥N` 开头、`getBoundingClientRect().height` 在 40–120 px 之间，取最后一个匹配），可得「步行 210 米 → X站 上车 → 方向 → 几站 → 哪个出口 → 步行 670 米」。

## 枚举某地的门/出入口（百度 su 接口）
路线面板只会给「它收录过的」门（`展春园小区-南门` 这类联想项），问「这小区有哪些门」要走联想接口：
```
https://map.baidu.com/su?wd=<urlencode>&cid=131&type=0&newmap=1&ie=utf-8&oue=1&fromproduct=jsapi&res=api
```
返回 `{"s": ["北京市$海淀区$$展春园小区-西门$131$..."]}`，按 `$` 切开后**第 4 段（index 3）是名称**。多换几个前缀（`小区-`、`小区北`、`小区东`、`小区东南`、`小区门`）凑全集，去重后筛含「门」的项。脚本：`scripts/bd_poi_enum.py "展春园"`。

- 百度收录不全：某小区只有北门/西门/南门/南1门，没有东门。**「没收录」≠「没有门」**，结论里注明数据源与收录情况。
- 拿到门名后要逐个人算一遍，必须放在**同一个 browser_exec 调用**里循环（tab 会重置），每次改终点后重新处理一次「请选择准确的起点…」弹窗。
- 同一小区的门之间能差 9 分钟（实测 西门 21 / 北门 26 / 南门 27 / 南1门 30，地铁13号线口径），所以「门」是必须先枚举再锁定的变量，不能凭方位猜。

## 坑
- 直接 `el.value = '...'` 多半不触发框架事件（`js()` 返回 None）；用 `fill_input`。
- 别把 Python 布尔值拼进 JS 字符串，会报 `ReferenceError: True is not defined`；JS 侧写 `true`。
- 首次加载完成时 `document.querySelectorAll('canvas').length` 可能为 0、`innerText` 只有 177 字符，说明地图还没初始化；继续等，工具栏按钮此刻点不动。
- 图片侧栏（`.tooltip` 内容）和真实按钮是两套节点，按文本选元素容易选中 tooltip。
- `capture_screenshot()` 在这种 canvas 地图上常拍到空白底图，别拿截图判断页面是否正常，用 `innerText`。
- 要按经纬度调用时，坐标必须先转 BD-09（`scripts/wgs2bd.py`）；按地名 + 联想项调用最省事。

## 对照口径
同一段路（大钟寺广场2号楼 → 展春园小区南门）：

| 方式 | 百度 | OSM/OSRM |
|---|---|---|
| 步行 | 46 min / 3.1 km | 44 min / 3.31 km |
| 骑行 | 28 min / 4.8 km | 20 min / 3.77 km |
| 地铁13号线 | 21 min / 步行880 m / ¥3（到小区整体入口） | — |

骑行差得最多：百度只走主干道辅路，OSM 走小路。报数时两家并列。
