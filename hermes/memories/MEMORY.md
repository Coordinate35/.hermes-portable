User operates within the 卢麒元 (Lu Qiyuan) investment analysis framework: real inflation = CPI + (M2 - GDP), real interest rate = nominal - real inflation. Four-matrix decision grid by growth/inflation quadrant. "Short stocks, long gold" strategy. CPI considered structurally understated. Core tool for macro allocation. See fact_store for full framework details.
§
User has large collection of investment/finance documents at /home/coordinate35/virtualbox_share/luqiyuan/docs - prefers extracting and analyzing content systematically. Previously analyzed 100+ docx files to build investment framework.
§
用户有投资分析框架，关注政策对投资的影响，特别是能源板块
§
用户偏好系统化分析，需要政策+基本面+技术面的完整投资逻辑
§
工作目录约定：
1. 所有新内容 → /home/coordinate35/hermes_data/
2. 绝不保存在 /home/coordinate35/ 根目录
3. 读取数据 → 优先从 /home/coordinate35/hermes_data/ 读取
§
用户前瞻性分析能力: 主动询问GDP目标下调可能性(5%→4.5%/4%), 关注基数效应、房地产拖累、政策空间等深层次因素。需要基于官方目标(2025年5%)进行前瞻性情景推演。
§
User is building a Global Multi-Economy Wealth Conservation Model. Combines SFC framework with physical Numéraire (Ω = fixed commodity basket). Axioms: (1) global net wealth = sum of physical capital only, financial claims net to zero, (2) replacement-cost valuation makes K immune to currency devaluation, (3) FX endogenous from PPP (B_i/B_j). Also built deviation-detection framework: 4 anchors (cost/yield/monetary/cross-country), RPI priority index (Regression Priority Index = arbitrage × cashflow × funding / institutional protection), linked to 卢麒元 four-matrix decision grid. Prefers rigorous math, layered architecture docs, systematic docs. Latest deliverable: architecture V0.2 at ~/hermes_data/global_economy_model_architecture.md. Open issues: production function, currency creation module, MVP scope.
§
架构分层原则：监控/数据采集脚本只做单一职责（如 weibo_monitor.py 只输出文字），不要在脚本里耦合下游处理逻辑（如 TTS 生成）。降级策略、消息格式化、推送渠道等应在 agent 层（cronjob prompt）处理，保持脚本的可复用性和降级灵活性。
§
语音/TTS 全部细节见 skill voice-message-delivery（已在 description 标注「必加载」）。QQ Bot 渠道短句默认语音、长文先文字摘要再语音。
§
自报告准确性要求：用户会核验我口头汇报的工作内容（如"我加进 skill 的那段"）。回答"我做了什么/记了什么"时，必须先实际读取文件/状态确认全貌，不能只描述本次新增动作而忽略已有上下文。否则容易把"新增了一段"误述为"加进的全部内容"，与文件实际状态不符，被用户当场抓出。