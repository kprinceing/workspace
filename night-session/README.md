# Night session teaching data

Synthetic staggered minimum-wage / teen-employment panel for the **Reliable AI for Empirical Research** night workshop.

## Clone this folder

```bash
git clone https://github.com/kprinceing/workspace.git
cd workspace/night-session
```

## Quick check (Exercise 7.0)

```bash
wc -l data/panel_s0.csv          # expect 1001 lines (header + 1000 rows)
cat data/row_ledger_s0.csv       # adopting=700, never_treated=300, total=1000
cat data/row_ledger_s2.csv       # adopting=648, never_treated=300, total=948
```

## Files

| File | Role |
|------|------|
| `data/panel_s0.csv` | **S0 clean** panel — 50 states × 20 years, locked effect path |
| `data/panel_s1.csv` | **S1 trends** panel — differential untreated trends planted |
| `data/panel_s2.csv` | **S2 sample** panel — selective row loss after bad merge |
| `data/employment_raw.csv` | Raw employment counts for merge exercise |
| `data/population_weights.csv` | Population weights with deliberate post-2010 code mismatch |
| `data/policy_ledger.csv` | State adoption years |
| `data/answer_key_effects.csv` | Locked cohort-time effect path (auditor answer key) |
| `data/row_ledger_s0.csv` / `row_ledger_s2.csv` | Row counts by group before/after S2 loss |
| `specs/*.template.md` | Blank specification templates for exercises |

## Regenerate (instructors)

Requires Stata MP:

```bash
cd night-session
/Applications/Stata/StataMP.app/Contents/MacOS/stata-mp -b do code/export_data.do
```

Seed is fixed at `20260721`. This DGP is synthetic teaching data — it makes no claim about real minimum-wage effects.
