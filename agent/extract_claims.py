"""OpenAI structured extraction; every output is schema-validated."""
import os

from openai import OpenAI

from .filing_reader import build_extraction_prompt, validate_claim
from .schemas import ClaimsEnvelope


def extract(deal_id, source_id, source_url, page_or_section, text):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = build_extraction_prompt(
        deal_id, source_id, source_url, text, page_or_section
    )
    response = client.responses.parse(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=prompt,
        text_format=ClaimsEnvelope,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise ValueError("Structured extraction returned no parsed claim envelope.")

    claims = []
    for item in parsed.claims:
        payload = item.model_dump()
        payload.update({
            "deal_id": deal_id,
            "source_id": source_id,
            "source_url": source_url,
            "page_or_section": str(page_or_section),
        })
        claims.append(validate_claim(payload))
    return claims
