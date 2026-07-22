# 导出 PR 包

::: warning 占位
文档建设中。
:::

探针 Web UI：访问 `http://127.0.0.1:8080/__ledger__/export`，选时间窗口（1-90 天），生成脱敏 JSON 包 + PR 描述模板。

PR 包内容：
- 聚合指标：TTFT p50/p90/p99、TPS 分布、状态码统计、超时率、缓存命中率
- 厂商声称用量：5h/周/月剩余百分比曲线
- **匿名 user_hash**（sha256(token+salt) 前 12 位）
- **不含**：token 明文、prompt 内容、IP、任何 PII
