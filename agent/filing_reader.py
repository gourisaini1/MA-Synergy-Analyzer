"""PDF page extraction, keyword filtering, chunking and quote verification."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from pypdf import PdfReader

from .schemas import EvidenceClaim

RELEVANCE = re.compile(
    r"synerg|saving|integration|merger|acquisition|funding|borrowings|"
    r"deposit|cost.to.income|net interest margin|nim|crr|slr|priority sector|"
    r"goodwill|impairment|restructur|procurement|cross.sell|margin|"
    r"operating expense|ebitda|cost of product|annual cost",
    re.IGNORECASE,
)


@dataclass
class PageChunk:
    page_number: int
    chunk_number: int
    text: str


def extract_pdf_pages(path: str) -> list[tuple[int, str]]:
    reader = PdfReader(path)
    return [
        (page_number, page.extract_text() or "")
        for page_number, page in enumerate(reader.pages, start=1)
    ]


def relevant_pages(pages: Iterable[tuple[int, str]]) -> list[tuple[int, str]]:
    return [
        (page_number, text)
        for page_number, text in pages
        if text.strip() and RELEVANCE.search(text)
    ]


def chunk_pages(
    pages: Iterable[tuple[int, str]], max_chars: int = 3500, overlap: int = 350
) -> list[PageChunk]:
    chunks = []
    for page_number, text in pages:
        text = re.sub(r"\s+", " ", text).strip()
        start = 0
        chunk_number = 1
        while start < len(text):
            end = min(start + max_chars, len(text))
            chunks.append(PageChunk(page_number, chunk_number, text[start:end]))
            if end == len(text):
                break
            start = max(0, end - overlap)
            chunk_number += 1
    return chunks


def verify_quote(claim: EvidenceClaim, page_text: str) -> bool:
    quote = re.sub(r"\s+", " ", claim.supporting_excerpt).strip()
    page = re.sub(r"\s+", " ", page_text).strip()
    return bool(quote) and quote in page


def validate_claim(payload: dict) -> EvidenceClaim:
    claim = EvidenceClaim.model_validate(payload)
    if not claim.supporting_excerpt.strip():
        raise ValueError("Evidence claim requires an exact supporting excerpt.")
    return claim


def build_extraction_prompt(deal_id, source_id, source_url, page_text, page_number):
    return (
        "Extract only explicitly stated facts, management synergy targets, "
        "integration milestones, risks or financial metrics from this page. "
        "Return the required structured claims array. Each supporting_excerpt "
        "must be an exact contiguous verbatim quote from this page. Do not infer "
        "synergies from milestones, segment growth or management aspirations. "
        "Return an empty claims array if the page has no material claim. "
        f"Deal={deal_id}; source_id={source_id}; URL={source_url}; page={page_number}.\n"
        f"PAGE TEXT:\n{page_text}"
    )
