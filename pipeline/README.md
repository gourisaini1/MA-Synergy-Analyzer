# Pipeline architecture

Run the complete workflow with one command:

```bash
python run.py
```

The pipeline validates the source register and assumption provenance, calculates low/base/high synergy scenarios, downloads and parses Microsoft SEC Companyfacts, builds financial diligence tables, generates the announced-vs-estimated-vs-realised back-test, creates the Excel workbook and PowerPoint deck, ingests registered PDFs through the evidence agent, runs exact-page citation checks, evaluates model extraction when an API key is present, performs a market-model event study, and runs automated tests.

## Alteryx counterpart
`alteryx/source_register_cleaning.yxmd` provides the source-register cleaning workflow: Input Data → Data Cleansing → Unique source ID → Output Data. It should be opened and validated in Alteryx Designer before claiming production execution.

## External credentials
- `OPENAI_API_KEY`: enables model-based structured claim extraction. Without it, PDF ingestion and page chunking run offline; no model precision/recall is reported.
- `SEC_USER_AGENT`: optional contact-bearing User-Agent for SEC data retrieval.
- Event study downloads daily MSFT and SPY adjusted prices through yfinance.
