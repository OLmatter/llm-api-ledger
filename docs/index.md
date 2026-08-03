---
layout: home

hero:
  name: "LLM API Ledger"
  text: "LLM API 可信账本"
  tagline: 集齐主流厂商的真实用量与性能 · 本地装探针自核账 · 众包脱敏数据上榜
  actions:
    - theme: brand
      text: 看榜单 →
      link: '#leaderboard'
    # 截图分享时, 让群友直接看到 repo (避免搜不到)。放 actions 里才能和主按钮同行对齐
    - theme: alt
      text: 'github: OLmatter/llm-api-ledger'
      link: https://github.com/OLmatter/llm-api-ledger
    # 第三个无 link 的按钮, 显示「最新更新」时间, build 脚本自动从 git log 取日期填进来
    - theme: alt
      text: '📅 最新更新 2026-08-04 03:33'
---

# 榜单 {#leaderboard}

<LeaderBoard />

## 🚀 现在的厂商越来越坑，甚至我们只有联合起来才能有看清！假如你有数据！欢迎加入项目的贡献者！{#how-to-contribute}

**假如你有 agent 的话，直接把你知道的信息告诉它，它看了 `.agents/skills/contributions-data-routing/SKILL-and-SOP.md` 就会自动提 PR 了。**

不会用 agent？按下面表格手动提 PR：

下面按"实际最常见 → 少见"排列，PR 要交到仓库哪些目录一目了然：

| 你手上有什么 | 提交到哪里 | PR 标题示例 |
|---|---|---|
| 🛒 **你买的套餐 + 你的真实用量**（账单截图 / monitor API 页面 / CSV 导出） | `data/<vendor_id>/scraped/` | `[self-report] 我买了 zhipu-glm-coding-pro-v3 用了一个月` |
| 📷 **官方一手材料**（厂商定价页 / 文档摘录 / 公告） | `data/<vendor_id>/official/` | `[evidence] zhipu GLM Coding Plan v3 overview 2026-07-31` |
| 🔍 **社区观察 / 第三方博客 / 浏览器记录** | `data/<vendor_id>/scraped/` | `[scraped] kimi allegretto 社区推算 2026-08-01` |
| 🆕 **新厂商 / 新套餐** | 同时加 `data/vendors/<id>.yml` + `data/plans/<id>.yml` + `data/<id>/official/` | `[new vendor] <vendor_id>` 或 `[new plan] <vendor_id>/<plan_id>` |
| 📊 **跑探针 ≥ 7 天的脱敏月报** | `data/reports/<vendor_id>/<plan_id>/<user-hash>-<date>.md` | `[report] <vendor_id>/<plan_id> <YYYY-MM>` |

**估计大多数人都是「我买了 X 套餐，用了多少」**——这就是第一行，最常见也最低门槛。**截图或导出发票扔进 PR**，维护者会按证据建表。

**`<vendor_id>` 怎么看**：去 [`data/vendors/`](https://github.com/OLmatter/llm-api-ledger/tree/main/data/vendors) 里找现成的小写标识（`zhipu`、`openai`、`zai`、`volcengine`、`kimi`、`minimax`、`anthropic`、`opencode`、`chatgpt`）；没收录就按"新厂商"行开 PR。

**完整规范**：[`data/README.md`](https://github.com/OLmatter/llm-api-ledger/blob/main/data/README.md)（evidence frontmatter 必填字段 / 命名 / 什么时候必须建 evidence 文件） · [PR 模板](https://github.com/OLmatter/llm-api-ledger/blob/main/.github/PULL_REQUEST_TEMPLATE.md)（按贡献类型勾选） · [贡献指南](/contributing)（4 种路径详解）

## 加入交流群 {#community}

<div style="display: flex; gap: 2rem; align-items: center; flex-wrap: wrap; margin: 1rem 0 2rem;">

![Coding AI 交流群微信群二维码](/wechat-qr.png){width=220}

<div>
<p style="margin-top: 0;"><strong>📱 微信群：Coding AI 交流群</strong></p>
<p>扫码加入。<strong>大众立场,跟各家企业群不同</strong>——不替任何厂商站台,套餐好不好全靠用户自己反馈。</p>
<p style="color: #888; font-size: 0.9em;">⚠ 二维码 7 天内有效（2026-08-08 前），过期后群内将更新。</p>
<p>另有 <a href="https://t.me/+s1flX6cpUZ1kM2M1">Telegram 群</a>(glm-coding-helper 用户群)。</p>
</div>
</div>

## 为什么做这个 {#why-this}

**国内 Coding Plan 市场正在变成耍猴大赛。**

你以为买的是"每月 1000 次"——结果：

- 🔥 **动态倍率**：同一句话，账单扣多少全看实时负载和模型路由，你以为跑 1 次，实际扣 100 倍额度也说不准——倍率表藏得越深越有鬼
- 🙈 **不标承诺用量**：只写"日常额度 / 澎湃额度"这种词，绝口不提具体多少 token
- 💰 **积分通胀**：某家给你一个月 **820 亿——积分！** 听着是不是要上天？但计费倍率几百起步，缓存命中 2.5 积分/token、未命中 300 积分/token，算下来实际能跑的 token 远没有数字唬人。积分看着涨了 50 倍，计费系数也偷偷跟着调
- 🚫 **整天 429**：有限流没额度，有额度跑不出来——钱付了，token 没跑成

**结果就是：你抢到的套餐到底能跑多少，没人说得清。厂商自己说的，你敢信吗？**

---

### 我们做什么 {#what-we-do}

**很简单一句话：把厂商说的、用户实测的、官方 monitor 公布的，三方摆一起。**

| 维度 | 厂商宣传 | 我们榜单 |
|---|---|---|
| **用量** | "澎湃额度""10 亿积分" | 探针实测反推到 100% 满 |
| **倍率** | 藏在文档角落 | 显式标注（高峰 ×3 / ZCode ×0.67）|
| **可信度** | "我们的产品很稳定" | 三级标签 + 数据争议红 ⚠ |
| **价格** | "首单 49.9！"（续费呢？）| 原价 + 首单价 + 邀请码叠加分开列 |
| **限流** | 不提 | 5h / 周 / 月三周期独立展示 |

**榜单客观铁律：邀请码不影响排序、没邀请码的套餐照样上榜、单点数据标红警示。** 我们不卖货、不返佣、不经手 token、不经手资金——榜单存在的唯一理由，就是让你在掏钱之前看清楚自己买的是什么。

> 📊 **榜单数据仍在补全中，我们刚起步。你用的套餐没上榜？把数据报上来，下一个就是你。**

## 项目是什么 {#what}

**一句话**：LLM API 领域的可信数据账本。不经手 Token、不经手资金。

- **横向对比对象**：厂商 × 套餐（如「火山方舟 Coding Plan Pro」「智谱 GLM Coding Plan Max」）
- **每行内容**：这个套餐在真实开发者使用下能交付多少
- **数据来源**：用户本地装探针跑真实流量 → 脱敏后提 PR 上榜

## 为什么可信 {#why}

| 设计 | 保障 |
|---|---|
| 服务端零账号 | 用户身份 = `sha256(token+salt)` 匿名 hash，绝不上传 token |
| 双源采集 | 探针同时记本地计数 + 厂商 monitor API，交叉验证 |
| 三级可信度 | 单用户 low / 3+ 用户 medium / PR 验证 high |
| 榜单客观 | 邀请码不影响排序，没邀请码的套餐照样上榜 |

## 怎么贡献 {#how}

1. 装探针：`/probe`
2. 跑真实编码流量 7+ 天
3. 导出脱敏 PR 包：`/probe-export`
4. 提 GitHub PR，绿标认证等社区 reviewer 审核

详见 [贡献指南](/contributing) 和 [数据口径](/methodology)。

## 反馈与交流 {#contact}

- 🐛 **数据有误 / 缺失厂商？** [提 GitHub Issue](https://github.com/OLmatter/llm-api-ledger/issues)（标 `data-correction` 或 `vendor-request`）
- 💬 **Telegram 群**：[glm-coding-helper 用户群](https://t.me/+s1flX6cpUZ1kM2M1)

> 我们刚起步，榜单数据仍在补全中。**你用的厂商/套餐没上榜？把数据报上来，下一个就是你。**
