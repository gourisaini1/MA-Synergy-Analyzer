"""Generate editable scenario workbook and answer-led executive deck."""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from .run_model import HDFC_MATCHED_LEVERS, HDFC_STRESS_CASES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
MODEL = ROOT / "model"
RESEARCH = ROOT / "research"


def style_header(sheet):
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="17365D")
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.row_dimensions[1].height = 32


def build_workbook():
    workbook = Workbook()
    readme = workbook.active
    readme.title = "Read Me"
    notes = [
        ["AI-Assisted M&A Synergy Analyzer"],
        ["Headline cases: HDFC funding economics and Kraft Heinz synergy/value back-test; other deals are appendix cases."],
        ["Four classifications remain separate: announced, estimated, realised and unverified."],
        ["Analyst estimates are scenario assumptions, not management guidance or realised synergy."],
        ["Cost run-rate = baseline cost × overlap × addressable × achievable."],
        ["First-year net allocates total multi-year integration cost over programme years; five-year NPV discounts ramped cash flows."],
        ["Kraft Heinz overlap range is an ex-post sensitivity, not an external benchmark or blind prediction."],
        ["Blank values mean unverified; they are never silently converted to zero."],
    ]
    for row in notes:
        readme.append(row)

    inputs = pd.read_csv(MODEL / "synergy_inputs.csv")
    sheet = workbook.create_sheet("Scenario Inputs")
    sheet.append(list(inputs.columns))
    for row in inputs.itertuples(index=False, name=None):
        sheet.append(list(row))
    style_header(sheet)

    calc = workbook.create_sheet("Scenario Calculations")
    calc.append([
        "Deal", "Lever", "Scenario", "Currency", "Gross run-rate",
        "Net first-year", "Five-year NPV after costs", "Classification", "Confidence", "Assumption IDs",
    ])
    columns = {name: get_column_letter(index + 1) for index, name in enumerate(inputs.columns)}
    for index, row in enumerate(inputs.itertuples(index=False), start=2):
        scenario_specs = [(name, None) for name in ("low", "base", "high")]
        if row.deal_id == "HDFC" and row.stress_scenario in ("low", "high"):
            scenario_specs.extend(
                (stress_name, case_inputs)
                for stress_name, case_inputs in HDFC_STRESS_CASES.items()
            )
        for scenario, stress_values in scenario_specs:
            target_row = calc.max_row + 1
            source_scenario = row.stress_scenario if stress_values else scenario
            fields = [
                f"'Scenario Inputs'!{columns[name]}{index}"
                for name in (
                    "baseline_amount", f"overlap_{source_scenario}",
                    f"addressable_{source_scenario}", f"achievable_{source_scenario}",
                    f"ramp_{source_scenario}", f"one_off_cost_{source_scenario}",
                    f"contribution_margin_{source_scenario}", "direction",
                    "integration_program_years", "discount_rate",
                )
            ]
            if stress_values and row.lever in HDFC_MATCHED_LEVERS:
                fields[1] = str(stress_values["matched_share"])
                fields[4] = str(stress_values["ramp"])
            gross = (
                "*".join((fields[0], fields[1], fields[2], fields[3], fields[6]))
                + f'*IF({fields[7]}="negative",-1,1)'
            )
            if row.deal_id == "HDFC" and row.lever == "Priority-sector lending compliance cost":
                npv_formula = "=" + "+".join(
                    f'({fields[0]}*{fields[1]}*{phase}*{fields[3]}*{fields[6]}*'
                    f'IF({fields[7]}="negative",-1,1))/(1+{fields[9]})^{year}'
                    for year, phase in enumerate((1/3, 2/3, 1, 1, 1), start=1)
                )
            else:
                npv_formula = "=" + "+".join(
                    f'(E{target_row}*MIN(1,{fields[4]}+{0.2 * (year - 1):.1f})-'
                    f'IF({year}<={fields[8]},{fields[5]}/{fields[8]},0))/(1+{fields[9]})^{year}'
                    for year in range(1, 6)
                )
            calc.append([
                row.deal_id, row.lever, scenario, row.currency,
                f'=IF(COUNT({",".join(fields)})<7,"",{gross})',
                f'=IF(E{target_row}="","",E{target_row}*{fields[4]}-{fields[5]}/{fields[8]})',
                npv_formula,
                row.assumption_type, row.confidence, row.assumption_ids,
            ])
    style_header(calc)

    bridge = workbook.create_sheet("Announced vs Est vs Realised")
    bridge.append([
        "Deal", "Announced target", "Independent low", "Independent base",
        "Independent high", "Reported realisation", "Basis / caveat",
    ])
    targets = pd.read_csv(RESEARCH / "announced_synergy_targets.csv")
    model_output = pd.read_csv(ROOT / "dashboard" / "tableau_synergy_data.csv")
    for target in targets.itertuples(index=False):
        subset = model_output[
            (model_output.deal_id == target.deal_id)
            & (model_output.evidence_status == "estimated")
        ]
        vals = {
            scenario: subset.loc[subset.scenario.eq(scenario), "gross_run_rate"].sum()
            for scenario in ("low", "base", "high")
        }
        bridge.append([
            target.deal_id, f"{target.currency} {target.target_value:,.0f}m",
            f"{target.currency} {vals['low']:,.0f}m",
            f"{target.currency} {vals['base']:,.0f}m",
            f"{target.currency} {vals['high']:,.0f}m",
            f"{target.currency} {target.realised_value:,.0f}m cumulative",
            target.caveat,
        ])
    style_header(bridge)

    evidence = pd.read_csv(RESEARCH / "quantitative_backtest.csv").fillna("")
    evidence_sheet = workbook.create_sheet("Evidence Back-test")
    evidence_sheet.append(list(evidence.columns))
    for row in evidence.itertuples(index=False, name=None):
        evidence_sheet.append(list(row))
    style_header(evidence_sheet)

    financial = pd.read_csv(RESEARCH / "financial_due_diligence.csv").fillna("")
    financial_sheet = workbook.create_sheet("Financial Diligence")
    financial_sheet.append(list(financial.columns))
    for row in financial.itertuples(index=False, name=None):
        financial_sheet.append(list(row))
    style_header(financial_sheet)

    for tab in workbook.worksheets:
        for col in range(1, tab.max_column + 1):
            width = max(
                len(str(tab.cell(row, col).value or ""))
                for row in range(1, tab.max_row + 1)
            )
            tab.column_dimensions[get_column_letter(col)].width = min(48, max(14, width + 2))
    OUT.mkdir(exist_ok=True)
    workbook.save(OUT / "MA_Synergy_Model.xlsx")


def add_slide(prs, title, subtitle, bullets, source_note):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(15, 32, 55)
    title_box = slide.shapes.add_textbox(
        Inches(.65), Inches(.45), Inches(12), Inches(.8)
    ).text_frame
    title_paragraph = title_box.paragraphs[0]
    title_paragraph.text = title
    title_paragraph.font.size = Pt(25)
    title_paragraph.font.bold = True
    title_paragraph.font.color.rgb = RGBColor(255, 255, 255)

    sub = slide.shapes.add_textbox(
        Inches(.7), Inches(1.35), Inches(12), Inches(.55)
    ).text_frame.paragraphs[0]
    sub.text = subtitle
    sub.font.size = Pt(15)
    sub.font.bold = True
    sub.font.color.rgb = RGBColor(100, 190, 220)

    body = slide.shapes.add_textbox(
        Inches(.8), Inches(2.1), Inches(11.7), Inches(4.2)
    ).text_frame
    body.word_wrap = True
    for index, bullet in enumerate(bullets):
        paragraph = body.paragraphs[0] if index == 0 else body.add_paragraph()
        paragraph.text = bullet
        paragraph.font.size = Pt(17)
        paragraph.font.color.rgb = RGBColor(235, 240, 245)
        paragraph.space_after = Pt(12)

    footer = slide.shapes.add_textbox(
        Inches(.7), Inches(6.95), Inches(12), Inches(.25)
    ).text_frame.paragraphs[0]
    footer.text = source_note
    footer.font.size = Pt(8)
    footer.font.color.rgb = RGBColor(175, 190, 205)
    return slide


def add_synergy_bridge(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(15, 32, 55)

    title = slide.shapes.add_textbox(
        Inches(.65), Inches(.45), Inches(12), Inches(.75)
    ).text_frame.paragraphs[0]
    title.text = "Kraft Heinz: $313m benchmarked overlap pool filters to $211m achievable run-rate"
    title.font.size = Pt(23)
    title.font.bold = True
    title.font.color.rgb = RGBColor(255, 255, 255)

    subtitle = slide.shapes.add_textbox(
        Inches(.7), Inches(1.28), Inches(12), Inches(.55)
    ).text_frame.paragraphs[0]
    subtitle.text = "USD million | $23.0bn analyst cost-pool proxy × 1.36% pre-2015 median overlap × 90% addressable × 75% achievable"
    subtitle.font.size = Pt(14)
    subtitle.font.color.rgb = RGBColor(100, 190, 220)

    stages = [
        ("Identified overlap", 313, 0, 313, "313"),
        ("Not addressable", -31, 282, 313, "(31)"),
        ("Execution haircut", -70, 211, 282, "(70)"),
        ("Base-case run-rate", 211, 0, 211, "211"),
    ]
    x_positions = [1.0, 3.65, 6.3, 8.95]
    bottom = 5.25
    scale = 1.75 / 313
    bar_width = 1.25
    for index, (label, value, lower, upper, display) in enumerate(stages):
        x = x_positions[index]
        y = bottom - upper * scale
        height = max((upper - lower) * scale, .06)
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(x),
            Inches(y),
            Inches(bar_width),
            Inches(height),
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = (
            RGBColor(42, 139, 174) if index in (0, 3) else RGBColor(190, 111, 82)
        )
        bar.line.fill.background()

        value_box = slide.shapes.add_textbox(
            Inches(x - .1), Inches(y - .35), Inches(bar_width + .2), Inches(.28)
        ).text_frame.paragraphs[0]
        value_box.text = display
        value_box.font.size = Pt(14)
        value_box.font.bold = True
        value_box.font.color.rgb = RGBColor(255, 255, 255)

        label_box = slide.shapes.add_textbox(
            Inches(x - .25), Inches(5.38), Inches(bar_width + .5), Inches(.6)
        ).text_frame.paragraphs[0]
        label_box.text = label
        label_box.font.size = Pt(11)
        label_box.font.color.rgb = RGBColor(235, 240, 245)
        label_box.alignment = 2

        if index in (0, 1, 2):
            next_x = x_positions[index + 1]
            connector_y = bottom - lower * scale
            connector = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(x + bar_width),
                Inches(connector_y - .01),
                Inches(next_x - x - bar_width),
                Inches(.02),
            )
            connector.fill.solid()
            connector.fill.fore_color.rgb = RGBColor(150, 165, 180)
            connector.line.fill.background()

    note = slide.shapes.add_textbox(
        Inches(.85), Inches(6.2), Inches(11.7), Inches(.55)
    ).text_frame.paragraphs[0]
    note.text = "Announced target: $1,500m annual run-rate | Independent base: $211m | Reported: >$1,700m cumulative by end-2017 (different basis)"
    note.font.size = Pt(13)
    note.font.bold = True
    note.font.color.rgb = RGBColor(100, 190, 220)

    footer = slide.shapes.add_textbox(
        Inches(.7), Inches(6.95), Inches(12), Inches(.25)
    ).text_frame.paragraphs[0]
    footer.text = "Analyst assumptions: low confidence. Sources: SEC merger filing, SEC 10-Q and post-integration investor presentation."
    footer.font.size = Pt(8)
    footer.font.color.rgb = RGBColor(175, 190, 205)
    return slide


def add_native_chart_slides(prs):
    scenario_data = pd.read_csv(ROOT / "dashboard" / "tableau_synergy_data.csv")
    financial_data = pd.read_csv(RESEARCH / "financial_due_diligence.csv")

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(15, 32, 55)
    heading = slide.shapes.add_textbox(Inches(.6), Inches(.35), Inches(12), Inches(.6)).text_frame.paragraphs[0]
    heading.text = "Scenario ranges: HDFC funding economics and Kraft Heinz cost takeout"
    heading.font.size = Pt(22)
    heading.font.bold = True
    heading.font.color.rgb = RGBColor(255, 255, 255)

    for deal, label, x in [
        ("HDFC", "HDFC net recurring scenario (INR crore)", .6),
        ("KRAFT_HEINZ", "Kraft Heinz gross run-rate (USD million)", 6.8),
    ]:
        subset = scenario_data[
            (scenario_data.deal_id == deal)
            & (scenario_data.evidence_status == "estimated")
        ]
        values = subset.groupby("scenario").gross_run_rate.sum().reindex(["low", "base", "high"]).fillna(0)
        chart_data = CategoryChartData()
        chart_data.categories = ["Low", "Base", "High"]
        chart_data.add_series(label, tuple(float(value) for value in values))
        chart = slide.shapes.add_chart(
            XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(1.25), Inches(5.8), Inches(4.9), chart_data
        ).chart
        chart.has_title = True
        chart.chart_title.text_frame.text = label
        chart.has_legend = False
        chart.value_axis.has_major_gridlines = True

    for company, metric, title in [
        ("Blinkit", "Adjusted EBITDA", "Blinkit adjusted EBITDA loss narrows, but is not attributed to merger synergy"),
        ("HDFC Bank", "Cost-to-income ratio", "HDFC Bank cost-to-income trend: FY23 pre-merger to FY25 post-merger"),
    ]:
        subset = financial_data[
            (financial_data.company == company) & (financial_data.metric == metric)
        ].copy()
        subset["period"] = subset["period"].astype(str)
        subset["value"] = pd.to_numeric(subset["value"], errors="coerce")
        subset = subset.dropna(subset=["value"]).sort_values("period")

        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor(15, 32, 55)
        heading = slide.shapes.add_textbox(Inches(.6), Inches(.35), Inches(12), Inches(.75)).text_frame.paragraphs[0]
        heading.text = title
        heading.font.size = Pt(21)
        heading.font.bold = True
        heading.font.color.rgb = RGBColor(255, 255, 255)

        chart_data = CategoryChartData()
        chart_data.categories = subset["period"].tolist()
        chart_data.add_series(metric, tuple(float(value) for value in subset["value"]))
        chart = slide.shapes.add_chart(
            XL_CHART_TYPE.LINE_MARKERS, Inches(.8), Inches(1.35), Inches(11.7), Inches(4.8), chart_data
        ).chart
        chart.has_title = True
        chart.chart_title.text_frame.text = metric
        chart.has_legend = False
        chart.value_axis.has_major_gridlines = True

        note = slide.shapes.add_textbox(Inches(.8), Inches(6.35), Inches(11.7), Inches(.45)).text_frame.paragraphs[0]
        if company == "Blinkit":
            note.text = "FY23 is a partial-year consolidation period; adjusted EBITDA trajectory is standalone segment performance, not proof of synergy."
        else:
            note.text = "FY23 is pre-merger HDFC Bank standalone; FY24/FY25 include the merged bank. Mix and scale changes limit comparability."
        note.font.size = Pt(11)
        note.font.color.rgb = RGBColor(205, 215, 225)

    add_slide(
        prs,
        "Appendix: Air India–Vistara remains a qualitative PMI case",
        "Integration milestones are visible; attributable financial synergy is not",
        [
            "4,000+ vendor contracts consolidated; 140+ IT systems aligned; 270,000 bookings and 4.5m loyalty accounts migrated.",
            "These are integration outputs, not verified procurement savings or revenue uplift.",
            "A full diligence case needs vendor spend/rate baselines, route contribution, fleet utilisation and service disruption costs.",
        ],
        "Sources: Air India merger completion release and transformation update.",
    )
    add_slide(
        prs,
        "Appendix: Microsoft–LinkedIn is a financial trajectory case, not the headline event study",
        "LinkedIn grew to scale, but product attach synergy is not isolated in public segment reporting",
        [
            "LinkedIn contributed USD 2.268bn revenue and USD 948m operating loss in the partial FY17 period.",
            "FY18 revenue was USD 5.3bn; FY26 revenue reached USD 19.817bn.",
            "Growth is not proof of Microsoft cross-sell; require enterprise seat attach, renewal and matched-cohort contribution data.",
        ],
        "Sources: Microsoft FY17, FY18 and FY26 annual reports.",
    )


def build_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    add_slide(
        prs,
        "Kraft Heinz reported >$1.7bn cumulative savings against a $1.5bn annual run-rate target",
        "The deal provides a real announced-versus-estimated-versus-reported back-test",
        [
            "Management target: $1.5bn annual cost savings run-rate by end-2017.",
            "Independent base case: $0.21bn gross annual run-rate; low/high range $0.04bn–$0.91bn using pre-2015 benchmark ratios.",
            "Reported delivery: >$1.7bn cumulative savings by end-2017, net of approx. $200m business investments.",
            "Important: cumulative realised savings and annual run-rate are different measurement bases.",
        ],
        "Sources: SEC merger filing, SEC 10-Q and post-integration investor presentation. Independent estimate is an analyst scenario.",
    )
    add_synergy_bridge(prs)
    add_slide(
        prs,
        "HDFC's value case is funding substitution, with regulatory drag explicitly netted",
        "Base-case five-year NPV after the new PSL/PSLC lever: approximately –₹261cr",
        [
            "HDFC Ltd's FY23 funding mix: market borrowings 45%; deposits ₹1,52,111cr or 27% of borrowings. Implied market-borrowing pool ~₹2.54 lakh crore.",
            "Funding benefit uses 25/50/75 bps spread sensitivities and 10%/20%/30% substitution; all are analyst assumptions, not realised savings.",
            "CRR 4% and SLR 18% are modelled as a reserve opportunity-cost sensitivity; HDFC's merger deck said Day-0 CRR was organically met and SLR assets earned positive returns.",
            "Small operating overlap is based on HDFC Ltd standalone non-finance costs (~₹2,420cr), not the merged bank's expense base. Phased PSL/PSLC base sensitivity contributes ~–₹382cr five-year NPV; this is not a disclosed shortfall.",
        ],
        "Sources: HDFC Ltd FY23 annual report and earnings transcript; HDFC Bank merger investor deck. Low-confidence sensitivities.",
    )
    add_slide(
        prs,
        "HDFC: matched migration stress turns five-year NPV negative",
        "Five-year NPV by lever (₹ crore); programme costs are included in the operating-cost lever",
        [
            "Base case: funding substitution +₹475cr; CRR/SLR reserve drag –₹228cr; legacy operating-cost lever –₹127cr; phased PSL/PSLC cost –₹382cr; combined ~–₹261cr.",
            "Matched stress before PSL remains –₹352cr (30% / 80%) and –₹278cr (20% / 65%). Including high PSL/PSLC downside, totals become ~–₹2,680cr and ~–₹2,606cr respectively.",
            "The operating-cost lever is negative in low/base/high because the three-year programme cost exceeds the discounted savings.",
            "These are analyst sensitivities, not realised merger savings. PSL assumes the high PSLC-SMF premium and 75% of the conservative shortfall proxy is not met organically.",
        ],
        "Sources: HDFC Ltd FY23 annual report and earnings transcript; HDFC Bank merger deck and post-merger results. Model outputs from scenario inputs.",
    )
    add_slide(
        prs,
        "Kraft Heinz's later impairments show why synergy delivery is not value creation",
        "FY18 impairments were USD 15.936bn; FY19 added another USD 1.899bn",
        [
            "FY18: USD 7.008bn goodwill and USD 8.928bn intangible-asset impairment charges.",
            "FY19: a further USD 1.197bn goodwill and USD 702m intangible-asset impairment charges.",
            "FY19 net sales fell to USD 24.977bn from USD 26.268bn in FY18.",
            "The charges are accounting evidence of reduced expected value, not a clean causal estimate of merger NPV.",
        ],
        "Source: Kraft Heinz FY2019 Form 10-K. Cost synergies were reported; total shareholder value creation is a separate test.",
    )
    add_slide(
        prs,
        "The two headline cases separate upside, downside and delivery evidence",
        "HDFC: funding-led net synergy sensitivity | Kraft Heinz: announced target versus reported delivery",
        [
            "HDFC: funding substitution is offset by CRR/SLR reserve carry and a quantified-but-low-confidence PSL/PSLC downside sensitivity.",
            "Kraft Heinz: USD 1.5bn annual run-rate target; >USD 1.7bn cumulative reported savings by end-2017. The target exceeds the pre-2015 benchmark overlap range.",
            "Kraft Heinz overlap range uses three pre-March-2015 deals (0.38% / 1.36% / 4.91%); the $1.5bn target equals 6.52% of the $23bn cost-pool proxy and exceeds the benchmark high.",
            "Air India–Vistara and Microsoft–LinkedIn are moved to the appendix; Blinkit is retained only as a financial trend chart.",
        ],
        "Four-way status remains: announced, estimated, realised and unverified. See source register and evidence ledger.",
    )
    add_native_chart_slides(prs)
    OUT.mkdir(exist_ok=True)
    prs.save(OUT / "MA_Executive_Deck.pptx")


def main():
    build_workbook()
    build_deck()
    print("Generated editable scenario workbook and answer-led deck with native charts and appendix.")


if __name__ == "__main__":
    main()
