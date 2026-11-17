# Synergy model

The core model now focuses on two transactions:
- **HDFC Ltd–HDFC Bank:** funding substitution benefit, CRR/SLR reserve opportunity-cost drag, a small legacy standalone operating-cost overlap, and an unquantified PSL compliance downside.
- **Kraft Heinz:** announced target back-test, multi-year integration-cost allocation and five-year NPV.

## HDFC funding economics
HDFC Ltd's FY23 call reported market borrowings at 45% of borrowings and deposits of ₹1,52,111cr or 27% of borrowings. The model derives an approximate market-borrowing pool of ₹2.54 lakh crore from these rounded percentages. It applies a 25/50/75 bps funding spread sensitivity to the assumed share refinanced through bank deposits.

A separate negative CRR/SLR sensitivity applies the 4% CRR and 18% SLR regulatory thresholds disclosed in the merger investor deck. The opportunity-cost spread is an analyst sensitivity; actual Day-0 liquidity offsets and liability-level NDTL treatment must be reconciled. PSL compliance remains unquantified until incremental shortfall and PSLC costs are observed.

The cost overlap is based only on HDFC Ltd FY23 standalone employee, depreciation and other expenses (₹2,419.87cr proxy), not the merged bank's full expense base.

## Kraft Heinz
The USD 23bn cost pool and 7%/9%/11% overlap are explicitly an **ex-post sensitivity**, set after the announced target and realised savings were known. This is not a cited benchmark or a blind prediction. The total programme cost is spread over three years; the model reports first-year net and a five-year NPV using a 10% analyst discount rate.

## Formula
Gross run-rate = baseline × overlap × addressable × achievable × unit-economics factor × direction.

First-year net = gross run-rate × year-one ramp − total integration programme cost / programme years.

Five-year NPV ramps synergy over the first four years, spreads programme costs over the specified programme period and discounts annual cash flows. The discount rate is a transparent analyst assumption.

Blank values mean unverified, not zero. All inputs carry an assumption ID and confidence.


## Input-column mapping by lever

The CSV uses a common calculation schema, but some fields have lever-specific meanings:

| Input field | Operating-cost overlap | Funding substitution | CRR/SLR reserve drag |
|---|---|---|---|
| `overlap_{scenario}` | Share of standalone expense assumed duplicated | Share of market borrowings migrated to deposits | Share of market borrowings migrated and exposed to reserve drag |
| `addressable_{scenario}` | Share of duplicated expense that can be removed | Share of migrated funding eligible for substitution | Combined CRR/SLR reserve share (22% sensitivity) |
| `achievable_{scenario}` | Execution-realisation factor | Execution-realisation factor | Applied at 100% in the current reserve sensitivity |
| `contribution_margin_{scenario}` | Retained unit economics (1.0) | Funding spread advantage as a decimal (25/50/75 bps) | Reserve opportunity-cost spread as a decimal (40/61/80 bps) |

These shared column names are a schema convenience, not interchangeable economic concepts. Read the lever-specific definitions before interpreting the values.

## HDFC stress case

The generated `stress` rows pair the low funding-substitution assumptions with the high reserve-drag assumptions and, for the legacy operating-cost lever, the high one-off programme-cost assumption. The stress case is a deliberately adverse analyst sensitivity, not a management forecast or observed outcome. The five-year NPV includes programme costs and should be read as the after-costs result.
