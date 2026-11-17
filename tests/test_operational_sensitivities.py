from pipeline.build_operational_sensitivities import build_air_india, build_zomato


def test_blinkit_order_sensitivity_uses_reported_fy25_volume_and_discloses_assumptions():
    result = build_zomato()
    delivery = result[result.lever.eq("Blinkit delivery-backend cost per order")]
    assert len(delivery) == 3
    assert set(delivery.reported_denominator) == {424.0}
    base = delivery[delivery.scenario.eq("base")].iloc[0]
    assert base.annual_sensitivity == 7.95
    assert base.output_unit == "INR crore"
    assert base.sensitivity_type == "illustrative_not_forecast"
    assert "no matched-city" in base.caveat.lower()


def test_cross_sell_sensitivity_uses_food_delivery_customer_pool_as_upper_bound():
    result = build_zomato()
    cross = result[result.lever.eq("Cross-platform customer activation")]
    assert set(cross.reported_denominator) == {20.6}
    base = cross[cross.scenario.eq("base")].iloc[0]
    assert base.annual_sensitivity == 3.708
    assert "net cross-sell eligible pool" in base.caveat


def test_air_india_procurement_is_reverse_hurdle_not_a_synergy_estimate():
    result = build_air_india()
    assert len(result) == 27
    row = result[
        result.hurdle_savings.eq(100)
        & result.assumed_contract_rate_reduction.eq(0.01)
        & result.assumed_capture_rate.eq(0.75)
    ].iloc[0]
    assert row.required_addressable_vendor_spend == 13333.33
    assert row.reported_contract_count == 4000
    assert row.sensitivity_type == "reverse_hurdle_not_forecast"
    assert "not spend data" in row.caveat
