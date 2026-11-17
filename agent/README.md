# Evidence extraction agent

The agent is manual-only to avoid calling an LLM on every push. It downloads registered PDF and HTML sources, filters pages by financial/M&A keywords, chunks only relevant content, extracts structured claims with the OpenAI Responses API and validates every verbatim excerpt against the exact cited PDF page or HTML source text.

Run it from the GitHub Actions tab using **Manual evidence extraction** after adding the OPENAI_API_KEY repository secret. It is intentionally not part of python run.py or ordinary CI.

The manually curated gold set contains 61 claims across HDFC, Kraft Heinz, Air India and Zomato/Blinkit. The new Air India claims cover vendor, system, workforce, booking and loyalty integration milestones; the Blinkit claims cover segment financials, order volumes, customers and store footprint. Precision/recall are written only when predictions exist. Empty output means metrics are undefined; the evaluator deletes any stale metrics file and updates the README to say undefined rather than reporting zero.

The agent output is committed by the manual workflow. Review claims before incorporating them into the evidence ledger. The gold set is a small manually adjudicated evaluation set, not a representative statistical sample of all filing statements.
