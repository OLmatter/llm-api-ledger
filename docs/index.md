---
layout: home

hero:
  name: "LLM API Ledger"
  text: "LLM API 可信账本"
  tagline: 集齐主流厂商的真实用量与性能 · 本地装探针自核账 · 众包脱敏数据上榜
  actions:
    - theme: brand
      text: 看榜单
      link: '#leaderboard'
    - theme: alt
      text: 装探针
      link: /probe
    - theme: alt
      text: TG 群交流
      link: https://t.me/+s1flX6cpUZ1kM2M1
    - theme: alt
      text: GitHub
      link: https://github.com/OLmatter/llm-api-ledger
---

# 榜单 {#leaderboard}

<LeaderBoard />

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
- 💬 **交流大模型套餐 / 上报使用量：** [Telegram 群](https://t.me/+s1flX6cpUZ1kM2M1)（也是 glm-coding-helper 用户群，欢迎来聊大模型套餐选型、把自己的真实使用量报上来帮助更多人）

> 我们刚起步，榜单数据仍在补全中。**你用的厂商/套餐没上榜？把数据报上来，下一个就是你。**
