# Credentialed filing-agent run checklist

The live extractor calls the OpenAI API. The repository owner must supply the credential through GitHub Actions secrets; it must never be embedded in code, committed files, workflow logs or chat.

## Before the run

- [ ] In GitHub repository Settings → Secrets and variables → Actions, create or update the repository secret named `OPENAI_API_KEY`.
- [ ] Confirm the manual evidence-extraction workflow is present on the branch being tested.
- [ ] Confirm the source register URLs are reachable and the source IDs map to the correct deal IDs.
- [ ] Review `agent/gold_claims.csv`; gold claims should be manually adjudicated and should not be edited merely to improve the model score.
- [ ] Start with the default chunk cap. Increase `AGENT_MAX_CHUNKS_PER_SOURCE` only after checking API cost and run time.

## Run

1. Open the repository's Actions tab.
2. Select **Manual evidence extraction**.
3. Select the intended branch and run the workflow.
4. Do not expose the secret in workflow inputs or logs.

## Review generated files

| File | Review |
|---|---|
| `agent/output/page_chunks.csv` | Coverage by source/page and whether keyword filtering missed relevant pages |
| `agent/output/retrieval_failures.csv` | HTTP, PDF parsing and extraction errors; distinguish unavailable sources from model failures |
| `agent/output/extracted_claims.jsonl` | Claim type, classification, confidence, exact excerpt, source ID, page/section and citation-valid flag |
| `agent/output/extraction_metrics.csv` | One-to-one precision/recall against the 61-claim gold set, if the evaluator ran with predictions |

## Acceptance gates

- Reject any claim with a missing source ID, unsupported deal ID, empty excerpt or failed exact-quote verification.
- Inspect claims that describe integration milestones: they must not be relabelled as financial savings.
- Inspect all management synergy targets and realised savings against the original source and stated measurement basis.
- Treat the benchmark as a small manually curated test set, not a representative estimate of performance on all filings.
- Do not report precision/recall if no predictions were produced. Do not substitute zero for undefined metrics.
- Record model name, run date, source coverage, chunk cap, failures and gold-set version alongside any published metrics.

## Current execution status

No live model run is claimed by this repository documentation. A credentialed run must be started from GitHub Actions after the repository secret is configured. The assistant cannot read or retrieve the repository's secret value.
