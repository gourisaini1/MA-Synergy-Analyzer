"""Build transparent operational sensitivities for Air India and Blinkit.

These are reverse hurdles and illustrative unit-economics scenarios, not
independent synergy forecasts. Missing cost pools and customer overlap are not
imputed.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ZOMATO_OUT = ROOT / "dashboard" / "zomato_operational_sensitivities.csv"
AIR_OUT = ROOT / "dashboard" / "air_india_procurement_hurdles.csv"

# Reported FY25 operating denominators from Eternal FY25 annual report.
BLINKIT_ORDERS_MILLION = 424.0
FOOD_DELIVERY_MTC_MILLION = 20.6
AIR_INDIA_CONSOLIDATED_VENDOR_CONTRACTS = 4000
SCENARIOS = ("low", "base", "high")


def build_zomato():
    rows = []
    delivery = {
        "low": (0.50, 0.10, 0.50),
        "base": (1.00, 0.25, 0.75),
        "high": (2.00, 0.50, 0.90),
    }
    for scenario, (saving_per_order, eligible_share, capture) in delivery.items():
        annual = (
            BLINKIT_ORDERS_MILLION * saving_per_order
            * eligible_share * capture / 10
        )
        rows.append({
            "deal_id": "ZOMATO",
            "lever": "Blinkit delivery-backend cost per order",
            "scenario": scenario,
            "reported_denominator": BLINKIT_ORDERS_MILLION,
            "denominator_unit": "FY25 million orders",
            "assumed_unit_economics": saving_per_order,
            "unit_economics_unit": "INR saved per eligible order",
            "eligible_share": eligible_share,
            "capture_rate": capture,
            "annual_sensitivity": round(annual, 3),
            "output_unit": "INR crore",
            "sensitivity_type": "illustrative_not_forecast",
            "source_id": "ZOM-02",
            "caveat": (
                "Uses FY25 Blinkit order volume. Per-order saving, eligible order "
                "share and capture are analyst sensitivities; no matched-city "
                "counterfactual or merger attribution is disclosed. Excludes "
                "implementation costs, service-level effects and dis-synergies."
            ),
        })

    cross_sell = {
        "low": (0.25, 0.01, 0.25, 10.0),
        "base": (0.50, 0.03, 0.50, 20.0),
        "high": (0.75, 0.05, 1.00, 30.0),
    }
    for scenario, (net_eligible_share, conversion, extra_orders, contribution) in cross_sell.items():
        incremental = (
            FOOD_DELIVERY_MTC_MILLION * net_eligible_share * conversion
            * extra_orders * contribution * 12 / 10
        )
        rows.append({
            "deal_id": "ZOMATO",
            "lever": "Cross-platform customer activation",
            "scenario": scenario,
            "reported_denominator": FOOD_DELIVERY_MTC_MILLION,
            "denominator_unit": "FY25 average monthly food-delivery MTC (million)",
            "assumed_unit_economics": contribution,
            "unit_economics_unit": "INR contribution per incremental order",
            "eligible_share": net_eligible_share,
            "capture_rate": conversion,
            "annual_sensitivity": round(incremental, 3),
            "output_unit": "INR crore",
            "sensitivity_type": "illustrative_not_forecast",
            "source_id": "ZOM-02",
            "caveat": (
                "Gross food-delivery MTC is not the net cross-sell eligible pool. "
                "Eligible share, conversion, incremental orders per converted "
                "customer per month and contribution per order are analyst "
                "sensitivities. Requires deduplicated customer cohorts and "
                "incremental contribution after discounts/cannibalisation."
            ),
        })
    return pd.DataFrame(rows)


def build_air_india():
    rows = []
    targets = (100.0, 250.0, 500.0)
    rate_reductions = (0.005, 0.01, 0.02)
    capture_rates = (0.50, 0.75, 0.90)
    for target in targets:
        for rate in rate_reductions:
            for capture in capture_rates:
                spend = target / (rate * capture)
                rows.append({
                    "deal_id": "AIR_INDIA",
                    "hurdle_savings": target,
                    "hurdle_unit": "INR crore annual recurring savings",
                    "assumed_contract_rate_reduction": rate,
                    "assumed_capture_rate": capture,
                    "required_addressable_vendor_spend": round(spend, 2),
                    "spend_unit": "INR crore",
                    "reported_contract_count": AIR_INDIA_CONSOLIDATED_VENDOR_CONTRACTS,
                    "sensitivity_type": "reverse_hurdle_not_forecast",
                    "source_id": "AIR-01",
                    "caveat": (
                        "Solves required eligible spend = savings hurdle / "
                        "(rate reduction × capture). 4,000+ consolidated contracts "
                        "is a milestone, not spend data. Requires category-level "
                        "spend, matched contract scope/rates, volumes, termination "
                        "costs and service-level controls. No synergy amount inferred."
                    ),
                })
    return pd.DataFrame(rows)


def main():
    zomato = build_zomato()
    air = build_air_india()
    ZOMATO_OUT.parent.mkdir(parents=True, exist_ok=True)
    zomato.to_csv(ZOMATO_OUT, index=False)
    air.to_csv(AIR_OUT, index=False)
    print(
        f"Wrote {len(zomato)} illustrative Blinkit sensitivities and "
        f"{len(air)} Air India procurement reverse hurdles."
    )


if __name__ == "__main__":
    main()
