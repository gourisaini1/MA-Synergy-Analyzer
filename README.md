# AI-Assisted M&A Synergy & Due Diligence Analyzer

**Conclusion:** HDFC's merger economics are funding-led: cheaper bank deposits can replace HDFC Ltd's market borrowings, offset by CRR/SLR reserve carry and PSL obligations. Kraft Heinz shows the other essential lesson: cost synergies were delivered, but major subsequent asset impairments meant synergy delivery did not guarantee value creation.

![Outside-in synergy scenarios](docs/synergy_estimate.svg)

## Headline cases

| Deal | Independent scenario | Announced / reported evidence | Key conclusion |
|---|---:|---|---|
| **HDFC Ltd–HDFC Bank** | Funding benefit ₹27–411cr; reserve drag ₹22–134cr; small standalone cost overlap ₹4–25cr. Net steady-state scenario approx. **₹8–302cr**, base **₹86cr** before programme costs and unquantified PSL impact. | HDFC Ltd reported 45% of borrowings from market borrowings; deposits were ₹1,52,111cr or 27% of borrowings. | Funding substitution is the main upside. CRR/SLR and PSL are explicit offsets; PSL remains unquantified. |
| **Kraft Heinz** | USD 0.71–2.04bn gross annual run-rate; base USD 1.40bn. Five-year NPV: USD 715m / 2,983m / 5,632m (low/base/high), after spreading programme costs over three years and discounting at 10%. | USD 1.5bn annual run-rate target; management reported >USD 1.7bn cumulative savings by end-2017. | Savings were delivered, but FY18 and FY19 impairment charges totalled USD 17.835bn. Value creation is not the same as cost synergy delivery. |

**Important estimate caveat:** Kraft Heinz's 7%/9%/11% overlap range is an ex-post sensitivity chosen after the target and reported savings were public. It is not an externally benchmarked, blind estimate. HDFC's funding spreads and reserve opportunity-cost ranges are analyst sensitivities, not reported realised savings. All estimates are separate from management claims.

## Core conclusion

"Synergies were delivered, but value was destroyed anyway" is the key Kraft Heinz lesson. The company reported more than USD 1.7bn cumulative savings by end-2017, but recorded USD 15.936bn of goodwill and intangible impairment in FY18 and a further USD 1.899bn in FY19. These write-downs signal severe value erosion; they do not alone prove that the merger caused all of it.

For HDFC, the model does not apply a generic cost-overlap percentage to the merged bank. It uses HDFC Ltd's standalone cost base only for a small operating-cost opportunity and models the larger funding substitution mechanism against CRR/SLR reserve carry. PSL compliance remains unquantified until the incremental shortfall and PSLC cost are known.

## Event-study sanity check

The 4 April 2022 HDFC merger announcement produced close-to-close raw returns of **+10.01% for HDFC Bank** and **+9.29% for HDFC Ltd**, according to SEBI's adjudication order. These are not abnormal returns: the Nifty 50 also rose approximately 2.17% that day, according to Reuters. The multi-deal event-study workflow estimates market-model CAR and t-statistics for the listed acquirer/target securities; Heinz and Blinkit were private at announcement and therefore have no target-share-price series. For each listed security, the market model uses the 120 to 20 trading-session pre-event estimation window and reports CAR over [-1,+1], [-2,+2] and [-5,+5]. Benchmarks are the S&P 500 for Kraft and Nifty 50 for Indian securities. HDFC Ltd's delisted daily series and KRFT's historical daily feed are not available in the current cache, so their sourced raw-price reactions are shown separately and never labelled CAR.

<!-- EVENT_STUDY_TABLE_START -->
| Deal | Security | [-1,+1] CAR (t) | [-2,+2] CAR (t) | [-5,+5] CAR (t) |
|---|---|---:|---:|---:|
| HDFC | HDFC Bank (acquirer) | +7.03% (t=+4.20) | +4.18% (t=+1.93) | +3.09% (t=+0.93) |
| HDFC | HDFC Ltd (target) | n/a; SEBI reports +9.29% close-to-close on announcement day; raw return, not CAR. | n/a | n/a |
| KRAFT_HEINZ | Kraft Foods Group (listed target) | n/a; SEC S-4 reports USD 61.33 on 24 Mar and USD 89.40 on 9 Apr (+45.8% cumulative); not event-window CAR. | n/a | n/a |
| ZOMATO | Zomato (acquirer) | -14.90% (t=-2.23) | -16.78% (t=-1.92) | -18.99% (t=-1.43) |
<!-- EVENT_STUDY_TABLE_END -->

[SEBI adjudication order (HDFC announcement-day reaction)](https://www.sebi.gov.in/web/?file=https%3A%2F%2Fwww.sebi.gov.in%2Fsebi_data%2Fattachdocs%2Fjul-2025%2F1753789804303_1.pdf) · [Reuters market close report](https://www.marketscreener.com/quote/stock/HOUSING-AND-DEVELOPMENT-B-6498420/news/Indian-shares-surge-on-HDFC-twins-merger-plan-39956925/)

## Evidence extraction evaluation

The gold set contains manually curated claims across HDFC and Kraft Heinz (the exact row count is read from agent/gold_claims.csv). The agent is manual-only, filters filing pages by keyword, uses structured JSON-schema outputs and checks every excerpt against the exact cited PDF page. Evaluation uses one-to-one matching within the same deal, source and claim type; a prediction is a true positive only when token Jaccard similarity is at least 0.35 and its source-page excerpt passes exact-quote verification. This is a lightweight benchmark, not a substitute for expert review of claim correctness.

| Metric | Result |
|---|---|
| Gold claims | See current count in agent/gold_claims.csv |
| Model-extracted claims | Not run (API key required) |
| True positives | Not available |
| Precision | Undefined until a credentialed run |
| Recall | Undefined until a credentialed run |

Precision and recall remain undefined until the manual extraction workflow has run with the repository OPENAI_API_KEY secret. Kraft's SEC S-4 also discloses a move from USD 61.33 on 24 March to USD 89.40 on 9 April 2015 (+45.8% cumulative); this is not a market-adjusted event-window return. The evaluator does not write 0.000/0.000 for an empty file.

## Run the model and tests

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python run.py

The unified run validates provenance, builds the directional low/base/high model, attempts SEC Companyfacts retrieval, creates financial diligence tables, refreshes the event study when market data is available, generates the workbook and PowerPoint deck, and runs pytest. Event-study CARs are only emitted when the exact event-session return and every observation in the requested window are available; missing or partial windows are marked unavailable rather than shifted or silently shortened. If a provider is unavailable and no cache exists, the event study skips safely so the remaining build and tests can run.

## Manual refresh workflows

- **Manual evidence extraction:** add OPENAI_API_KEY in GitHub repository secrets, then run Actions → Manual evidence extraction. It commits page chunks, verified claims and precision/recall output. This credentialed run has not been performed as part of this code change; no fabricated metrics are included.
- **Refresh multi-deal event study:** run Actions → Refresh multi-deal event study. It downloads and commits data/market_prices.csv plus dashboard/event_study_results.csv. The workflow includes Kraft Foods Group/KRFT, HDFC Bank/HDFC Ltd and Zomato; Heinz and Blinkit are private targets.

## Outputs

- output/MA_Synergy_Model.xlsx: editable scenario inputs, directional calculations, five-year NPV, announced-vs-estimated-vs-realised bridge, evidence and financial diligence.
- output/MA_Executive_Deck.pptx: answer-led deck with native PowerPoint scenario, Blinkit EBITDA and HDFC cost-to-income charts, plus Air India/Microsoft appendix slides.
- dashboard/tableau_synergy_data.csv: scenario estimates, signed negative synergies, confidence and assumption provenance.\n- dashboard/deal_comparability.csv: four-deal evidence bridge with explicit partial/unquantified statuses.\n- research/integration_cost_tracker.csv: workstream-level integration cost register; KHC reported programme expenses are separated from undisclosed costs in the other deals; the 2015–17 series totals $2.055bn pre-tax.
- dashboard/financial_due_diligence.csv: financial metrics, before/after changes and caveats.
- dashboard/event_study_results.csv: event-window CAR and t-statistics after manual market-data refresh.
- agent/output/: committed only after the manual extraction workflow has produced real output.

## Tableau and Alteryx

The repository contains Tableau-ready data sources and a dashboard specification in dashboard/tableau_spec.md. A Tableau Public workbook has **not** been published from this environment; publishing requires an authenticated Tableau Public session. The Alteryx source-cleaning workflow is in alteryx/source_register_cleaning.yxmd; it has not been executed or screenshot-verified in Alteryx Designer.

## Four-deal core coverage and comparability

The project now explicitly treats **HDFC–HDFC Bank, Air India–Vistara, Zomato–Blinkit and Kraft Heinz** as its four core cases. Microsoft–LinkedIn remains an additional reference case, not a substitute for one of the four.

`dashboard/deal_comparability.csv` is generated by `pipeline.build_deal_comparability` and included in the Excel workbook. It puts the four deals on one evidence bridge: independent low/base/high scenario (where supportable), management-announced target, management-reported realisation, measurement basis, evidence quality and the missing inputs needed to close diligence gaps. Missing target and realisation values remain blank—not zero.

| Core deal | Current model status | What can be defended today | What is still required |
|---|---|---|---|
| HDFC–HDFC Bank | Partial estimate | Funding-substitution scenario net of modelled CRR/SLR drag and small cost overlap | PSL shortfall/PSLC economics and matched funding data; the current scenario is not a realised result |
| Air India–Vistara | Not quantified | Merger integration milestones: 4,000+ contracts consolidated and 140+ IT systems aligned | Vendor category spend/rate cards, fleet and route unit economics, integration costs and service-quality counterfactuals |
| Zomato–Blinkit | Not quantified | Blinkit segment financial trajectory and management's stated cross-leverage / delivery-backend hypotheses | Matched-city delivery costs, cross-order cohorts, incremental contribution after incentives and a standalone counterfactual |
| Kraft Heinz | Modelled, ex-post calibrated | $1.5bn annual run-rate target and >$1.7bn cumulative savings reported by end-2017 | Pre-close category-level cost pool and recurring run-rate bridge; current overlap range is not a blind forecast |

The four deals are therefore comparable in **evidence structure**, not yet in the precision of their financial estimates. Air India integration milestones are not savings; Blinkit segment growth is not acquisition synergy; Kraft Heinz cumulative savings are not directly comparable to an annual run-rate target.

## Additional deal case

Microsoft–LinkedIn remains a financial trajectory reference case; LinkedIn growth is not proof of cross-sell attribution. It is retained outside the four-deal core.

## Evidence and caveats

- data/source_register.csv: source-of-truth register.
- research/evidence_ledger.csv: hand-built evidence claims and attribution caveats.
- agent/gold_claims.csv: manually curated evaluation set (use the CSV row count as the source of truth).
- research/financial_due_diligence.csv: HDFC funding mix, standalone cost base, regulatory requirements, Kraft Heinz impairments and segment financial metrics.
- research/integration_risk_register.csv: integration risks and mitigations.
- model/assumptions_register.csv and model/synergy_inputs.csv: analyst assumptions separated from management disclosures.

## Project structure

- agent/: structured extraction, keyword filtering, exact-page quote checks and gold-set evaluation.
- pipeline/: source validation, financial analysis, SEC XBRL, event study, synergy model and artifact generation.
- research/: deal briefs, evidence ledger, financial diligence, announced targets and risk register.
- model/: directional low/base/high inputs and five-year NPV assumptions.
- dashboard/: Tableau-ready outputs and specifications.
- alteryx/: source-register cleaning workflow.
- tests/: model, agent and event-study tests.
