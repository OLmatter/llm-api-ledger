---
evidence_id: e_2026_08_28_kimi_k3_launch
vendor_id: kimi
captured_at: 2026-08-28
captured_by: claude
source_url: https://www.kimi.com/code
capture_method: webfetch-plus-web-search
data_status: vendor_official
credibility: high
file_path: data/kimi/official/2026-08-28_kimi_k3_launch.md
related_plans:
  - kimi-code-andante
  - kimi-code-allegretto
  - kimi-code-moderato
  - kimi-code-allegro
related_measurements:
  - m_2026_08_kimi_k3_model_generation
---

# Kimi K3 正式上线；Code Plan 模型代际切换（K2.7 Code / K3）；平台迁移 moonshot→kimi.com

## 原文摘录

> kimi.com 首页标题："K3 上线，专为智能体编程与知识工作打造"
> kimi.com/code："Kimi K3 正式上线……最高 1M 上下文"；"Moderato 及更高档位套餐可使用 K3 模型"
> platform.kimi.com/docs/pricing/chat：模型入口 "Kimi K3（旗舰模型,1M token 上下文）、Kimi K2.7 Code（Coding 模型,多模态）、Kimi K2.6（视觉+文本）"；"Moonshot V1 预计 8 月 31 日全平台下线"
> CLI 演示界面："Model: K2.7 Code"

## 数据点

| 字段 | 值 | 备注 |
|---|---|---|
| K3 发布 | 2026-07-17 | 参数规模 2.8 万亿（第三方口径），1M 上下文 |
| Code Plan K3 门槛 | **Moderato 及以上** | Andante/Allegretto 不可用 K3 |
| CLI 编程模型 | K2.7 Code | 多模态编程模型 |
| 四档价格 | ¥49/99/199/699 | 与账本一致，本轮未发现变价 |
| 平台迁移 | platform.moonshot.cn → platform.kimi.com (301) | 文档域名已切换 |
| Moonshot V1 | 2026-08-31 全平台下线 | 老模型退役 |

## 存疑（待证）

1. **档位数量**：第三方横评（CodePick 2026-08）称"5 档套餐 ¥49–¥699"，账本仅 4 档。可能存在第 5 档（新增顶配或入门下探），**购买页 JS 渲染未能直接核实**，不新增 yml，待用户截图。
2. **限购**：第三方称 Kimi 8 月出现"限购"（新用户购买受限），性质与范围不明，待官方公告。
3. **"Token Plan 全档位支持 K3"**（第三方转述）：Kimi 若另设 Token Plan 与 Code Plan 并行，账本未收录，待确认。

## 对账本的动作

- 榜单现有 @K3 探针实测（Allegretto 25.4M/508M/1B 等）与本轮 K3 上线时间线吻合（K3 7-17 上线，实测 7 月下旬），**实测数据仍有效**。
- Andante/Allegretto 两档**不能用 K3**（仅 Moderato+），前端如按"全档 @K3"展示需修正口径。

## 二次验证（必填）

- [x] kimi.com 首页 + /code 页 WebFetch 直接确认 K3 上线与档位门槛
- [x] platform.kimi.com 文档页确认 K3/K2.7 Code/K2.6 模型线与 V1 退役
- [x] 四档价格与账本对账一致（¥49/99/199/699）
- [ ] 第 5 档存在性、限购政策：未证实，标存疑

## 不确定 / 存疑

见上"存疑"节。

## 关联引用

- vendor: data/vendors/kimi.yml
- plans: data/plans/kimi-code-{andante,allegretto,moderato,allegro}.yml
