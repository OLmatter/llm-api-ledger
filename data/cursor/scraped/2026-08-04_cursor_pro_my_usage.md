---
evidence_id: e_2026_08_04_cursor_pro_my_usage
vendor_id: cursor
captured_at: 2026-08-04
captured_by: user
source_url: https://cursor.com/dashboard/usage
capture_method: dashboard-screenshots-csv-export-redacted-receipt
data_status: community_report
credibility: low
file_path: data/cursor/scraped/2026-08-04_cursor_pro_my_usage.md
related_plans:
  - cursor-pro
related_measurements:
  - m_2026_07_cursor_pro_single_user_cycle
  - m_2026_07_cursor_pro_model_grok_4_5
  - m_2026_07_cursor_pro_model_composer_2_5
---

# Cursor Pro single-user report: 2026-06-30 to 2026-07-30

## Subscription evidence

- Plan: Cursor Pro.
- Billing period: 2026-06-30 through 2026-07-30.
- Standard unit price on the receipt: USD 20.
- Amount paid: USD 10 after a one-time USD 10 friend-referral discount.
- The full receipt is intentionally not included because it contains a name, postal address, email,
  invoice number, and receipt number. Only the line-item/price area was retained.

## Dashboard totals

| Metric | Dashboard value |
|---|---:|
| Total tokens | 562M |
| Included tokens | 562M |
| On-demand tokens | 0 |
| Total spend-equivalent | USD 341.73 |
| Included spend-equivalent | USD 341.73 |
| On-demand spend | USD 0 |

## CSV cleaning and exact totals

The raw export contains 642 rows. For subscription-capacity analysis, only `Kind=Included` rows are
kept. `Cloud Agent ID` and `Automation ID` columns are removed from the sanitized file.

| Kind | Rows | Tokens | Treatment |
|---|---:|---:|---|
| Included | 631 | 561,145,630 | Kept |
| User API Key | 7 | 388,818 | Excluded: billed to the user's own key |
| free | 1 | 886,583 | Excluded: not paid subscription-pool usage |
| Errored, No Charge | 3 | 0 | Excluded: no token count and no charge |
| **Raw export total** | **642** | **562,421,031** | Dashboard rounds this to 562M |

Included-row time range in the CSV: `2026-06-30T19:24:17.431Z` to
`2026-07-30T18:46:03.716Z`.

## Included usage split by pool

| Pool | Included rows | Tokens | Share of clean included tokens |
|---|---:|---:|---:|
| Cursor Models (Cursor Grok 4.5 + Composer 2.5 variants) | 605 | 512,424,585 | 91.32% |
| Other Models | 26 | 48,721,045 | 8.68% |
| **Total** | **631** | **561,145,630** | **100%** |

The per-model details and a current-rate retail recomputation are in
`2026-08-04_cursor_pro_model_summary.csv`.

At the 2026-08-04 captured rates, that audit recomputation is USD 415.14224 for Cursor Models
and USD 50.35105 for Other Models (USD 465.49328 total), which is higher than the dashboard's
USD 341.73. Therefore the recomputation is used only to cross-check model mix and the approximate
Other Models range; it is not treated as Cursor's historical pool accounting.

## Pool-size inference

The contributor observed approximately 1% remaining in the Cursor Models pool at the end of the
cycle and inferred approximately USD 300 of Cursor Models capacity. The submitted screenshots show
the aggregate spend/tokens but do not show the remaining-percentage widget, so this value cannot be
independently reconstructed from the files and is marked `disputed: true`.

The Other Models allocation is estimated at roughly USD 48. As a cross-check, applying the official
rates captured on 2026-08-04 to the 26 Other Models rows produces USD 50.35105. The difference can be
caused by historical price changes, promotions, or Cursor's internal accounting. The evidence supports
an approximate USD 48-50 range, not a precise pool cap.

## Model-equivalent Cursor Models capacity

Using the repository's coding ratio (92% cache read, 7.3% uncached input, 0.7% output):

| Model | Effective USD/M | USD 300 equivalent | Conservative summary |
|---|---:|---:|---:|
| Grok 4.5 | 0.648 | 462,962,963 tokens | about 450M |
| Composer 2.5 | 0.238 | 1,260,504,202 tokens | about 1.2B |

These are scenario conversions of the inferred dollar pool, not direct token caps published by Cursor.
Fast variants are substantially more expensive and are not used for the headline equivalence.

## Privacy and reproducibility

- No prompt content is present.
- The full receipt is withheld; the retained crop excludes account/address/receipt identifiers.
- The sanitized CSV contains no Cloud Agent ID or Automation ID columns.
- BYOK/free/error rows remain documented in this summary but are not included in the submitted detail CSV.

## Evidence files

- `2026-08-04_cursor_pro_receipt_plan_price_redacted.png`
- `2026-08-04_cursor_pro_usage_tokens.png`
- `2026-08-04_cursor_pro_usage_spend.png`
- `2026-08-04_cursor_pro_included_usage_sanitized.csv`
- `2026-08-04_cursor_pro_model_summary.csv`
