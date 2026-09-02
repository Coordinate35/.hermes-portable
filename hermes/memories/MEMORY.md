User operates within the 卢麒元 (Lu Qiyuan) investment analysis framework: real inflation = CPI + (M2 - GDP), real interest rate = nominal - real inflation. Four-matrix decision grid by growth/inflation quadrant. "Short stocks, long gold" strategy. CPI considered structurally understated. Core tool for macro allocation. See fact_store for full framework details.
§
工作目录：新建/读取→~/hermes_data/，绝不存~/根目录。
§
User is building a Global Multi-Economy Wealth Conservation Model. Combines SFC framework with physical Numéraire (Ω = fixed commodity basket). Axioms: (1) global net wealth = sum of physical capital only, financial claims net to zero, (2) replacement-cost valuation makes K immune to currency devaluation, (3) FX endogenous from PPP (B_i/B_j). Also built deviation-detection framework: 4 anchors (cost/yield/monetary/cross-country), RPI priority index (Regression Priority Index = arbitrage × cashflow × funding / institutional protection), linked to 卢麒元 four-matrix decision grid. Prefers rigorous math, layered architecture docs, systematic docs. Latest deliverable: architecture V0.2 at ~/hermes_data/global_economy_model_architecture.md. Open issues: production function, currency creation module, MVP scope.
§
架构分层原则：监控/数据采集脚本只做单一职责（如 weibo_monitor.py 只输出文字），不要在脚本里耦合下游处理逻辑（如 TTS 生成）。降级策略、消息格式化、推送渠道等应在 agent 层（cronjob prompt）处理，保持脚本的可复用性和降级灵活性。
§
语音/TTS 全部细节见 skill voice-message-delivery。QQ Bot 渠道：短句语音是默认输出方式，文字是例外（仅长文/复杂结构时用）。认知翻转：不是"要不要加语音"，而是"要不要加文字"。每条回复先判断是否 QQ Bot 短句，是则默认走语音，文字只做补充。
§
交付铁律：(1) 自报告前先读文件确认全貌，不可只描述新增。(2) 重复任务须封装成 skill，触发条件枚举完整自然口语变体。(3) SOUL.md 和所有 skill 触发条件一律平等，命中即执行，禁止自行排优先级或区分"必做/可做"。QQ Bot 短句默认走语音（见 voice-message-delivery skill），文字仅补充。
§
tts 工具集已禁用（hermes tools disable tts），text_to_speech 工具不可用。所有 TTS 走 terminal 三级降级链：win_tts.sh → MeloTTS → edge-tts CLI。voice-message-delivery skill 已同步更新。
§
记账分类：饮料→娱乐·餐饮娱乐，饭菜/买菜→刚性·食。文档阅读须逐字念原文不可概括。
§
用户偏好（2026-08 被纠正）：宏观分析/卢麒元框架计算必须展开过程，不能只给结果。格式：公式 → 代入数值 → 中间步骤 → 最终结果 → 判断。反例：直接输出"真实通胀率=4.3%"缺少推导。
§
用户=魏俊杰（GitHub Coordinate35，1995.03）：2018.07-2023.12 滴滴接入层资深研发D7（DevOps→管控面→转发引擎→接入层技术负责人）；2024.01-至今 抖音服务架构·研发体验与效率2-1。工作史源=~/Documents/summary，简历任务见 skill resume-cv-workflow。投资分析偏好系统提取+政策/基本面/技术面，聚焦能源板块。