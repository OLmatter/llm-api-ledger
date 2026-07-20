# PR 提交模板

## 数据来源

- **厂商**: <!-- 如 zhipu / deepseek / openai -->
- **套餐**: <!-- 如 zhipu-glm-pro -->
- **时间窗**: <!-- 起止时间 -->
- **数据点数**: <!-- 探针记录的请求数 -->
- **user_hash**: <!-- sha256(token+salt)[:16] -->
- **token_last4**: <!-- ***xxxx -->

## 核心指标（从导出页复制）

- 成功率: xx%
- 超时率: xx%
- 缓存命中率: xx%
- TTFT p50/p90/p99: xx / xx / xx ms
- TPS p50: xx tok/s

## 厂商声称额度（monitor API）

- 5h 窗口: xx%
- weekly: xx%
- 30d MCP: xx%

## 三方交叉验证结论

<!-- 本地计数 vs monitor 返回 vs 套餐标称 是否一致？如不一致，描述差异 -->

## 复现性

- 探针版本: <!-- v0.1.0-alpha 等 -->
- 生成时间: <!-- 从导出页自动带 -->

---

本 PR 由 llm-api-ledger 探针自动生成的 Markdown 模板填写。数据已脱敏（无 prompt 内容、无 API key、无完整 token）。
