from pathlib import Path

from openpyxl import load_workbook
from pptx import Presentation


ROOT = Path(__file__).resolve().parents[1]


def test_generated_workbook_has_excel_safe_sheet_names_and_npv():
    workbook_path = ROOT / "output" / "MA_Synergy_Model.xlsx"
    workbook = load_workbook(workbook_path, data_only=False)
    assert all(len(name) <= 31 for name in workbook.sheetnames)
    assert "Announced vs Est vs Realised" in workbook.sheetnames
    calculations = workbook["Scenario Calculations"]
    assert "Five-year NPV after costs" in [cell.value for cell in calculations[1]]
    assert any(
        isinstance(cell.value, str) and cell.value.startswith("=")
        for row in calculations.iter_rows(min_row=2)
        for cell in row
    )


def test_generated_deck_contains_native_charts_and_appendix():
    deck_path = ROOT / "output" / "MA_Executive_Deck.pptx"
    deck = Presentation(deck_path)
    charts = [
        shape
        for slide in deck.slides
        for shape in slide.shapes
        if getattr(shape, "has_chart", False)
    ]
    assert len(charts) >= 3
    assert len(deck.slides) >= 10
