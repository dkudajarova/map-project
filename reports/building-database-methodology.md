# Footprint-master building database methodology

Updated: 2026-08-11

## Data model

The Cambridge building-footprint GeoJSON is the master layer. Every source footprint feature is retained, producing 18,236 output features. Address Points is the bridge:

- `Address Points.BldgID` → `Building footprints.BldgID`
- `Address Points.ml` → `Assessor.gisid`
- Standardized Address Point addresses → staged Hail address candidates

Razed Hail records are excluded from matching. Cross-reference and unclear Hail records are left unmatched. A Hail `Building complex` candidate is routed to review even when its address has only one footprint candidate, because the historical entry may represent multiple geometries.

## Deterministic Hail stages

| Stage | Implemented rule | Treatment |
|---:|---|---|
| 1 | Exact standardized Hail street and full house token matches one Address Point and one valid `BldgID` | Auto-accept; complexes review |
| 2 | Hail numeric range contains Address Point number(s) and all valid candidates resolve to one `BldgID` | Usually auto-accept; complexes review |
| 3 | Exact Hail address matches multiple Address Points whose valid IDs all resolve to one `BldgID` | Auto-accept; complexes review |
| 4 | Street and number overlap, while rear/suffix/range representation differs | Auto-accept only one plausible footprint; otherwise review |
| 5 | Hail `historic_address` produces candidate(s) on a current Address Point street/address | Review |
| 6 | Street edit distance is small and the house number is compatible | Review |
| 7 | No valid footprint candidate, or record classification is cross-reference/unclear | Leave unmatched |

Standardization is deliberately conservative: Unicode/case/punctuation/spacing normalization, common street-suffix normalization, and preservation of rear, letter, fraction, plus, and range markers in the full house token.

## Current match results

| Stage | Status | Hail records |
|---:|---|---:|
| 0 | Excluded as razed | 5,451 |
| 1 | Accepted | 6,672 |
| 1 | Review | 32 |
| 2 | Accepted | 1,544 |
| 2 | Review | 54 |
| 3 | Accepted | 20 |
| 3 | Review | 2 |
| 4 | Accepted | 166 |
| 4 | Review | 2,426 |
| 5 | Review | 71 |
| 6 | Review | 276 |
| 7 | Unmatched | 2,070 |

Totals: 8,402 accepted Hail records, 2,861 review records, 2,070 unmatched records, and 5,451 excluded records.

## Displayed construction year

Only accepted Hail matches participate in the displayed-year calculation.

1. If accepted Hail records on a footprint contain more than one distinct complete construction year, flag `hail_year_conflict = true`, do not select a Hail year, and use the assessor year if available.
2. If exactly one Hail year exists and the assessor year is missing, use Hail.
3. If exactly one Hail year exists and its absolute difference from the assessor year is **less than 50 years**, use Hail.
4. If the difference is **50 years or greater**, retain the assessor year and set `year_needs_review = true`.
5. If neither source provides a valid complete year, leave `year_built` null.

Current footprint results:

| Display source | Footprints |
|---|---:|
| Hail | 7,189 |
| Assessor | 5,645 |
| Unknown | 5,402 |

There are 868 footprint records flagged for construction-year review because Hail records conflict or Hail and assessor differ by at least 50 years.

## Output files

- `data/processed/cambridge-buildings-enriched.geojson`: canonical processed footprint database.
- `public/data/cambridge-buildings.geojson`: byte-identical map-serving copy.
- `data/processed/hail-address-matches.csv`: audit row for every Hail record, including exclusions and unmatched records.
- `data/processed/hail-address-review.csv`: only candidates requiring manual review.

Run `npm run data:build` to regenerate all four outputs.

## Principal footprint properties

- Master and address: `BldgID`, `footprint_feature_index`, `Address`, `addresses`, `address_count`, `address_point_count`.
- Assessor: `assessor_gisid`, `assessor_gisids`, `assessor_pid`, `assessor_address`, `assessor_year_built`, `PropertyClass`, `Zoning`.
- Hail: `hail_match_count`, `hail_building_ids`, `hail_years`, `hail_year_built`, `hail_year_conflict`, `hail_primary_building_id`, `hail_match_stage`, `hail_classification`, `hail_building_type`, `hail_architect`, `hail_builder`, `hail_owner_at_construction`, `hail_summary`.
- Display: `year_built`, `year_built_source`, `year_difference_hail_assessor`, `year_needs_review`, `age`, `age_band`.

## Review workflow

Review `hail-address-review.csv` without editing generated output files. A future adjudication file should map `building_id` to an approved `BldgID`, reviewer, decision date, and note. The build can then load those overrides before deterministic stages. Proven historical street aliases should similarly be stored in a small explicit alias table and promoted from Stage 5 review only after validation.

