# 本地探针

::: warning 占位
文档建设中。当前探针源码在 `src/probe/`，跑法见仓库根 README。
:::

## 它做什么

- 透明代理你的 LLM API 请求（不改业务）
- 本地核账：请求次数 / TTFT / TPS / 状态码 / 超时
- 主动查厂商 monitor API：厂商声称的剩余额度
- 导出脱敏 PR 包：只含聚合指标 + token 后 4 位，无 token 明文

## 它不做什么

- 不上传 prompt 内容
- 不上传 API key / token
- 不上传 IP
- 不经手资金
