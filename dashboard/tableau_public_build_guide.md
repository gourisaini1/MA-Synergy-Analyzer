# Tableau Public implementation guide

This guide turns the repository's Tableau specification and CSV outputs into a publishable Tableau Public workbook. It is deliberately a build guide rather than a claim that a workbook has already been published: publishing requires an authenticated Tableau Public session.

## Workbook structure

Create one Tableau workbook with five dashboards. Use separate logical tables/relationships rather than physically joining unlike-grain datasets.

| Dashboard | Primary source | Supporting sources | Purpose |
|---|---|---|---|
| 1. Executive deal scorecard | `deal_comparability.csv` | `deal_evidence_backtest.csv` | Compare evidence coverage and distinguish estimated, announced, realised and unverified items |
| 2. Synergy bridge | `tableau_synergy_data.csv` | `announced_synergy_targets.csv`, `quantitative_backtest.csv` | Show low/base/high analyst scenarios beside management targets and reported outcomes |
| 3. Financial & integration diligence | `financial_due_diligence.csv` | `integration_cost_tracker.csv`, `integration_risk_register.csv` | Display reported metrics, integration milestones, disclosed costs and open risks |
| 4. Operational sensitivities | `zomato_operational_sensitivities.csv` | `air_india_procurement_hurdles.csv` | Show Blinkit unit-economics scenarios and Air India reverse procurement hurdles |
| 5. Market reaction | `event_study_results.csv` | `market_prices.csv` | Show CAR/t-statistics only where a valid event study exists; show raw price references separately |

Keep Microsoft–LinkedIn visually labelled as a reference case, not one of the four core deals.

## Data modelling rules

1. Relate deal-level sources on `deal_id` only when both sides have that field. For sources without a common deal key, keep a separate data source and use dashboard filter actions rather than forcing a many-to-many join.
2. Do not join scenario rows to financial diligence rows on deal alone: that creates row multiplication and inflated sums.
3. Keep currency in every measure view. Never sum INR and USD values.
4. Preserve blank values. In Tableau, use explicit status labels such as `Not disclosed`, `Not quantified`, or `Daily data unavailable`; do not use `ZN()` on unknown financial values.
5. Keep `evidence_class` / classification visible. Announced targets, analyst estimates and reported realisations are different evidence classes.
6. Keep scenario rows labelled as sensitivities where the source says illustrative or reverse hurdle. Do not relabel them as forecasts.

## Dashboard 1 — Executive deal scorecard

- KPI tiles: core deals covered (4), deals with quantified independent model, deals with an announced numeric target, deals with publicly reported realisation, and deals with unquantified integration costs.
- A four-row deal matrix with columns for independent estimate, management target, reported realisation, evidence quality and principal open diligence item.
- Use a status colour only for evidence quality; do not encode unknown as zero.
- Add a deal selector that filters all dashboard sheets.

## Dashboard 2 — Synergy bridge

- Use a low/base/high selector parameter to display one scenario at a time.
- Show separate bars for analyst estimate, management-announced target and reported realisation. Do not stack them.
- Add a currency filter and a prominent classification legend.
- Add tooltips for assumption IDs, source IDs, overlap, addressable share, achievable share, ramp and integration-cost assumptions.
- For Kraft Heinz, label the overlap range as an ex-post sensitivity, not a blind pre-deal estimate.
- For HDFC, show funding substitution benefit and CRR/SLR reserve drag as separate positive and negative components; show PSL as unquantified.

## Dashboard 3 — Financial & integration diligence

- Show financial metric, period, reported value, unit, source ID and comparability caveat.
- Add a period selector and deal selector.
- Put integration milestones in a separate lane from financial outcomes. Air India's consolidated vendor contracts and aligned IT systems are milestones, not savings.
- Display integration costs only when disclosed. Retain not-disclosed rows as status records.
- Use a risk heatmap with likelihood × impact and a detail table for leading indicator, mitigation and owner.

## Dashboard 4 — Operational sensitivities

- Blinkit: two independent views — delivery-backend cost/order and cross-platform customer activation. Label all values illustrative, not forecast. Do not sum the two levers without a documented overlap review.
- Air India: plot annual savings hurdle against required addressable vendor spend, with rate-reduction and capture-rate controls. State that the hurdle is analyst-defined and that 4,000+ contracts is not the spend denominator.
- Include a visible caveat panel listing the missing data needed to convert sensitivities into an estimate.

## Dashboard 5 — Market reaction

- Plot CAR by event window only for rows with `status = calculated`.
- Show t-statistic and estimation observations in tooltip.
- Render unavailable daily price series as a separate text/table reference. Never place raw cumulative returns in the CAR axis.
- Include the event date, benchmark, event window and concurrent-news caveat.

## Recommended calculated fields

Create these fields only where the source schema supports them:

- `Scenario Label`: preserve the source scenario value (Low/Base/High).
- `Evidence Class Label`: map the source classification to Announced / Analyst estimate / Reported realisation / Unverified without changing the underlying value.
- `Is Calculated CAR`: `[status] = "calculated" AND NOT ISNULL([car_pct])`.
- `CAR Display`: `IF [Is Calculated CAR] THEN [car_pct] END`.
- `Unknown Status`: map null/blank values to the source's explicit status; never imply zero.

Avoid a universal "synergy total" across deals. If a view aggregates within a deal, enforce a single currency and a single evidence class.

## Publish and QA checklist

- [ ] Connect each CSV as a separate data source or relationship at its natural grain.
- [ ] Verify row counts against the source CSVs.
- [ ] Verify INR and USD never share a numeric axis or aggregate.
- [ ] Verify blanks remain unknown and not zero.
- [ ] Verify no event-study row with unavailable daily data is plotted as CAR.
- [ ] Verify Blinkit sensitivities and Air India hurdles are labelled illustrative.
- [ ] Verify Air India integration milestones are not presented as savings.
- [ ] Test deal, scenario, period and currency filters.
- [ ] Publish to Tableau Public from an authenticated desktop session.
- [ ] Add the public workbook URL to the project README only after publication succeeds.

## Live AI extraction dependency

The filing agent is not run by ordinary CI. Before starting **Manual evidence extraction**, add `OPENAI_API_KEY` as a GitHub Actions repository secret. Never commit the key or paste it into source files. After the workflow completes, inspect retrieval failures and exact-page citations before accepting extracted claims. Precision/recall should be reported only from the actual prediction file and the manually adjudicated gold set; no metric should be inferred from an empty output.
