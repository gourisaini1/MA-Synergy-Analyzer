from agent.filing_reader import chunk_pages, relevant_pages, verify_quote
from agent.schemas import EvidenceClaim
from agent.evaluate_extraction import main as evaluate_extraction


def test_pdf_page_chunking_preserves_page_and_overlap():
    chunks = chunk_pages([(7, "A" * 100 + "B" * 100)], max_chars=120, overlap=20)
    assert len(chunks) == 2
    assert chunks[0].page_number == 7
    assert chunks[0].text[-20:] == chunks[1].text[:20]


def test_keyword_filter_skips_irrelevant_annual_report_pages():
    pages = [(1, "Chairman's welcome and corporate profile"), (2, "The merger synergies are progressing and funding costs declined")]
    assert relevant_pages(pages) == [pages[1]]


def test_exact_quote_citation_check():
    claim = EvidenceClaim(
        deal_id="KRAFT_HEINZ",
        claim_type="management_synergy_target",
        claim="Annual cost savings target",
        source_id="KHC-01",
        source_url="https://example.com/filing.pdf",
        page_or_section="page 1",
        supporting_excerpt="estimated $1.5 billion in annual cost savings",
        classification="management_statement",
        confidence="high",
    )
    assert verify_quote(claim, "The company estimated $1.5 billion in annual cost savings by 2017.")
    assert not verify_quote(claim, "The company estimated $1.4 billion in annual cost savings.")

def test_empty_prediction_file_does_not_emit_zero_metrics(tmp_path, monkeypatch, capsys):
    import agent.evaluate_extraction as evaluator

    gold = tmp_path / "gold_claims.csv"
    gold.write_text(
        "gold_id,deal_id,source_id,claim_type,gold_claim,expected_page_or_section\n"
        "G1,HDFC,HDFC-01,financial_metric,Net interest margin was 3.48%,FY25 annual report\n",
        encoding="utf-8",
    )
    predictions = tmp_path / "extracted_claims.jsonl"
    predictions.write_text("\n", encoding="utf-8")
    metrics = tmp_path / "extraction_metrics.csv"
    metrics.write_text("stale,0\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "| Metric | Result |\n|---|---:|\n| Precision | old |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(evaluator, "ROOT", tmp_path)
    monkeypatch.setattr(evaluator, "GOLD", gold)
    monkeypatch.setattr(evaluator, "PRED", predictions)
    monkeypatch.setattr(evaluator, "OUT", metrics)

    evaluator.main()

    assert not metrics.exists()
    assert "undefined" in capsys.readouterr().out
