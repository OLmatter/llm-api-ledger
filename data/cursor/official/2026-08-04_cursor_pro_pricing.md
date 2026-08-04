---
evidence_id: e_2026_08_04_cursor_pro_pricing
vendor_id: cursor
captured_at: 2026-08-04
captured_by: codex
source_url: https://cursor.com/pricing
capture_method: requests-html-parse
data_status: vendor_official
credibility: high
file_path: data/cursor/official/2026-08-04_cursor_pro_pricing.md
related_plans:
  - cursor-pro
related_measurements: []
---

# Cursor Pro pricing and usage-pool structure

## Official data points

| Field | Value | Evidence |
|---|---:|---|
| Pro monthly price | USD 20 | Cursor pricing page, Individual/Pro selector |
| Usage reset | Monthly billing cycle | Cursor models/pricing documentation |
| Cursor Models pool | Grok 4.5 and Composer 2.5 | Cursor models/pricing documentation |
| Other Models pool | At least USD 20/month on Pro | Cursor models/pricing documentation |

The official pricing page describes Pro as having extended Agent limits and generous Grok/Composer
limits. The models/pricing documentation says the two pools reset separately each billing month.

## Secondary verification

- The contributor's redacted receipt shows `Cursor Pro`, `Jun 30-Jul 30, 2026`, and a USD 20 unit price.
- The receipt also shows a one-time USD 10 friend-referral discount. This is account-specific evidence
  and is not encoded as a generally available introductory price or affiliate offer.

## Uncertainty

Cursor does not publish an exact dollar amount for the Cursor Models pool on the captured pages.
The approximately USD 300 figure in the self-report is therefore a disputed single-user inference.

## Related evidence

- `data/cursor/official/2026-08-04_cursor_models_and_pricing.md`
- `data/cursor/scraped/2026-08-04_cursor_pro_receipt_plan_price_redacted.png`
- `data/plans/cursor-pro.yml`
