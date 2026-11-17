# AI-Assisted M&A Synergy & Due Diligence Analyzer

An evidence-led model of merger synergies, integration costs and post-close financial outcomes, with HDFC Bank–HDFC Ltd and Kraft Heinz as the two quantitative cases.

![Outside-in synergy scenarios](docs/synergy_estimate.svg)

- **HDFC:** the base-case five-year after-cost NPV is approximately **+₹121cr**; the adverse stress case is approximately **–₹560cr**, driven by high reserve drag and operating-cost programme costs. These are analyst sensitivities, not realised savings.
- **Kraft Heinz:** management reported more than **USD 1.7bn cumulative savings** by end-2017 against a USD 1.5bn annual run-rate target, but later impairment charges show that synergy delivery is not the same as value creation.
- **HDFC actuals:** post-merger cost of funds remained around **4.8–4.9%** through FY24/Q1 FY25, CASA fell from **42%** in Jun-23 to **36%** in Jun-24, and the credit-deposit ratio declined from about **110%** at merger to **96%** by Mar-25. These outcomes are consistent with balance-sheet repositioning, but do not isolate the merger's causal funding benefit.

## How to run

```bash
pip install -r requirements.txt
python run.py
pytest -q
```

## Headline cases

| Deal / lever | Low | Base | High | Interpretation |
|---|---:|---:|---:|---|
| HDFC funding substitution — 5-year NPV after costs (₹cr) | +80 | +475 | +1,482 | Funding-spread and migration sensitivities |
| HDFC CRR/SLR reserve drag — 5-year NPV (₹cr) | –67 | –228 | –483 | Reserve opportunity-cost sensitivity |
| HDFC legacy operating-cost lever — 5-year NPV after programme costs (₹cr) | –72 | –127 | –157 | Negative in every scenario because programme costs exceed savings |
| Kraft Heinz gross annual run-rate (USD bn) | 0.71 | 1.40 | 2.04 | Ex-post sensitivity; not an out-of-sample estimate |

**HDFC combined base case:** approximately **+₹121cr** five-year after-cost NPV across the three quantified levers.  
**HDFC adverse stress:** approximately **–₹560cr** five-year after-cost NPV, pairing low funding benefit, high reserve drag and high operating-cost programme costs. This is not the earlier rough –₹103cr estimate: that figure does not reconcile to the current five-year cash-flow model and should not be repeated without a separately defined calculation basis. PSL remains unquantified and is excluded from both totals.

**Important estimate caveat:** HDFC's funding spreads and reserve opportunity-cost ranges are analyst sensitivities, not reported realised savings. Kraft Heinz's 7%/9%/11% overlap range is an ex-post sensitivity chosen after the target and reported savings were public; it is not an externally benchmarked blind estimate.

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

The gold set contains 46 manually curated claims across HDFC and Kraft Heinz. The agent is manual-only, filters filing pages by keyword, uses structured JSON-schema outputs and checks every excerpt against the exact cited PDF page.

| Metric | Result |
|---|---:|
| Gold claims | 46 |
| Model-extracted claims | 0 |
| True positives | 0 |
| Precision | undefined |
| Recall | undefined |

Manual extraction workflow run #2 completed, but the OpenAI API returned HTTP 429 because the account had no remaining credits. No claims were extracted, so precision and recall are undefined. Add API credits and rerun before treating the agent as operational. Kraft's SEC S-4 also discloses a move from USD 61.33 on 24 March to USD 89.40 on 9 April 2015 (+45.8% cumulative); this is not a market-adjusted event-window return.

## Run the model and tests

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python run.py

The unified run validates sources and assumptions, builds the directional low/base/high model, downloads SEC Companyfacts, creates financial diligence tables, refreshes the event study when market data is available, generates the workbook and PowerPoint deck, and runs pytest. If the market-data provider is unavailable and no cache exists, the event study skips safely so pytest still runs.

## Manual refresh workflows

- **Manual evidence extraction:** add OPENAI_API_KEY in GitHub repository secrets, then run Actions → Manual evidence extraction. It commits page chunks, verified claims and precision/recall output.
- **Refresh multi-deal event study:** run Actions → Refresh multi-deal event study. It downloads and commits data/market_prices.csv plus dashboard/event_study_results.csv. The workflow includes Kraft Foods Group/KRFT, HDFC Bank/HDFC Ltd and Zomato; Heinz and Blinkit are private targets.

## Outputs

- output/MA_Synergy_Model.xlsx: editable scenario inputs, directional calculations, five-year NPV, announced-vs-estimated-vs-realised bridge, evidence and financial diligence.
- output/MA_Executive_Deck.pptx: answer-led deck with native PowerPoint scenario, Blinkit EBITDA and HDFC cost-to-income charts, plus Air India/Microsoft appendix slides.
- dashboard/tableau_synergy_data.csv: scenario estimates, signed negative synergies, confidence and assumption provenance.
- dashboard/financial_due_diligence.csv: financial metrics, before/after changes and caveats.
- dashboard/event_study_results.csv: event-window CAR and t-statistics after manual market-data refresh.
- agent/output/: committed only after the manual extraction workflow has produced real output.

## Tableau and Alteryx

The repository contains Tableau-ready data sources and a dashboard specification in dashboard/tableau_spec.md. A Tableau Public workbook has **not** been published from this environment; publishing requires an authenticated Tableau Public session. The Alteryx source-cleaning workflow is in alteryx/source_register_cleaning.yxmd; it has not been executed or screenshot-verified in Alteryx Designer.

## Secondary deal cases

Air India–Vistara remains a qualitative PMI appendix because public data does not support a harmonised financial synergy back-test. Microsoft–LinkedIn remains a financial trajectory appendix; LinkedIn growth is not proof of cross-sell attribution. Zomato–Blinkit provides Blinkit's standalone financial trajectory and the acquisition event-study acquirer series; Blinkit itself was privately held.

## Evidence and caveats

- data/source_register.csv: source-of-truth register.
- research/evidence_ledger.csv: hand-built evidence claims and attribution caveats.
- agent/gold_claims.csv: 46-claim evaluation set.
- research/financial_due_diligence.csv: HDFC funding mix, standalone cost base, regulatory requirements, Kraft Heinz impairments and segment financial metrics.
- research/integration_risk_register.csv: integration risks and mitigations.
- model/assumptions_register.csv and model/synergy_inputs.csv: analyst assumptions separated from management disclosures.

## Limitations & next steps

- HDFC post-merger actuals are observational. Balance-sheet mix, deposit pricing, interest-rate cycles, growth calibration and the merger all changed; the available disclosures do not isolate a causal synergy effect.
- The HDFC PSL shortfall and PSLC purchase cost remain unquantified.
- The HDFC funding and CRR/SLR calculations use simplified migration and spread sensitivities; a liability-level NDTL, reserve and maturity schedule is required for a bank-grade estimate.
- Kraft Heinz's overlap range is ex-post calibrated. A blind estimate requires pre-2015 comparable food/consumer merger benchmarks and pre-close category cost bases.
- Event-study CARs are single-event market-model estimates, not causal proof; data-provider adjustment conventions are selected consistently within each ticker.
- Air India–Vistara, Zomato–Blinkit and Microsoft–LinkedIn are qualitative appendix cases, not fully modelled synergy valuations.
- Tableau Public is not published and the Alteryx workflow has not been executed in Designer; the repository only includes Tableau-ready data/specification and the Alteryx workflow file.
- The evidence-extraction agent has run, but the current run produced no claims because the OpenAI API account had no remaining credits. Precision and recall are therefore undefined.

## Project structure

- agent/: structured extraction, keyword filtering, exact-page quote checks and gold-set evaluation.
- pipeline/: source validation, financial analysis, SEC XBRL, event study, synergy model and artifact generation.
- research/: deal briefs, evidence ledger, financial diligence, announced targets and risk register.
- model/: directional low/base/high inputs and five-year NPV assumptions.
- dashboard/: Tableau-ready outputs and specifications.
- alteryx/: source-register cleaning workflow.
- tests/: model, agent and event-study tests.
