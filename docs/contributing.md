# 贡献指南

LLM API Ledger 的所有数据来自社区贡献。我们不维护私有数据集，**贡献归属完全依赖 GitHub PR 流程** —— 你的 PR 作者会自动出现在仓库 Contributors 列表、commit 历史和 GitHub contribution graph 里，**项目不会单独维护 in-app 贡献者 credit / badge 系统**。

下面按门槛从低到高列出三种贡献路径。任选一种即可，不必都做。

---

## 方式 1：你买了 X 套餐，这是你的实测（最常见 / 最低门槛）

适用：你买了某个套餐跑了一段时间，有账单截图 / 厂商 monitor API 页面截图 / CSV 导出 / IDE 用量截图。**这是大多数人贡献数据的方式**——一次性，不需要装探针。

1. Fork 仓库，把你的截图或导出文件放进 `data/<vendor_id>/scraped/`。
   - `<vendor_id>` 是厂商在 `data/vendors/<vendor_id>.yml` 里的标识，全小写、无空格（例：`zhipu`、`openai`、`zai`）。
   - 不知道 `vendor_id` 就先开 Issue 问，或按方式 3 新建厂商路径。
2. 命名：`YYYY-MM-DD_<套餐名>_my_usage.md` 或 `.png`，多图加 `_1/_2/_3`。
3. **截图请务必打码**：完整 token / API key / 个人邮箱 / 账号 ID 涂黑后再传。
4. **不需要写 frontmatter**——把文件扔进来就行，PR 描述里写清：
   - 你买了哪个套餐
   - 跑了多久
   - 你看到的数字（用过的 token / 撞限的窗口 / 截图里展示的关键数据）
5. 提 PR，标题写 `[self-report] 我买了 <vendor_id>-<plan_id> <一句话总结>`，例：`[self-report] 我买了 zhipu-glm-coding-pro-v3 用了一个月`。
6. 维护者审核：
   - 会按你截图里的数字补 `data/plans/<plan_id>.yml` 的 measurements（`source_kind: community_report`，`credibility: low`，`evidence_path` 指向你的文件）。
   - 单点数据按铁律 10 标 `disputed: true`（等第二个用户数据来再升级 median）。
   - 你不必会写 YAML，也不必读懂 schema。

注意：

- **不要贴完整 token / API key / prompt 内容**。
- 截图可读的最小要素：套餐名 + 周期 + 关键数字（额度 / 用量 / 撞限状态）。
- 个人实测跟"社区第三方博客推算"放在同一个 `scraped/` 目录，但 PR 标题前缀要分清（`[self-report]` vs `[scraped]`）。

---

## 方式 2：直接提交官方一手材料

适用：你看到了厂商官方页面（定价、限额、抵扣系数、monitor API 截图），想分享给维护者。

1. Fork 仓库，本地把材料放进 `data/<vendor_id>/official/`。
   - 一手材料（厂商官网 / 文档 / 公告）→ `official/`；社区推算、第三方博客、你的浏览器观察 → `scraped/`。两类不要混放。
2. 命名：`YYYY-MM-DD_<短描述>.md` 或 `.png`。
3. 文字证据 frontmatter 至少填：`evidence_id / vendor_id / captured_at / captured_by / source_url / capture_method / data_status / credibility / file_path / related_plans`。
4. 截图证据：截全屏、字能看清、命名说清厂商 + 数据内容。
5. 提 PR，标题写 `[evidence] <vendor_id> <短描述>`，例：`[evidence] zhipu GLM Coding Plan v3 overview 2026-07-31`。
6. 维护者审核：按 `data/README.md` 的"什么时候必须建 evidence 文件"清单检查 source_kind 是否合规，跑 lint 和 `node scripts/build-plans.mjs` 验证不被破坏。

维护者会按材料创建 / 更新 `data/vendors/` 和 `data/plans/` YAML，并在 measurement 里通过 `evidence_path` 引用你的文件。**你不必会写 YAML**。

---

## 方式 3：新建厂商或套餐（中门槛）

适用：你发现了榜单没收录的厂商，或新版本套餐。

1. **新建厂商**：先提一个 PR 同时包含：
   - `data/vendors/<vendor_id>.yml`：厂商元数据（homepage / brand_color / shared_features / affiliate 等）。参考现有 `data/vendors/openai.yml`。
   - `data/<vendor_id>/official/`：第一条证据（官网定价页截图 / monitor API 抓取结果）。
2. **新建套餐**：在同一个 PR 或后续 PR 加 `data/plans/<plan_id>.yml`，并按 `data/README.md` 的 evidence 规范建 `official/` 文件。
3. **跑一遍构建**：
   ```bash
   node scripts/build-plans.mjs
   node scripts/lint-plans.mjs
   npx vitepress build docs
   node scripts/data-diff.mjs
   ```
   确保 lint 通过、页面正常渲染、data-diff 无意外字段变化。
4. 提 PR，标题写清 `[new vendor] <vendor_id>` 或 `[new plan] <vendor_id>/<plan_id>`。

数据纪律铁律（每条都对应历史踩坑）见 `.agents/skills/ledger-data-discipline/SKILL-and-SOP.md`，提交前请把 27 条铁律里的 `铁律 1 / 3 / 9 / 10 / 16 / 17 / 18 / 27` 看完。

---

## 方式 4：跑探针并提交脱敏 PR 包（高门槛 / 数据最硬）

适用：你想长期贡献真实用量数据（≥ 7 天连续）。

1. 下载并跑探针（见 [本地探针页面](/probe)）。连续跑 ≥ 7 天。
2. 探针导出页（`/__ledger__/export`）会按 [PR 模板](https://github.com/OLmatter/llm-api-ledger/blob/main/.github/PULL_REQUEST_TEMPLATE.md) 自动生成脱敏 Markdown。
3. 把内容粘贴到 PR 描述里，提 PR 到 `data/reports/<vendor_id>/<plan_id>/<user-hash>-<date>.md`。
4. PR 通道会自动把这次数据标 `credibility: high`，写入 `plans.json` 时权重高于匿名自动通道。

PR 标题写清 `[report] <vendor_id>/<plan_id> <YYYY-MM>`。同一套餐每月最多提 1 个。

---

## 方式 5：报 bug / 提建议

开 GitHub Issue 即可。**永远不要贴完整 token、API key、prompt 内容**。

---

## 代码 / 文档贡献

代码改动提 PR 时附：改动说明 + 测试方式（手跑命令 + 预期输出）+ schema 改动附带 migration。

不接受：

- 跳过测试直接合并
- 在代码 / 日志里硬编码 token / key
- 删除安全相关代码（keychain / 脱敏）

---

## 数据隐私承诺

- ❌ **不上传**：prompt 内容、API key、用户 IP、完整 token
- ✅ **只上传**：聚合指标（TTFT / TPS 分布、状态码统计、超时率、缓存命中率）+ token 后 4 位用于归属验证
- Token 存在你本机的系统 keychain（Windows Credential Manager / macOS Keychain / Linux Secret Service），不写明文

## 贡献归属

- 仓库 Contributors 页面、commit 历史、GitHub contribution graph 自动展示你的贡献
- 5+ 有效 PR 后可申请 reviewer 权限（合并其他人提交的 evidence / plan PR）
- 不维护任何 in-app 贡献者 credit、积分或 badge 系统 —— GitHub 自带的归属就够了