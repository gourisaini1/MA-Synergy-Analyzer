"""Manual, keyword-filtered PDF/HTML evidence extraction over the source register."""
import os
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
import requests

from .extract_claims import extract
from .filing_reader import chunk_pages, extract_pdf_pages, relevant_pages, verify_quote

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "data" / "source_register.csv"
OUT = ROOT / "agent" / "output"
USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "MA-Synergy-Analyzer research contact@users.noreply.github.com",
)
MAX_CHUNKS_PER_SOURCE = int(os.getenv("AGENT_MAX_CHUNKS_PER_SOURCE", "20"))


class VisibleTextParser(HTMLParser):
    """Small standard-library HTML text extractor that ignores scripts/styles."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data):
        if not self.hidden_depth and data.strip():
            self.parts.append(data.strip())

    def text(self):
        return " ".join(self.parts)


def extract_source_pages(response, source_id):
    if response.content.startswith(b"%PDF"):
        pdf_path = OUT / f"{source_id}.pdf"
        pdf_path.write_bytes(response.content)
        return extract_pdf_pages(str(pdf_path)), "PDF page"
    parser = VisibleTextParser()
    parser.feed(response.text)
    text = parser.text()
    if not text:
        return [], "HTML page"
    return [(1, text)], "HTML page"


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "Set OPENAI_API_KEY to run the manual LLM extraction. "
            "The agent is intentionally not run in ordinary CI."
        )
    OUT.mkdir(parents=True, exist_ok=True)
    register = pd.read_csv(REGISTER)
    claims = []
    chunks_log = []
    failures = []

    for source in register.itertuples(index=False):
        try:
            response = requests.get(
                source.url,
                headers={"User-Agent": USER_AGENT},
                timeout=30,
            )
            response.raise_for_status()
            pages, page_label = extract_source_pages(response, source.source_id)
        except Exception as error:
            failures.append({
                "source_id": source.source_id,
                "url": source.url,
                "error": str(error),
            })
            continue

        selected_pages = relevant_pages(pages)
        page_text = dict(pages)
        chunks = chunk_pages(selected_pages)[:MAX_CHUNKS_PER_SOURCE]
        for chunk in chunks:
            chunks_log.append({
                "source_id": source.source_id,
                "page": chunk.page_number,
                "chunk": chunk.chunk_number,
                "characters": len(chunk.text),
            })
            try:
                extracted = extract(
                    source.deal_id,
                    source.source_id,
                    source.url,
                    f"{page_label} {chunk.page_number}",
                    chunk.text,
                )
                for claim in extracted:
                    item = claim.model_dump()
                    item["citation_valid"] = verify_quote(
                        claim, page_text.get(chunk.page_number, "")
                    )
                    if item["citation_valid"]:
                        claims.append(item)
            except Exception as error:
                failures.append({
                    "source_id": source.source_id,
                    "url": source.url,
                    "error": f"{page_label} {chunk.page_number}: {error}",
                })

    pd.DataFrame(chunks_log).to_csv(OUT / "page_chunks.csv", index=False)
    pd.DataFrame(failures).to_csv(OUT / "retrieval_failures.csv", index=False)
    pd.DataFrame(claims).to_json(
        OUT / "extracted_claims.jsonl", orient="records", lines=True
    )
    print(
        f"Registered sources={len(register)}; keyword-filtered chunks={len(chunks_log)}; "
        f"citation-verified claims={len(claims)}; failures={len(failures)}."
    )


if __name__ == "__main__":
    main()
