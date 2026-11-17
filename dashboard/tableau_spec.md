# Tableau Public dashboard specification

## Executive overview
Lead with a four-deal coverage and evidence-status scorecard using deal_comparability.csv. The four core cases are HDFC–HDFC Bank, Air India–Vistara, Zomato–Blinkit and Kraft Heinz; Microsoft–LinkedIn is an additional reference case. Keep announced, estimated, realised and unverified classifications distinct. Never aggregate values across currencies. Show blank/unknown fields as not disclosed or not quantified, never as zero.

## Air India–Vistara financial context\nUse financial_due_diligence.csv and deal_evidence_backtest.csv:\n- FY24 Air India revenue ₹51,364.89cr and Vistara revenue ₹15,191.27cr.\n- FY25 merged Air India revenue ₹76,754.10cr and loss after tax ₹10,858.82cr.\n- Show 4,000+ vendor contracts consolidated and 140+ IT systems aligned as integration milestones, not financial savings.\n- Explicitly flag FY24 standalone and FY25 merged periods as non-like-for-like; no attributable financial synergy target or realised savings is identified.\n\n## Zomato–Blinkit operating-cost context\nUse financial_due_diligence.csv and deal_evidence_backtest.csv:\n- FY24 consolidated delivery and related charges ₹3,915cr, advertising/sales promotion ₹1,432cr, IT support ₹485cr, outsourced support ₹330cr and other expenses ₹1,179cr.\n- These are consolidated food-delivery plus quick-commerce expense lines; do not present them as Blinkit-only cost pools.\n- Show Blinkit adjusted EBITDA and NOV trajectory separately from integration synergies.\n- Keep numeric synergy unquantified until cohort, city and segment-level cost evidence is available.\n\n## HDFC funding bridge
Use tableau_synergy_data.csv:
- Funding substitution benefit from market borrowings refinanced through bank deposits.
- CRR/SLR reserve opportunity-cost drag as a negative synergy.
- Small standalone HDFC Ltd non-finance cost overlap.
- PSL compliance downside marked unverified, not zero.
Display low/base/high ranges, assumption confidence and source IDs. Explain that reserve drag is a sensitivity and Day-0 liquidity offsets need reconciliation.

## Kraft Heinz scenario and value creation
Show USD 1.5bn announced annual run-rate target, independent USD 0.71–2.04bn gross run-rate sensitivity (base USD 1.40bn), and >USD 1.7bn cumulative realised savings separately. Clearly label 7%/9%/11% overlap as ex-post sensitivity, not a cited benchmark. Include 3-year programme-cost allocation and five-year NPV. Add FY18/FY19 goodwill and intangible impairment context.

## Financial diligence
Use financial_due_diligence.csv:
- HDFC Bank cost-to-income and NIM, with FY23 pre-merger bank and FY24/FY25 post-merger comparability caveat.
- HDFC Ltd funding mix and standalone operating cost proxy.
- Blinkit adjusted EBITDA FY23–FY26.
- Kraft Heinz FY18/FY19 impairment and net-sales trend.
Display reported value, prior-period change, source and comparability caveat. Never infer causal synergy from a pre/post change alone.

## Event study
Use event_study_results.csv and market_prices.csv:
- HDFC Bank acquirer and HDFC Ltd target when daily history is available.
- Kraft Foods Group listed target (Heinz was privately held acquirer).
- Zomato acquirer (Blinkit was privately held target).
- Benchmarks: Nifty 50 for Indian listings; S&P 500 for Kraft.
- Market model estimation window: -120 to -20 trading sessions; event windows: [-1,+1], [-2,+2], [-5,+5].
Show CAR, t-statistic, estimation observations and data availability status. Where daily data is unavailable, show the sourced raw price reference separately and never label it CAR.

## Evidence back-test and risk heatmap
Use deal_evidence_backtest.csv and research/integration_risk_register.csv. Include classification, source ID, synergy relevance, attribution caveat, likelihood, impact, leading indicator, mitigation and owner.

## Tableau Public
The repository contains Tableau-ready datasets and this specification. A public workbook has not been published from this environment because an authenticated Tableau Public session is not available.
