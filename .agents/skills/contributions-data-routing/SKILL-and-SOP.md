---
name: contributions-data-routing
description: 引导贡献者提交 PR 时把数据放到正确目录，避免维护者返工。触发条件：用户/贡献者表示"想贡献数据""报数据""新厂商""新套餐""能不能加 XX 厂商""我这个 XX 实测了多少"——任何外部贡献入口场景都必须先读本文件，按决策树告诉对方正确的目录路径 + PR 标题 + 必填字段。本文件既是 skill（agent 决策用），又是 SOP（标准路由流程），与 ledger-data-discipline 同款双重属性。
---

# 贡献数据路由（避免 PR 后返工）

> **强制触发**：任何对**外部贡献者**（含用户自己以外的人）的"提交数据 / 报数据 / 加厂商 / 加套餐"指导之前，必须读完本文件并按决策树给出路径。**不准凭印象指导路径**，否则 PR 后维护者要返工。
>
> 本文件跟 `ledger-data-discipline/SKILL-and-SOP.md` 是姐妹文件——那个管"维护者改 yml 时怎么做"，这个管"贡献者提交时去哪"。两者必须配套。
>
> **配套人类入口文档**（贡献者先看的）：`CONTRIBUTING.md`（根） / `docs/contributing.md`（站点） / `.github/PULL_REQUEST_TEMPLATE.md`（按贡献类型勾选）。本文件是 agent 内部用的决策树，不是给贡献者直接看的。

---

## 0. 心智模型（先理解再指导）

### 三层数据，三层信任

```
┌────────────────────────────────────────────────────┐
│ evidence（材料层）  data/<vendor>/official|scraped │
│   ↑ 任何贡献者都能交                                 │
│     官方一手 → official/                            │
│     社区/第三方 → scraped/                          │
├────────────────────────────────────────────────────┤
│ schema（结构层）  data/vendors/*.yml + data/plans/  │
│   ↑ 维护者按 evidence 写，含 data_status 字段       │
├────────────────────────────────────────────────────┤
│ build（产品层）   docs/.vitepress/plans.json        │
│   ↑ GitHub Actions 自动产物，不允许手改             │
└────────────────────────────────────────────────────┘
```

**贡献者大多数情况只需要交 evidence（第一层）**。schema 那层是维护者的事，避免贡献者被迫理解全部 YAML schema。**但要告诉他们"你交什么 → 落到哪个目录"，否则他们不知道该 push 到仓库哪里**。

### 三种贡献类型对应的目录

| 贡献类型 | 第一目标目录 | 是否需要 schema 文件 | PR 标题前缀 | 预估占比 |
|---|---|---|---|---|
| **个人实测**（"我买了 X 套餐，用了多少"） | `data/<vendor_id>/scraped/` | ❌ 不需要 | `[self-report]` | **~70%**（最常见） |
| **官方一手材料**（厂商官网 / 文档 / 公告） | `data/<vendor_id>/official/` | ❌ 不需要 | `[evidence]` | ~15% |
| **社区观察 / 第三方博客 / 浏览器记录** | `data/<vendor_id>/scraped/` | ❌ 不需要 | `[scraped]` | ~5% |
| **新厂商 / 新套餐** | `data/vendors/<id>.yml` + `data/plans/<id>.yml` + `data/<id>/official/` | ✅ 需要 schema | `[new vendor]` / `[new plan]` | ~5% |
| **探针月报（脱敏）** | `data/reports/<vendor_id>/<plan_id>/<user-hash>-<date>.md` | ❌ 不需要 | `[report]` | ~5% |

**为什么个人实测排第一**：现实约束决定贡献流量——7 天探针门槛高，一次性账单/截图门槛低。大多数贡献者不愿意装探针跑一周，但他们愿意分享一次实测。设计必须迁就现实，不是反过来。

### vendor_id 是什么 / 在哪里查

- **定义**：厂商在 `data/vendors/<vendor_id>.yml` 里的文件名，全小写、无空格
- **查法**：[`data/vendors/`](https://github.com/OLmatter/llm-api-ledger/tree/main/data/vendors) 目录
- **现成 ID**：`zhipu` `zai` `openai` `volcengine` `kimi` `minimax` `anthropic` `opencode` `chatgpt`
- **没有**：按"新厂商"路径走，PR 里**同时**建 vendor.yml + 至少一条 official/ 证据

---

## 1. 决策树（agent 拿到用户贡献请求后按这个走）

**起点**：用户说"想贡献 X / 报数据 / 加 Y / 我这个 Z 实测了多少"。

```
1. 用户手上是什么类型的数据？
   ├─ 用户自己的实测数据（"我买了 X 套餐，用了多少"）
   │   → ⚠ 这是最常见路径（估计 ~70%），优先匹配
   │   → 引导路径 = data/<vendor_id>/scraped/
   │   → 文件名 = YYYY-MM-DD_<套餐名>_my_usage.md|.png
   │   → **不需要 frontmatter**——把截图扔进来 + PR 描述写清数字就行
   │   → 维护者会按 §3.5 流程补 measurements（credibility: low, disputed: true）
   │
   ├─ 官方一手材料（厂商定价页 / monitor API / 文档截图）
   │   → 引导路径 = data/<vendor_id>/official/
   │   → 命名规则 = YYYY-MM-DD_<短描述>.md|.png
   │   → frontmatter 必填字段见 §3
   │   → 立刻跳过 2-4，直接给 §3 + §4 模板
   │
   ├─ 社区观察 / 第三方博客 / 浏览器实测
   │   → 引导路径 = data/<vendor_id>/scraped/
   │   → 其他同 official/
   │   → credibility 默认给 medium 或 low（不是 high）
   │
   ├─ 新厂商 / 新套餐（schema 也要建）
   │   → 见 §2. 新厂商/套餐 checklist
   │   → 一次性 PR 同时含 vendor.yml + plan.yml + official/ 第一条证据
   │
   ├─ 探针月报（已跑 ≥ 7 天的脱敏数据）
   │   → 引导路径 = data/reports/<vendor_id>/<plan_id>/<user-hash>-<date>.md
   │   → 必须含脱敏检查（§3 末 4 条 checklist）
   │
   └─ 代码 / 文档改动
       → 不属于本 skill 范围，按常规代码 PR 流程
```

---

## 2. 新厂商 / 新套餐 checklist（最容易返工的部分）

**新厂商** 一次性 PR 必含 3 件套，缺一不可：

- [ ] `data/vendors/<vendor_id>.yml` — 厂商元数据
- [ ] `data/plans/<plan_id>.yml` — 至少 1 个套餐（首版一个就够）
- [ ] `data/<vendor_id>/official/<YYYY-MM-DD>_<短描述>.md` — 第一条官方证据（用于校验 vendor_id 拼写、定价口径、限流单位）

**新套餐**（厂商已存在）只需要 2 件：

- [ ] `data/plans/<plan_id>.yml`
- [ ] `data/<vendor_id>/official/` 或 `scraped/` 一条对应证据

**新厂商的关键陷阱（避免返工）**：

1. **vendor_id 拼写**：`data/vendors/<id>.yml` 必须跟 PR 里所有 `vendor:` 字段、`<vendor_id>` 引用**完全一致**（全小写、无空格、无连字符也尽量别用）。
2. **brand_color**：必须是合法 hex（`#0071e3` 形式），不能是 CSS 颜色名。
3. **affiliate 字段**：无邀请码就 `affiliate: null`，**不要省略字段**（铁律 7）。
4. **claimed 字段口径**：先看厂商公布的单位（次 / tokens / Credits / \$），不要默认填 requests_official（详见 `ledger-data-discipline/SKILL-and-SOP.md` 铁律 4）。
5. **tokens_measured vs tokens_official_claimed**：实测字段留空 ≠ 0；`tokens_measured: null` 表示"还没测"，前端展示 `—`（铁律 9 / 16）。
6. **首选模型**：放 `shared_features.primary_model`，便于榜单对比基准。
7. **TIER_RATIOS / VENDOR_RATIOS 新增**：如果新厂商多档位且不是 1:5 简单倍数，要同步改 `scripts/build-plans.mjs` 的 `TIER_RATIOS[vendor]` / `VENDOR_RATIOS[vendor]`，否则 lint 报错。

**PR 提交前自动跑**：

```bash
node scripts/build-plans.mjs   # 必须通过
node scripts/lint-plans.mjs    # 必须 0 error
npx vitepress build docs       # 必须通过
node scripts/data-diff.mjs     # 无意外字段变化
```

---

## 3. evidence 文件 frontmatter 必填字段（贡献者最容易漏）

```yaml
---
evidence_id: e_2026_07_31_zhipu_overview   # 全局唯一，建议 YYYY_MM_DD_<short>
vendor_id: zhipu                            # 必须跟 data/vendors/<id>.yml 一致
captured_at: 2026-07-31                     # YYYY-MM-DD
captured_by: claude                         # 谁抓的：claude / user / 第三方工具名
source_url: https://docs.bigmodel.cn/...    # 原始 URL（必填）
capture_method: chrome-dump-dom             # chrome-dump-dom / chrome-cdp-runtime-evaluate / 人工截图 / ...
data_status: vendor_official                # vendor_official / anthropic_official / community_report / scraped
credibility: high                           # high / medium / low
file_path: data/zhipu/official/2026-07-31_...md  # 自身路径（自引用）
related_plans:                              # 关联套餐 ID 列表，可以是未来 PR 计划加的
  - zhipu-glm-coding-pro-v3
---
```

**必填字段缺一不可**，lint 检查（铁律 28 已落地）：

- 缺 `evidence_id` → lint 报错
- 缺 `source_url` → lint 报错
- 缺 `vendor_id` → lint 报错
- 缺 `data_status` → lint 报错

**frontmatter 之外，正文建议结构**（不强制但维护者读起来快）：

```markdown
# <一句话标题>

## 原文摘录

> 关键句子（用 blockquote 标注原文）

## 数据点

| 字段 | 值 | 备注 |
|---|---|---|
| pricing_first_month_usd | 5 | 首月特价 |

## 二次验证

- [ ] 已 Chrome dump 验证 / 已 WebFetch 验证
- [ ] 关键数字 ≥ 2 个独立来源对账

## 不确定 / 存疑

（如有写明；如无写"无"）

## 关联引用

- vendor: data/vendors/<id>.yml
- plan: data/plans/<plan_id>.yml
```

---

## 4. 命名规则（一眼看懂）

| 类型 | 规则 | 例子 |
|---|---|---|
| 日期 | `YYYY-MM-DD`（必填，按捕获时间） | `2026-07-31` |
| 描述 | 简短中文/英文，描述这次抓的是什么 | `opencode_go_official`, `kimi_allegretto_burn_test` |
| 后缀 | `.md` 文字，`.png` 图片，多图加 `_1/_2/_3` | `_1.png`, `_2.png` |

**避免**：空格、中文标点、特殊字符（用 `_` 分隔）

**截图工作流**（适合不会写 frontmatter 的贡献者）：

1. 把截图直接拖进 `data/<vendor_id>/scraped/`
2. 命名：`YYYY-MM-DD_<短描述>.png`（截全屏、字能看清、命名说清厂商 + 数据内容）
3. 提 PR 时在描述里写：**"我截图了 XX 厂商 YY 页面的 ZZ 数据，文件在 scraped/ 目录，请维护者按 evidence 规范补 frontmatter 并创建对应 plan.yml"**
4. 维护者收到 PR 后会按 §3 补 frontmatter + 建 plan.yml / vendor.yml

这是**最低门槛贡献路径**，连 frontmatter 都不用贡献者写。

---

## 4.5 个人实测专用流程（[self-report]）

**预估占比 ~70%**——大多数贡献者只有"我买了 X 套餐，用了多少"的实测。

### 贡献者侧（5 步）

1. **Fork 仓库**。
2. **截图**（3 选 1，按清晰度从低到高）：
   - 厂商 monitor API 页面（最推荐，能看到 5h/weekly/MCP 三周期额度百分比）
   - 账单 / 邮件截图（次之，能看到本期用量和扣费）
   - IDE 用量统计截图 / 探针 dashboard 截图（兜底，看到的是单次请求统计）
3. **打码**：完整 token / API key / 个人邮箱 / 账号 ID 涂黑。
4. **扔进** `data/<vendor_id>/scraped/`，命名 `YYYY-MM-DD_<套餐名>_my_usage.png`（多图加 `_1/_2/_3`）。
5. **提 PR**：标题 `[self-report] 我买了 <vendor_id>-<plan_id> <一句话>`，描述里写 3 件事：套餐名、跑了多久、截图里展示的关键数字。

### 维护者侧（4 步，**必读**）

收到 [self-report] PR 后：

1. **核对脱敏**：完整 token / API key / 邮箱 / 账号 ID 都打码了吗？没打码就退回。
2. **提取数字**：从截图读出关键字段，**不靠用户手写**——截图说什么就是什么。
3. **写到 measurements**：
   ```yaml
   # data/plans/<plan_id>.yml 的 measurements 数组加：
   - measurement_id: m_<YYYY_MM>_<vendor>_<plan>_self_report_<n>
     source_kind: community_report
     source_url: https://github.com/<org>/llm-api-ledger/pull/<PR号>
     evidence_path: data/<vendor_id>/scraped/<文件名>.png
     captured_at: <YYYY-MM-DD>
     credibility: low            # 单点必 low
     disputed: true              # 单点必 disputed（铁律 10）
     # 数据字段直接放
     monthly_used_tokens: 804430000
     monthly_used_pct: 90
     # ...
     notes: |
       截图来自 <vendor_id>-<plan_id> 用户实测。
       单点数据，已标 disputed，等第二个用户数据来再升级 median。
   ```
4. **建 plan.yml / vendor.yml（如果没有）**：套餐第一次出现需要先建 YAML schema。详见 §2。

### 关键纪律（与 ledger-data-discipline 联动）

- **单点 credibility: low**（铁律 10）——别因为"看起来合理"就给 high
- **单点 disputed: true**（铁律 10）——等 ≥ 2 个独立 user_hash 数据才升级 median
- **跨周期数据缺失**（用户只跑了 3 天没满一周）→ 不准在 measurement 里写 weekly 字段，只填他实际跑到的周期
- **截图里数字与 PR 描述不一致** → 以截图为准，PR 描述里的数字是"用户估算"，仅供参考
- **用户同时改 plan.yml** → 拒绝，让维护者改（铁律 18 零修改原则的镜像版：贡献者也不要改 schema）

---

## 5. 探针月报专用（type D）

```yaml
# 文件位置
data/reports/<vendor_id>/<plan_id>/<user-hash>-<date>.md
```

**user-hash**：本地 `sha256(token+salt)[:16]`，探针自动生成。**绝不要**用 GitHub 用户名做 hash（会暴露身份）。

**token_last4**：用 `***xxxx` 形式，**只保留后 4 位用于归属验证**。

**PR 模板必填字段**（按 `.github/PULL_REQUEST_TEMPLATE.md` 类型 C 段勾选）：

- 数据来源（厂商 / 套餐 / 时间窗 / 数据点数 / user_hash / token_last4）
- 核心指标（成功率 / 超时率 / 缓存命中率 / TTFT p50/p90/p99 / TPS p50）
- 厂商 monitor API 返回（5h / weekly / 30d MCP 三个百分比）
- 三方交叉验证结论（本地 vs monitor vs 标称 是否一致）
- 复现性（探针版本 / 生成时间）

**脱敏 4 检查**（缺一条即拒绝）：

- [ ] 无 prompt 内容
- [ ] 无 API key 明文
- [ ] token 只保留后 4 位
- [ ] token 存放在本地 keychain（无明文 JSON）

**频次**：同一 (vendor, plan) 每月最多 1 个 PR，超出请合并。

---

## 6. 返工案例（"PR 后我们还要改"的事故库）

### 案例 1：贡献者把官方材料放进 scraped/

**症状**：把厂商官方定价页截图放进 `scraped/`，导致 `data_status: community_report` 标签被错误分配。
**修复**：迁移到 `official/`，`data_status` 改 `vendor_official`。
**预防**：本 skill §1 决策树第 2 个分支（self-report / scraped / official 三者严格区分）。

### 案例 2：贡献者把个人实测当 official 提交

**症状**：用户自己的账单截图被放进 `official/`，并被 `vendor_official` 标签污染。
**修复**：迁移到 `scraped/`，`credibility: low`，加 `disputed: true`。
**预防**：§1 决策树第 1 个分支（[self-report] 永远走 scraped/）。

### 案例 3：贡献者把 scrap 数据当 official 提交

**症状**：社区博客推算的数字被放进 `official/`，并被 `vendor_official` 标签污染。
**修复**：迁移到 `scraped/`，`credibility` 给 `low`/`medium`，并加 `disputed: true`。
**预防**：§1 决策树第 3 个分支；§3 二次验证至少 2 个独立来源。

### 案例 4：新厂商 PR 只加了 vendor.yml，没加第一条 evidence

**症状**：PR 通过后 plan 出现在榜单，但 source_url 为空，无法审计。
**修复**：回滚 PR，要求补 `data/<id>/official/` 至少一条证据。
**预防**：§2 新厂商 checklist 3 件套。

### 案例 5：贡献者改了多个 vendor / plan 文件

**症状**：用户只让加 GLM v4，PR 顺手改了 Kimi / MiniMax 的 fields → 违反铁律 18。
**修复**：回滚无关改动，要求只动 PR 主题相关的文件。
**预防**：本 skill §2 + ledger-data-discipline 铁律 18（最小 diff）。

### 案例 6：贡献者没跑 build / lint 就提 PR

**症状**：yml 字段写错（缺 brand_color / affiliate 写错格式 / TIER_RATIOS 没同步），build 失败。
**修复**：要求本地跑 §2 的 4 个命令。
**预防**：PR 模板"类型 C"段已经把 4 条 build 检查做成必填 checklist。

### 案例 7：探针月报漏脱敏（贴了完整 token）

**症状**：用户复用了本地 config.json，token 明文进 PR 历史。
**修复**：立即 git filter-branch / BFG 清历史 + 强制用户重置 token。
**预防**：§4.5 self-report 脱敏 4 检查 + 本地导出页强制脱敏。

### 案例 8：贡献者把月度数据当周度（单位错）

**症状**：Kimi Allegretto weekly 填了 9.8 亿（实际是月度数字）。
**修复**：回滚，让贡献者按 `data_status` 字段分清周期。
**预防**：§3 二次验证 + 引用 ledger-data-discipline 铁律 3（B/亿 单位）+ 铁律 6（月度 ≤ 周 × 5）。

### 案例 9（自报新增）：贡献者凭印象给单点数据标 high credibility

**症状**：用户说"我这个月大概用了 1.8 亿 token"，维护者顺手填 `credibility: high`。
**修复**：改成 `credibility: low` + `disputed: true`，等第二个用户数据来再升级。
**预防**：§4.5 关键纪律第 1 条——单点必 low。

### 案例 10（自报新增）：贡献者把自己 PR 里改的 plan.yml 当作"贡献"

**症状**：用户提 [self-report] 同时改了 `data/plans/<plan>.yml` 的 measurements。
**修复**：回滚 yml 改动，让维护者改。用户的 PR 只放 scraped/ 截图。
**预防**：§4.5 关键纪律第 5 条——贡献者不要改 schema。

---

## 7. agent 引导贡献者的标准流程（SOP）

收到贡献请求后：

1. **判断贡献类型**（按 §1 决策树第 1 层）。**优先匹配"个人实测"分支**——这是最常见的。
2. **给贡献者一份完整路径清单**，包括：
   - 目标目录路径（带 `<vendor_id>` 占位符，让对方填）
   - 文件命名规则（`YYYY-MM-DD_<套餐名>_my_usage.png` 用于自报，`YYYY-MM-DD_<短描述>.md` 用于官方/社区）
   - 必填 frontmatter 字段清单（§3，仅官方一手需要）
   - 命名禁忌（空格、中文标点）
   - **脱敏要求**（token / API key / 邮箱 / 账号 ID 必须打码）
3. **截图工作流**（§4 + §4.5）—— 适用于"我截图了但不会写 frontmatter"的贡献者；自报路径甚至不需要 frontmatter。
4. **PR 模板勾选提示**：告诉对方在 PR 描述里勾对应类型（A / B / C / D / E），不要瞎填。
5. **跑本地构建提示**（仅对新厂商/新套餐）：§2 末 4 行命令。
6. **明确"维护者会做什么"**：贡献者交 evidence 后，维护者会按 §3 / §4.5 流程补 measurements / plan.yml，**不需要贡献者会写 YAML**。

---

## 8. 与已有资源的关系

| 资源 | 谁看 | 关系 |
|---|---|---|
| `docs/index.md`（榜单页底部 callout） | 人类（贡献者） | 第一入口，看到就能找到路径；自报行排在最前面 |
| `CONTRIBUTING.md`（仓库根） | 人类（贡献者） | 5 种贡献路径详解（自报排第一） |
| `docs/contributing.md`（站点侧） | 人类（贡献者） | 同上，站点版 |
| `.github/PULL_REQUEST_TEMPLATE.md` | 人类（贡献者） | 按类型勾选 + 必填字段（自报 = 类型 A） |
| `.agents/skills/contributions-data-routing/SKILL-and-SOP.md`（本文件） | **agent** | 决策树 + 返工案例库 |
| `.agents/skills/ledger-data-discipline/SKILL-and-SOP.md` | agent + 维护者 | 维护者改 yml 时怎么改 |
| `data/README.md` | agent + 维护者 + 高阶贡献者 | 目录规范权威源 |

**注意**：本文件不重复 `ledger-data-discipline` 的 27 条铁律，需要时引过去（§2 末 + §6 案例 8）。

---

## 9. 一句话总结

**先判断贡献类型（§1，优先匹配"个人实测"），再给完整路径 + 命名 + PR 勾选（§3 + §4 + §4.5 + §7），最后跑 4 条 build 命令（仅新厂商/新套餐）** —— 一次到位，PR 后不返工。