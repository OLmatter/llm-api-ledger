# PR 提交模板

> 选择本次贡献类型，按对应章节填写。删掉不相关的章节。
>
> 维护者会按 [数据纪律铁律](../.agents/skills/ledger-data-discipline/SKILL-and-SOP.md) 审核，重点看 source_kind / evidence_path / 最小 diff / 不擅自改动其他字段。
>
> **永远不要贴完整 token、API key、prompt 内容。**

---

## 贡献类型

- [ ] 我买了 X 套餐，这是我的实测（路径：方式 1 — **最常见**）
- [ ] 直接提交官方一手材料（路径：方式 2）
- [ ] 新建厂商或套餐（路径：方式 3）
- [ ] 跑探针并提交脱敏 PR 包（路径：方式 4）
- [ ] 报 bug / 提建议
- [ ] 代码 / 文档改动

---

## 类型 A：你买了 X 套餐，这是你的实测（最常见）

<!-- 适用于把自己账单/截图/monitor API 页面截图扔进 data/<vendor>/scraped/ -->

- **厂商 + 套餐**：`<!-- zhipu-glm-coding-pro-v3 -->`
- **vendor_id**：`<!-- 跟 data/vendors/<id>.yml 对齐 -->`
- **目标目录**：`data/<vendor_id>/scraped/`
- **文件名**：`YYYY-MM-DD_<套餐名>_my_usage.md` 或 `.png`
- **跑了多久**：`<!-- 3 天 / 1 周 / 1 个月 -->`
- **关键数字（按截图复制）**：
  - 用了多少 token：`<!-- 1.8 亿 / 508M / 12 万 ... -->`
  - 撞限状态：`<!-- 5h 撞 429 / weekly 还剩 30% / 从未撞过 -->`
  - 实际跑多少请求：`<!-- 6700 次 / 大约 30 次/小时 -->`
- **脱敏检查**：
  - [ ] token / API key 已打码
  - [ ] 个人邮箱 / 账号 ID 已打码
  - [ ] prompt 内容未贴入
  - [ ] 截图能看到套餐名 + 周期 + 关键数字

---

## 类型 B：直接提交官方一手材料

<!-- 适用于把官方定价页 / 文档 / 公告 抓取结果放进 data/<vendor>/official/ -->

- **厂商**：`<!-- zhipu / openai / zai ... -->`
- **vendor_id**：`<!-- 跟 data/vendors/<id>.yml 对齐 -->>`
- **目标目录**：`data/<vendor_id>/official/`
- **文件名**：`YYYY-MM-DD_<短描述>.md` 或 `.png`
- **原始 URL**：`<!-- https://docs.bigmodel.cn/cn/coding-plan/overview -->`
- **抓取方法**：`<!-- chrome-dump-dom / chrome-cdp-runtime-evaluate / 人工截图 -->`
- **抓取日期**：`YYYY-MM-DD`
- **data_status**：`<!-- vendor_official / anthropic_official / community_report / scraped -->`
- **credibility**：`<!-- high / medium / low -->`
- **关联套餐 ID**：`<!-- 计划应用到哪些 plan.yml，可以是未来的 -->`
- **是否包含敏感信息检查**：
  - [ ] 已打码所有 token / API key / 用户账号
  - [ ] 已打码所有 prompt 内容

---

## 类型 C：新建厂商或套餐

<!-- 适用于首次把厂商/套餐纳入榜单。需提供厂商元数据 + 第一条证据 + 套餐 YAML。 -->

- **vendor_id**：`<!-- 跟 data/vendors/<id>.yml 文件名一致，全小写、无空格 -->`
- **新增 / 修改文件清单**：
  - [ ] `data/vendors/<vendor_id>.yml`
  - [ ] `data/plans/<plan_id>.yml`
  - [ ] `data/<vendor_id>/official/<第一条证据>`
  - [ ] （如适用）`scripts/build-plans.mjs` 的 `VENDOR_RATIOS` / `TIER_RATIOS` 新增条目
- **首选模型**：`<!-- 主力对比模型，例如 GLM-5.2 / MiniMax-M3 -->`
- **邀请码**（如有）：`<!-- code / url / discount / expires，写法见 data/vendors/openai.yml -->`
- **本次是否同时修改其他 vendor / plan 文件**：否 / 是（如果是，请列出 file_path + 一行说明）
- **跑过的本地检查**：
  - [ ] `node scripts/build-plans.mjs` 通过
  - [ ] `node scripts/lint-plans.mjs` 通过
  - [ ] `npx vitepress build docs` 通过
  - [ ] `node scripts/data-diff.mjs` 输出无意外字段变化
- **数据纪律自检**（铁律 1 / 3 / 9 / 10 / 16 / 17 / 18 / 27）：已读、已对照、没问题

---

## 类型 D：探针月报（脱敏 PR 包）

<!-- 本节由探针导出页自动填充最稳，手填请按下面字段 -->

### 数据来源

- **厂商**: <!-- 如 zhipu / deepseek / openai -->
- **套餐**: <!-- 如 zhipu-glm-coding-pro-v3 -->
- **时间窗**: <!-- 起止时间 -->
- **数据点数**: <!-- 探针记录的请求数 -->
- **user_hash**: <!-- sha256(token+salt)[:16] -->
- **token_last4**: <!-- ***xxxx -->

### 核心指标（从导出页复制）

- 成功率: xx%
- 超时率: xx%
- 缓存命中率: xx%
- TTFT p50/p90/p99: xx / xx / xx ms
- TPS p50: xx tok/s

### 厂商声称额度（monitor API）

- 5h 窗口: xx%
- weekly: xx%
- 30d MCP: xx%

### 三方交叉验证结论

<!-- 本地计数 vs monitor 返回 vs 套餐标称 是否一致？如不一致，描述差异 -->

### 复现性

- 探针版本: <!-- v0.1.0-alpha 等 -->
- 生成时间: <!-- 从导出页自动带 -->

### 脱敏检查

- [ ] 无 prompt 内容
- [ ] 无 API key 明文
- [ ] token 只保留后 4 位
- [ ] token 存放在本地 keychain（无明文 JSON）

---

## 类型 E：代码 / 文档改动

- **改动说明**：`<!-- 改了什么 + 为什么 -->`
- **测试方式**：`<!-- 手跑命令 + 预期输出 -->`
- **是否动 schema / data 字段**：否 / 是（如果是，附 migration）
- **本地构建**：`<!-- npx vitepress build docs / scripts/data-diff.mjs 跑过的输出片段 -->`

---

## 通用：贡献归属

本次 PR 的贡献归属会通过 GitHub 自带的机制展示：

- 仓库 Contributors 页面（你的头像 + PR 计数）
- commit 历史（作者署名）
- GitHub contribution graph（绿块自动累加）

**项目不维护任何 in-app 贡献者 credit / badge / 积分系统** —— 上面这些已经够了。