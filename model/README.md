# Synergy model

The core model now focuses on two transactions:
- **HDFC Ltd–HDFC Bank:** funding substitution benefit, CRR/SLR reserve opportunity-cost drag, a small legacy standalone operating-cost overlap, and a phased PSL/PSLC downside sensitivity.
- **Kraft Heinz:** announced target back-test, multi-year integration-cost allocation and five-year NPV.

## HDFC funding economics
HDFC Ltd's FY23 call reported market borrowings at 45% of borrowings and deposits of ₹1,52,111cr or 27% of borrowings. The model derives an approximate market-borrowing pool of ₹2.54 lakh crore from these rounded percentages. It applies a 25/50/75 bps funding spread sensitivity to the assumed share refinanced through bank deposits.

A separate negative CRR/SLR sensitivity applies the 4% CRR and 18% SLR regulatory thresholds disclosed in the merger investor deck. The opportunity-cost spread is an analyst sensitivity; actual Day-0 liquidity offsets and liability-level NDTL treatment must be reconciled. PSL/PSLC is modelled separately using a conservative ₹1,36,810cr non-individual HDFC Ltd FY22 loan-book proxy (corporate and other loans), the 40% overall PSL target, a one-third/two-thirds/full three-year phase-in, and a 25%/50%/75% residual shortfall assumed to be purchased via PSLC after organic lending. The PSLC price sensitivity uses RBI FY24-25 weighted-average premiums for General (0.01%), Agriculture (0.48%) and Small and Marginal Farmers (1.95%) certificates. This is not HDFC Bank's disclosed shortfall: individual-loan eligibility, corporate-loan eligibility, quarterly ANBC and sub-target mix are not available at loan level.

The cost overlap is based only on HDFC Ltd FY23 standalone employee, depreciation and other expenses (₹2,419.87cr proxy), not the merged bank's full expense base.

## Kraft Heinz
The USD 23bn cost pool uses the **pre-2015 benchmark** committed in `research/pre2015_synergy_benchmarks.csv`. Three disclosed annual cost-synergy targets divided by combined cost bases produce ratios of 0.3837%, 1.3593% and 4.9130%; the median is 1.3593%. Kraft Heinz's USD 1.5bn target equals 6.52% of the USD 23bn proxy and therefore exceeds the benchmark high. The Pringles denominator includes an EBITDA-derived cost proxy; this small, heterogeneous sample is directional rather than a statistical estimate. The total programme cost is spread over three years; the model reports first-year net and a five-year NPV using a 10% analyst discount rate.

## Formula
Gross run-rate = baseline × overlap × addressable × achievable × unit-economics factor × direction.

First-year net = gross run-rate × year-one ramp − total integration programme cost / programme years.

Five-year NPV ramps synergy over the first four years, spreads programme costs over the specified programme period and discounts annual cash flows. The discount rate is a transparent analyst assumption.

Blank values mean unverified, not zero. All inputs carry an assumption ID and confidence.


## Input-column mapping by lever

The CSV uses a common calculation schema, but some fields have lever-specific meanings:

| Input field | Operating-cost overlap | Funding substitution | CRR/SLR reserve drag | PSL/PSLC cost |
|---|---|---|---|
| `overlap_{scenario}` | Share of standalone expense assumed duplicated | Share of market borrowings migrated to deposits | Share of market borrowings migrated and exposed to reserve drag |
| `addressable_{scenario}` | Share of duplicated expense that can be removed | Share of migrated funding eligible for substitution | Combined CRR/SLR reserve share (22% sensitivity) | Legacy portfolio phase-in (1/3, 2/3, full) |
| `achievable_{scenario}` | Execution-realisation factor | Execution-realisation factor | Applied at 100% in the current reserve sensitivity | Share of residual shortfall assumed to require PSLC purchase after organic lending (25%/50%/75%) |
| `contribution_margin_{scenario}` | Retained unit economics (1.0) | Funding spread advantage as a decimal (25/50/75 bps) | Reserve opportunity-cost spread as a decimal (40/61/80 bps) | PSLC premium as a decimal (General/Agriculture/SMF: 0.01%/0.48%/1.95%) | PSLC premium as a decimal (General/Agriculture/SMF: 0.01%/0.48%/1.95%) |

These shared column names are a schema convenience, not interchangeable economic concepts. Read the lever-specific definitions before interpreting the values.

## HDFC stress cases

Two matched migration stresses are generated from the `stress_scenario` column in `synergy_inputs.csv`. Funding substitution selects its low columns; CRR/SLR reserve drag and legacy operating cost select their high columns. Only the matched migration share and ramp are overridden by the two-case dictionary:
- **30% / 80%:** funding and reserve drag share a 30% migration assumption and 80% ramp.
- **20% / 65%:** funding and reserve drag share a 20% migration assumption and 65% ramp.

The operating-cost lever retains its high-column overlap, addressability, execution, ramp and programme-cost inputs in both stresses. The PSL lever also uses its high-column inputs in both stresses. All other stress parameters are read from the selected low/high input columns; the workbook formulas point to those same input cells. These are analyst sensitivities, not management forecasts or observed outcomes. Five-year NPV includes programme costs and phases the PSL exposure one-third/two-thirds/full over the first three years.
