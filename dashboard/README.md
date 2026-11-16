# Tableau dashboard build guide

Run python run.py to generate all dashboard datasets.

## Data sources
- tableau_synergy_data.csv: directional low/base/high estimates with assumption provenance, confidence and status.
- deal_evidence_backtest.csv: announced target and observed management KPIs, integration milestones and acquired-business financial metrics.
- financial_due_diligence.csv: pre/post financial observations and changes.
- event_study_results.csv: market-model CAR and t-statistics for HDFC Bank, Zomato and any other listed securities with daily price coverage.

## Recommended views
1. Executive bridge: management-announced target vs independent estimate vs reported realised savings.
2. Waterfall: cost pool → overlap → addressable → achievable → gross annual run-rate.
3. HDFC funding bridge: lower-cost deposit substitution benefit less CRR/SLR reserve carry and small legacy operating-cost overlap; show PSL as unquantified.
4. Kraft Heinz scenario sensitivity: low/base/high range, multi-year programme cost, five-year NPV, announced target and cumulative realised savings.
5. Financial diligence: HDFC cost-to-income/NIM, Blinkit adjusted EBITDA and Kraft Heinz impairments with comparability caveats.
6. Event study: CAR and t-statistics across [-1,+1], [-2,+2] and [-5,+5] trading sessions; S&P 500 benchmark for Kraft, Nifty 50 for Indian listings.
7. Evidence back-test and integration risk heatmap.

Keep currencies separate. Never plot nulls as zero or treat acquired-business growth and integration milestones as causal synergy. HDFC Ltd's delisted daily series and Kraft Foods Group's KRFT daily series are not available in the current feed; show sourced raw price reactions separately rather than inventing CAR. Tableau Public publication requires an authenticated Tableau session; repository provides Tableau-ready datasets and specifications.
