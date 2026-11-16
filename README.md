# AI-Assisted M&A Synergy & Due Diligence Analyzer

> Initial research and engineering foundation. Deal-specific synergy values remain blank until evidence and assumptions have been reviewed.

## Deal universe
1. HDFC Ltd–HDFC Bank (India; effective 1 July 2023)
2. Air India–Vistara (India; completed 12 November 2024)
3. Zomato–Blinkit (India; completed August 2022)
4. Microsoft–LinkedIn (US; completed 8 December 2016)

## Deliverables
- Public-source register: annual reports, exchange filings, SEC EDGAR, investor presentations and earnings-call transcripts.
- Python extraction, cleaning, standardisation and validation pipeline designed to mirror an Alteryx flow.
- Transparent synergy model for SG&A, procurement, headcount, other cost levers and cross-sell revenue, with base/bull/bear cases.
- Evidence-first AI research agent with page/section citations.
- Tableau dashboard specification and five-slide consulting-style deck template.
- Back-test separating independent estimates, management targets and reported outcomes.
- Add-ons: outside-in commercial diligence for a D2C brand and a synthetic PMI cost tracker.

## Methodology
Keep three values distinct: management-announced synergy, independent estimate and subsequently reported realisation. Integration milestones are not proof of financial savings. Every quantitative claim needs a source or assumption ID; unknowns remain null, not zero. Do not mix run-rate, cumulative savings, one-off costs, pre-tax and post-tax figures. Financial institutions require sector-specific adjustments.

The model captures baseline, overlap, addressability, achievability, ramp, gross run-rate, one-off integration costs and net first-year impact. The AI agent extracts claims; it does not invent or calculate synergies.

## Setup
```bash
python -m venv .venv
pip install -r requirements.txt
python pipeline/build_source_register.py
python pipeline/validate_inputs.py
pytest -q
```

## SEC EDGAR
Microsoft submissions and XBRL facts are available without an API key. See https://www.sec.gov/search-filings/edgar-application-programming-interfaces. Use a descriptive User-Agent and follow SEC fair-access guidance.

## Limitations
Public disclosures rarely provide granular cost bases. Management targets may not be comparable. Operating milestones do not prove savings. Comparisons require accounting, fiscal-year, business-mix and currency adjustments. These are outside-in estimates, not investment advice or a fairness opinion.

## Status
- [x] Four-deal universe and source register foundation
- [x] Python pipeline scaffold
- [x] Evidence extraction scaffold
- [x] Tableau and add-on specifications
- [ ] Downloaded source corpus and page-level evidence
- [ ] Deal-level estimates and back-test
- [ ] Published dashboard and final deck
