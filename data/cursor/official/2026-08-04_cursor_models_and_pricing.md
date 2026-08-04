---
evidence_id: e_2026_08_04_cursor_models_and_pricing
vendor_id: cursor
captured_at: 2026-08-04
captured_by: codex
source_url: https://cursor.com/docs/models-and-pricing
capture_method: requests-next-data-parse
data_status: vendor_official
credibility: high
file_path: data/cursor/official/2026-08-04_cursor_models_and_pricing.md
related_plans:
  - cursor-pro
related_measurements:
  - m_2026_07_cursor_pro_model_grok_4_5
  - m_2026_07_cursor_pro_model_composer_2_5
---

# Cursor model pools and token pricing

## Pool structure

Cursor documents two independent pools that reset with the monthly billing cycle:

- **Cursor Models**: Grok 4.5 and Composer 2.5.
- **Other Models**: third-party models deducted at API-equivalent pricing; Pro includes at least USD 20.

## Captured model rates

All values are USD per million tokens.

| Model | Uncached input | Cache read | Output |
|---|---:|---:|---:|
| Grok 4.5 | 2.00 | 0.50 | 6.00 |
| Grok 4.5 Fast | 4.00 | 1.00 | 18.00 |
| Composer 2.5 | 0.50 | 0.20 | 2.50 |
| Composer 2.5 Fast | 3.00 | 0.50 | 15.00 |
| Claude Opus 4.8 | 5.00 | 0.50 | 25.00 |
| GPT-5.6 Terra | 2.00 | 0.20 | 12.00 |
| Kimi K3 | 3.00 | 0.30 | 15.00 |

For models with a distinct cache-write price, the sanitized model summary uses the official
cache-write rate captured on the same page (Opus 4.8: USD 6.25/M; GPT-5.6 Terra: USD 2.50/M).

## Verification

- The rendered documentation names Grok 4.5 and Composer 2.5 as the Cursor Models pool.
- The page's serialized model table was parsed to recover the numeric pricing fields.
- The contributor's CSV model names align with the standard/Fast variants in the official table.

## Uncertainty

These rates were captured on 2026-08-04, after the measured cycle ended on 2026-07-30.
The recomputed retail values are an audit cross-check, not a claim that Cursor used identical
historical pricing or promotion multipliers for every request in the cycle.

## Related evidence

- `data/cursor/scraped/2026-08-04_cursor_pro_model_summary.csv`
- `data/vendors/cursor.yml`
- `data/plans/cursor-pro.yml`
