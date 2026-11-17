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
        "Net first-year", "Five-year NPV", "Classification", "Confidence", "Assumption IDs",
    ])
    columns = {name: get_column_letter(index + 1) for index, name in enumerate(inputs.columns)}
    for index, row in enumerate(inputs.itertuples(index=False), start=2):
        for scenario in ("low", "base", "high"):
            target_row = calc.max_row + 1
            fields = [
                f"'Scenario Inputs'!{columns[name]}{index}"
                for name in (
                    "baseline_amount", f"overlap_{scenario}",
                    f"addressable_{scenario}", f"achievable_{scenario}",
                    f"ramp_{scenario}", f"one_off_cost_{scenario}",
                    f"contribution_margin_{scenario}", "direction",
                    "integration_program_years", "discount_rate",
                )
            ]
            gross = (
                "*".join((fields[0], fields[1], fields[2], fields[3], fields[6]))
                + f'*IF({fields[7]}="negative",-1,1)'
            )
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

    comparability = pd.read_csv(ROOT / "dashboard" / "deal_comparability.csv").fillna("")
    comparable_sheet = workbook.create_sheet("Four-Deal Comparability")
    comparable_sheet.append(list(comparability.columns))
    for row in comparability.itertuples(index=False, name=None):
        comparable_sheet.append(list(row))
    style_header(comparable_sheet)

    evidence = pd.read_csv(RESEARCH / "quantitative_backtest.csv").fillna("")
    evidence_sheet = workbook.create_sheet("Evidence Back-test")
    evidence_sheet.append(list(evidence.columns))
    for row in evidence.itertuples(index=False, name=None):
        evidence_sheet.append(list(row))
    style_header(evidence_sheet)

    integration_costs = pd.read_csv(RESEARCH / "integration_cost_tracker.csv").fillna("")
    cost_sheet = workbook.create_sheet("Integration Cost Tracker")
    cost_sheet.append(list(integration_costs.columns))
    for row in integration_costs.itertuples(index=False, name=None):
        cost_sheet.append(list(row))
    style_header(cost_sheet)

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
    title.text = "Kraft Heinz: $2.07bn overlap pool filters to $1.40bn achievable run-rate"
    title.font.size = Pt(23)
    title.font.bold = True
    title.font.color.rgb = RGBColor(255, 255, 255)

    subtitle = slide.shapes.add_textbox(
        Inches(.7), Inches(1.28), Inches(12), Inches(.55)
    ).text_frame.paragraphs[0]
    subtitle.text = "USD million | $23.0bn analyst cost-pool proxy × 9% overlap × 90% addressable × 75% achievable"
    subtitle.font.size = Pt(14)
    subtitle.font.color.rgb = RGBColor(100, 190, 220)

    stages = [
        ("Identified overlap", 2070, 0, 2070, "2,070"),
        ("Not addressable", -207, 1863, 2070, "(207)"),
        ("Execution haircut", -466, 1397, 1863, "(466)"),
        ("Base-case run-rate", 1397, 0, 1397, "1,397"),
    ]
    x_positions = [1.0, 3.65, 6.3, 8.95]
    bottom = 5.25
    scale = 1.75 / 2070
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
    note.text = "Announced target: $1,500m annual run-rate | Independent base: $1,397m | Reported: >$1,700m cumulative by end-2017 (different basis)"
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
    """Build a concise five-slide deck covering every core transaction."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    add_slide(
        prs,
        "Four M&A cases. Different synergy evidence. One consistent diligence framework.",
        "Keep management targets, independent scenarios, reported delivery and unverified outcomes separate",
        [
            "HDFC–HDFC Bank: partial outside-in estimate; base net recurring scenario ~₹86cr before unquantified PSL and programme costs.",
            "Air India–Vistara: financial scale and integration milestones are observable; attributable procurement or network savings are not disclosed.",
            "Zomato–Blinkit: consolidated cost pools and Blinkit segment trajectory are observable; standalone integration savings are not isolated.",
            "Kraft Heinz: $1.5bn annual run-rate target and >$1.7bn cumulative reported savings; independent $1.40bn base is an ex-post sensitivity, not a blind prediction.",
            "Microsoft–LinkedIn remains an additional reference case outside the four-deal core.",
        ],
        "Sources: deal briefs, source register and four-deal comparability scorecard. Values remain in deal currency.",
    )
    add_slide(
        prs,
        "HDFC: funding substitution is the value driver; reserve carry and PSL are the offsets",
        "Illustrative base annual run-rate: +₹142cr funding benefit +₹12cr cost overlap −₹68cr reserve drag = ~₹86cr net",
        [
            "HDFC Ltd reported 45% of borrowings from market borrowings; deposits were ₹1,52,111cr or 27% of borrowings.",
            "The implied market-borrowing pool is ~₹2.54 lakh crore; 25/50/75 bps spread and 10%/20%/30% migration are analyst sensitivities.",
            "CRR/SLR reserve opportunity cost is modelled as a drag; HDFC's merger deck described Day-0 CRR as organically met and SLR assets as earning positive returns.",
            "The small cost-overlap pool uses HDFC Ltd standalone non-finance expenses, not the merged bank's full expense base. PSL shortfall/PSLC cost remains unquantified.",
        ],
        "Sources: HDFC Ltd FY23 annual report and Q4 earnings call; HDFC Bank merger investor deck. Low-confidence analyst scenario, not reported savings.",
    )
    add_slide(
        prs,
        "Air India–Vistara: integration scale is proven; financial synergy is not yet measurable",
        "FY24 standalone revenue: Air India ₹51,365cr + Vistara ₹15,191cr | FY25 merged revenue ₹76,754cr",
        [
            "The merger completed on 12 November 2024. Tata Sons' FY25 annual report shows FY25 merged-entity loss after tax of ₹10,859cr.",
            "At completion, Air India reported 4,000+ vendor contracts consolidated, 140+ IT systems aligned, 270,000 bookings migrated and 4.5m loyalty accounts inducted.",
            "These are integration outputs, not savings. FY24 standalone and FY25 merged financial periods are not like-for-like.",
            "A defensible estimate needs category-level vendor spend/rate cards, route contribution, fleet utilisation, integration cash costs and service-quality controls.",
        ],
        "Sources: Tata Sons FY25 Annual Report; Air India merger completion release. No quantified synergy target or attributable realised saving identified.",
    )
    add_slide(
        prs,
        "Zomato–Blinkit: do not mistake acquired-business growth for integration synergy",
        "FY24 consolidated operating-cost pools are available; Blinkit-only cost split and causal integration benefits are not",
        [
            "FY24 consolidated delivery and related charges were ₹3,915cr; advertising/sales promotion ₹1,432cr; IT support ₹485cr; outsourced support ₹330cr; other expenses ₹1,179cr.",
            "These expense lines span food delivery and quick commerce. FY24 includes a full year of Blinkit consolidation versus a partial FY23 period.",
            "Blinkit adjusted EBITDA improved from -₹562cr in FY23 to -₹292cr in FY25; this segment trajectory is not a causal estimate of acquisition synergy.",
            "The next diligence step is matched-city delivery cost, cross-order customer cohorts, incremental contribution after incentives and a standalone counterfactual.",
        ],
        "Sources: Zomato FY24 Annual Report; Eternal FY25 Annual Report; BSE acquisition Q&A. Synergy estimate remains unquantified.",
    )
    add_slide(
        prs,
        "Kraft Heinz: reported cost savings did not guarantee value creation",
        "Announced: $1.5bn annual run-rate | Independent base: $1.40bn gross (ex-post sensitivity) | Reported: >$1.7bn cumulative",
        [
            "Management announced a $1.5bn annual cost-savings run-rate target by end-2017. Management later reported more than $1.7bn cumulative savings by end-2017.",
            "The model's $0.71bn–$2.04bn range is a sensitivity using a $23bn proxy cost pool and 7%/9%/11% overlap; it was calibrated after the target was public.",
            "SEC 10-Ks reported $829m, $887m and $339m of integration-program expense in 2015, 2016 and 2017 respectively; cumulative pre-tax programme costs reached $2.055bn, with approximately 60% expected to be cash.",
            "FY18/FY19 goodwill and intangible impairments totalled $17.835bn. Impairments indicate value erosion but do not alone prove merger causality.",
        ],
        "Sources: SEC merger filing, FY2016 and FY2017 Forms 10-K, post-integration presentation and FY2019 Form 10-K. Annual run-rate and cumulative savings are different measures.",
    )
    OUT.mkdir(exist_ok=True)
    prs.save(OUT / "MA_Executive_Deck.pptx")


def main():
    build_workbook()
    build_deck()
    print("Generated editable scenario workbook and answer-led deck with native charts and appendix.")


if __name__ == "__main__":
    main()
