"""Precision/recall evaluator; never reports zero metrics for an empty run."""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "agent" / "gold_claims.csv"
PRED = ROOT / "agent" / "output" / "extracted_claims.jsonl"
OUT = ROOT / "agent" / "output" / "extraction_metrics.csv"


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", str(text).lower()))


def score(left, right):
    first, second = tokens(left), tokens(right)
    return len(first & second) / max(1, len(first | second))


def match_predictions(gold, predictions, threshold=0.35):
    """Greedy one-to-one matching; a prediction can match at most one gold row."""
    remaining = set(range(len(gold)))
    matches = []
    for prediction in predictions:
        candidates = [
            (score(prediction.get("claim", ""), gold.iloc[index].gold_claim), index)
            for index in remaining
            if prediction.get("deal_id") == gold.iloc[index].deal_id
            and prediction.get("source_id") == gold.iloc[index].source_id
            and prediction.get("claim_type") == gold.iloc[index].claim_type
        ]
        if candidates:
            similarity, index = max(candidates)
            if similarity >= threshold and prediction.get("citation_valid") is True:
                matches.append((prediction, index, similarity))
                remaining.remove(index)
    return matches


def load_predictions():
    if not PRED.exists():
        return []
    predictions = []
    for line in PRED.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parsed = json.loads(line)
        predictions.extend(parsed if isinstance(parsed, list) else [parsed])
    return predictions


def main():
    gold = pd.read_csv(GOLD)
    predictions = load_predictions()
    if not predictions:
        if OUT.exists():
            OUT.unlink()
        update_readme_metrics(len(gold), 0, 0, None, None)
        print("No extracted claims: precision/recall are undefined; no metrics file written.")
        return

    matches = match_predictions(gold, predictions)
    true_positive = len(matches)
    precision = true_positive / len(predictions)
    recall = true_positive / len(gold) if len(gold) else None
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{
        "gold_claims": len(gold),
        "predicted_claims": len(predictions),
        "true_positive": true_positive,
        "precision": precision,
        "recall": recall,
        "matching_rule": "one-to-one matching by deal/source/type, token Jaccard >=0.35, citation_valid=true",
    }]).to_csv(OUT, index=False)
    update_readme_metrics(len(gold), len(predictions), true_positive, precision, recall)
    print(f"Extraction precision={precision:.3f}; recall={recall:.3f}")


def update_readme_metrics(gold_count, prediction_count, true_positive, precision, recall):
    readme = ROOT / "README.md"
    if not readme.exists():
        return
    lines = readme.read_text(encoding="utf-8").splitlines()
    marker = "| Metric | Result |"
    try:
        start = lines.index(marker)
    except ValueError:
        return
    end = start + 1
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    replacement = [
        "| Metric | Result |",
        "|---|---:|",
        f"| Gold claims | {gold_count} |",
        f"| Model-extracted claims | {prediction_count} |",
        f"| True positives | {true_positive} |",
        f"| Precision | {precision:.3f} |" if precision is not None else "| Precision | undefined |",
        f"| Recall | {recall:.3f} |" if recall is not None else "| Recall | undefined |",
    ]
    lines[start:end] = replacement
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
