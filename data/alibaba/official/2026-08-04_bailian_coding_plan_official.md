---
evidence_id: e_2026_08_04_alibaba_bailian_coding_plan
vendor_id: alibaba
captured_at: 2026-08-04
captured_by: claude
source_url: https://help.aliyun.com/zh/model-studio/coding-plan
capture_method: chrome-dump-dom + aliyun-help-md-export（同页两种独立方法交叉验证）
data_status: vendor_official
credibility: high
file_path: data/alibaba/official/2026-08-04_bailian_coding_plan_official.md
related_plans:
  - alibaba-bailian-coding-plan-pro
related_measurements: []
---

# 阿里云百炼 Coding Plan 官方套餐详情（Pro ¥200/月；6,000 / 45,000 / 90,000 次请求）

**厂商**：阿里云百炼（Alibaba Cloud Model Studio / Bailian）
**vendor_id**：`alibaba`
**官方文档更新时间**：2026-07-16 11:48:08（概述页）/ 2026-08-01 02:45:32（常见问题页）—— 均为页面自带的官方"更新时间"字段

## 抓到的官方 URL

| # | URL | 类型 | 抓取结果 |
|---|---|---|---|
| 1 | https://help.aliyun.com/zh/model-studio/coding-plan | 官方帮助文档 · Coding Plan 概述（**权威数据源**） | ✅ 成功（两种方法） |
| 2 | https://help.aliyun.com/zh/model-studio/coding-plan-faq | 官方帮助文档 · 常见问题（额度/限流/上下文） | ✅ 成功 |
| 3 | https://www.aliyun.com/benefit/scene/codingplan | 官方营销/抢购页 | ✅ 成功（无价格/额度数字） |
| 4 | https://common-buy.aliyun.com/coding-plan | 官方下单页 | ❌ 抓不到，302 跳登录页（需阿里云账号） |
| 5 | https://www.aliyun.com/notice/118094 | 官方公告 · Lite 停止新购 | ✅ 成功（仅日期，正文动态渲染） |
| 6 | https://www.aliyun.com/notice/118175 | 官方公告 · Lite 停止续费与升级 | ✅ 成功（仅日期，正文动态渲染） |
| 7 | https://bailian.console.aliyun.com/cn-beijing/?tab=plan#/efm/subscription/coding-plan | 控制台 Coding Plan 用量页 | ❌ 未抓，需登录 |

## 原文摘录（来自 URL 1，官方 .md 导出原文）

> Coding Plan 整合了千问、GLM、Kimi 、MiniMax顶级模型，并兼容主流AI编程工具。其折算成本远低于常规 API 调用，且通过固定月费模式有效防范了欠费风险。

> 1. Lite 套餐自 2026 年 3 月 20 日 00:00:00（UTC+08:00）起停止新购（详见公告）；4 月 13 日 18:00:00（UTC+08:00）起停止续费与升级（详见公告）。
> 2. Lite 套餐支持所有套餐模型（含千问、GLM、Kimi、MiniMax），与 Pro 套餐一致。

> **Pro 高级套餐**
> 价格：**¥ 200**/月
> 用量限制：
> - 每 5 小时 **6,000** 次请求
> - 每周 **45,000** 次请求
> - 每月 **90,000** 次请求

> **限时优惠**：活动已结束，当前价格以下单页为准。

> **限量抢购**：名额有限、先到先得。每日 09:30:00（UTC+08:00）补充，可前往 Coding Plan 页面抢购。

> **额度消耗**：单次提问将按实际"模型调用次数"扣除额度。简单任务约消耗 5-10 次，复杂任务约 10-30+ 次，实际消耗受任务难度、上下文及工具使用影响。

> **额度恢复**：
> 1. 每 5 小时额度：滚动恢复，每分钟自动释放 5 小时前的额度。 例：10:00 使用 100 次，11:00 使用 200 次。 → 15:00 先恢复 100 次，16:00 再恢复 200 次。
> 2. 每周额度：每周一 00:00:00（UTC+08:00）重置。
> 3. 每月额度：在下一个月订阅日的 00:00:00 (UTC+08:00) 重置。

> **支持的模型判断说明** — 判定规则：1. 本清单为精确字符串白名单 2. 必须逐字符完全匹配，版本号/子型号任何差异均视为不支持 3. 禁止做版本兼容推理
> 推荐模型：**qwen3.7-plus**（支持图片理解）、**qwen3.6-plus**（支持图片理解）、**kimi-k2.5**（支持图片理解）、**glm-5**、**MiniMax-M2.5**
> 更多模型：qwen3.5-plus（支持图片理解）、qwen3-max-2026-01-23、qwen3-coder-next、qwen3-coder-plus、glm-4.7

> **OpenAI 兼容协议**：`https://coding.dashscope.aliyuncs.com/v1`
> **Anthropic 兼容协议**：`https://coding.dashscope.aliyuncs.com/apps/anthropic`

> Coding Plan 服务**不支持退款**。
> **严禁 API 调用**：仅限在编程工具（如 Claude Code、OpenClaw 等）中使用，禁止以 API 调用的形式用于自动化脚本、自定义应用程序后端或任何非交互式批量调用场景。
> **数据使用授权**：使用 Coding Plan 期间，模型输入以及模型生成的内容将用于服务改进与模型优化。
> **账号使用规范**：套餐为订阅人专享使用，禁止共享。

### 来自 URL 2（常见问题页）

> **如何查看 Token 消耗信息？** 暂无法查看。Coding Plan 的额度消耗与 Token 消耗无关，只与模型调用次数有关。

> **可以查询 Coding Plan 套餐内特定模型（如 qwen3.6-plus）的使用量吗？** 不支持。Coding Plan 页面仅展示套餐总额度的整体消耗和剩余情况。

> **Coding Plan 有年付套餐吗？** 目前 Coding Plan 仅支持按月订阅，暂无年付套餐。

> **Coding Plan 额度用完后会转为按量计费吗？** Coding Plan 额度消耗完毕后，继续调用会失败报错，并且不会自动转为按量付费模式计费。

> **每个百炼账号支持同时开通几个 Coding Plan？** 每个百炼账号同时只能订阅一个 Coding Plan（不区分 Lite 和 Pro 套餐版本）。

> **Coding Plan 有并发限制吗？** Coding Plan 存在并发限制。平台会根据整体资源负载动态调整并发上限……触发并发限制时，等待片刻后重试即可。

> **Lite 和 Pro 套餐的模型响应速度相同吗？** Lite 基础套餐和 Pro 高级套餐在模型响应速度上是相同的，两个套餐使用的是同样的模型资源和推理服务。

> **首次续费为什么没有 5 折优惠？** 首次续费 5 折活动已于 2026 年 4 月 1 日 00:00:00（UTC+08:00）结束，当前续费价格以下单页为准。

> 错误码：`hour allocated quota exceeded`（每 5 小时请求额度已用完）/ `week allocated quota exceeded`（每周请求额度已用完）/ `month allocated quota exceeded`（每月请求额度已用完）/ `concurrency allocated quota exceeded`（并发超上限）

## 数据点

### 套餐与定价

| 字段 | 值 | 备注 |
|---|---|---|
| vendor_id | `alibaba` | 阿里云百炼 |
| plan_name | Coding Plan **Pro 高级套餐** | 当前唯一在售档位 |
| plan_tier | pro | — |
| currency | CNY | — |
| original_monthly | **200** | 官方"价格 ¥ 200/月" |
| original_quarterly | null | 官方未公布（仅支持按月订阅） |
| original_yearly | null | 官方明示"暂无年付套餐" |
| intro_monthly | null | 官方明示"限时优惠：活动已结束" |
| intro_renewal_discount | null | 首次续费 5 折已于 2026-04-01 结束 |
| status（Pro） | active | 需抢购，每日 09:30 (UTC+8) 补货 |
| status（Lite） | deprecated | 2026-03-20 停止新购；2026-04-13 停止续费与升级 |
| refundable | false | 官方"不支持退款" |
| auto_renew | 支持（到期前 9 天 08:00 UTC+8 起扣款，仅可扣账户可用额度） | 来自 FAQ |

### 用量限额（Pro）

| 窗口 | requests_official | tokens_official_claimed | 重置规则 |
|---|---|---|---|
| window_5h | **6,000** 次请求 | null | 滚动恢复，每分钟释放 5 小时前额度 |
| window_weekly | **45,000** 次请求 | null | 每周一 00:00:00（UTC+8）重置 |
| window_monthly | **90,000** 次请求 | null | 下一个月订阅日 00:00:00（UTC+8）重置 |

**计量单位为"模型调用次数"，不是 token**（官方明示额度消耗与 Token 消耗无关）。因此 `tokens_official_claimed` / `tokens_measured` 全部为 `null`（铁律 16 / 铁律 20：单位错位必须明示，不得把"次"强转成 tokens）。

### 支持的模型（官方精确白名单，逐字符匹配）

| model_id | 分类 | 图片理解 | 上下文长度（Tokens） | 最大思维链长度 |
|---|---|---|---|---|
| qwen3.7-plus | 推荐 | ✅ | 1,000,000 | 262,144 |
| qwen3.6-plus | 推荐 | ✅ | 1,000,000 | 81,920 |
| kimi-k2.5 | 推荐 | ✅ | 262,144 | 81,920 |
| glm-5 | 推荐 | — | 202,752 | 32,768 |
| MiniMax-M2.5 | 推荐 | — | 196,608 | 默认启用，无需配置 budgetTokens |
| qwen3.5-plus | 更多 | ✅ | 1,000,000 | 81,920 |
| qwen3-max-2026-01-23 | 更多 | — | 262,144 | 81,920 |
| qwen3-coder-next | 更多 | — | 262,144 | 不支持思考模式 |
| qwen3-coder-plus | 更多 | — | 1,000,000 | 不支持思考模式 |
| glm-4.7 | 更多 | — | 202,752 | 32,768 |

上下文长度与思维链长度来自 URL 2（常见问题页）。**primary_model 建议取 `qwen3.7-plus`**（官方推荐列首位、上下文最长）。

### 支持的客户端

OpenClaw、Hermes Agent、Claude Code（含 IDE 插件）、OpenCode、Cursor、Codex、Qwen Code、QwenPaw、Cherry Studio、Chatbox、Cline、Qoder、Qoder CN（原 Lingma）、Kilo CLI / Kilo Code IDE 插件、Postman、Dify（官方**不建议**）、Windsurf 等。

### 使用限制（风险项，必须显性标注）

- **严禁 API 调用**：仅限交互式编程工具，禁止自动化脚本 / 应用后端 / 非交互式批量调用，违规可能封禁 API Key。
- **禁止共享**：仅限订阅人个人使用，检测到 Key 公开泄露会自动禁用；Pro 不支持企业多人共用。
- **不支持退款**、**不支持降配**（Pro → Lite）。
- **数据使用授权**：模型输入与生成内容将用于服务改进与模型优化。
- **专属凭证**：API Key `sk-sp-xxxxx`，Base URL 必须含 `coding.dashscope.aliyuncs.com`；误用通用 Key/URL 会走按量计费产生额外扣费。
- **动态并发上限**：平台按整体负载动态调整，高峰期可能触发 `concurrency allocated quota exceeded`。
- **限量抢购**：可能显示售罄，每日 09:30（UTC+8）补货。
- 每个百炼账号同时只能订阅 1 个 Coding Plan。
- 服务周期按自然月：开通时刻起至次月对应日 23:59:59（UTC+8），2 月开通可能只有 28 天。

## 二次验证

- [x] **方法 A**：`chrome --headless=new --dump-dom` 抓 URL 1 → HTML 1,196,822 字节 → 正文文本 8,636 字符
- [x] **方法 B**：阿里云帮助中心官方 Markdown 导出端点 `https://help.aliyun.com/zh/model-studio/coding-plan.md` → 8,637 字节原文（对应页面上的"复制 MD 格式"按钮）
- [x] **关键数字逐项对账（方法 A vs 方法 B）**：

| 数据点 | 方法 A（dump-dom） | 方法 B（.md 导出） | 差异 |
|---|---|---|---|
| Pro 月价 | ¥200/月 | ¥200/月 | 0% ✅ |
| 每 5 小时 | 6,000 次请求 | 6,000 次请求 | 0% ✅ |
| 每周 | 45,000 次请求 | 45,000 次请求 | 0% ✅ |
| 每月 | 90,000 次请求 | 90,000 次请求 | 0% ✅ |
| 模型白名单 | 10 个 model_id 一致 | 10 个 model_id 一致 | 0% ✅ |
| Lite 停售日期 | 2026-03-20 / 2026-04-13 | 2026-03-20 / 2026-04-13 | 0% ✅ |

- [x] **方法 C（截图）**：`chrome --headless=new --screenshot`（2x device scale）拍到套餐详情表格，`¥ 200/月` + `6,000 / 45,000 / 90,000` 肉眼可读 → `2026-08-04_bailian_coding_plan_pricing_table_screenshot.png`
- [x] **Lite 停售日期第三方核验**：官方公告页 `aliyun.com/notice/118094`（影响时间 北京时间 2026-03-20 00:00:00 停止新购）与 `aliyun.com/notice/118175`（影响时间 北京时间 2026-04-13 18:00:00）与帮助文档一致

**结论：二次验证通过，三种方法关键数字 0 差异。**

## 自洽性验算（铁律 22）

官方只公布"请求次数"三窗口额度，**未公布** per-model 单次请求 token 组成，也未公布 Coding Plan 内部单价，**因此无法做"每请求成本 × 请求数 = 窗口额度"的反推验证**。可做的是窗口之间的比例自洽性检查：

| 检查 | 计算 | 结论 |
|---|---|---|
| 5h → 周 | 一周 = 168h = 33.6 个 5h 窗口；6,000 × 33.6 = 201,600 vs 官方 45,000 | 周额度是硬上限，**周先耗尽**（周额度 ≈ 7.5 个满 5h 窗口） |
| 周 → 月 | 45,000 × 4.286 周/月 = 192,857 vs 官方 90,000 | 月额度 = 周额度 × **2.0**（整数倍，非 4-5 倍） |
| 铁律 6（月 ≤ 周 × 5） | 90,000 / 45,000 = 2.0 | ✅ 通过（与火山方舟"月 = 2 × 周"同型，属官方硬封顶） |

**真实瓶颈判定（基于官方数字，非主观评估）**：月额度 90,000 次 = 2 个满周额度，即用户在一个订阅月内最多只能"跑满 2 周"。5h 窗口 6,000 次几乎不可能先撞到（需要在 5h 内发 6,000 次调用）。

**以下为推导值，非官方公布，仅供后续 yml 决策参考，不得写进 `*_official` 字段**：

| 推导项 | 计算 | 值 |
|---|---|---|
| 每次模型调用均价 | ¥200 ÷ 90,000 次 | ≈ ¥0.00222/次 |
| 月可完成"简单任务"数 | 90,000 ÷ 10 次（官方"简单任务约 5-10 次"取上限） | ≈ 9,000 个 |
| 月可完成"复杂任务"数 | 90,000 ÷ 30 次（官方"复杂任务约 10-30+ 次"取下限口径） | ≈ 3,000 个 |

## 不确定 / 存疑

1. **Lite 套餐的价格与三窗口额度：官方已下架，当前官方页面查不到。** 网络上流传的「Lite ¥40/月、1,200 次/5h、9,000 次/周、18,000 次/月」全部来自 CSDN / 博客园等二手推算，**未在任何 aliyun.com 官方页面找到**，按铁律 16 一律记 `null`，不得填入 `*_official` 字段。若要收录 Lite 档，必须另找官方存档页。
2. **下单页实付价抓不到**：`https://common-buy.aliyun.com/coding-plan` 302 跳转到阿里云登录页（截图见 `.scratch/buy_page.png`，非仓库文件），无法核验"当前价格以下单页为准"到底是不是 ¥200。**官方文档标价 ¥200/月是目前唯一可引用的官方价格**。
3. **首月 ¥7.9 / ¥39.9、次月 5 折**：官方文档明确写「限时优惠：活动已结束」「首次续费 5 折活动已于 2026-04-01 结束」，因此 `intro_*` 字段一律 `null`。二手博客上的 7.9/39.9 属过期活动，不得写入。
4. **token 口径完全缺失**：官方明示"额度消耗与 Token 消耗无关，只与模型调用次数有关"且"暂无法查看 Token 消耗"，所以 `tokens_official_claimed` / `tokens_measured` 只能是 `null`（铁律 20 claimed-only 状态需在 plan.yml 用 `data_status_declaration` measurement 明示）。
5. **营销页模型列表与帮助文档不一致**：`aliyun.com/benefit/scene/codingplan` 仍写 Qwen3.5-Plus / Qwen3-Max / MiniMax M2.5 / GLM-5 / Kimi-k2.5 / GLM-4.7，**没有 qwen3.7-plus / qwen3.6-plus**；帮助文档（2026-07-16 更新）已含 qwen3.7-plus / qwen3.6-plus。**以帮助文档为准**（官方 FAQ 亦声明"当前支持的模型以 Coding Plan 概述页面展示为准"）。
6. **并发上限无具体数字**：官方只说"平台动态调整"，无 RPM/RPS 公布值。
7. **邀请码 / affiliate**：本次未在任何官方页面发现 Coding Plan 专属邀请码或推荐返现，`affiliate: null`（未验证是否存在"云大使推荐返现计划"覆盖本产品）。
8. **`scope` 字段（铁律 21）**：官方"简单任务 5-10 次 / 复杂任务 10-30+ 次"是阿里云自己对全部编程工具场景的笼统描述，非某一客户端观测值，故 `scope: null`；但该区间随工具（Claude Code vs Cursor）差异很大，写入 measurement 时建议在 notes 中注明。

## 关联引用

- 原始抓取文件（同目录）：
  - `2026-08-04_bailian_coding_plan_overview_raw.md`（URL 1 官方 .md 导出全文，8,637 字节）
  - `2026-08-04_bailian_coding_plan_faq_raw.md`（URL 2 官方 .md 导出全文，40,788 字节）
  - `2026-08-04_bailian_codingplan_scene_page_raw.md`（URL 3 chrome dump-dom 正文）
  - `2026-08-04_bailian_coding_plan_overview_screenshot.png`（URL 1 全页截图，2800×5200）
  - `2026-08-04_bailian_coding_plan_pricing_table_screenshot.png`（套餐详情表格特写，价格+三窗口额度可读）
  - `2026-08-04_bailian_codingplan_scene_page_screenshot.png`（URL 3 全页截图，2800×4400）
- vendor（待建）：`data/vendors/alibaba.yml`
- plan（待建）：`data/plans/alibaba-bailian-coding-plan-pro.yml`
