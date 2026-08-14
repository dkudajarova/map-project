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
| 5 | An address in Hail `historic_address` or the parsed detail/body exactly equals a current canonical Address Point address | Auto-accept one valid footprint; ambiguous matches and complexes review; broader historic aliases review |
| 6 | Street edit distance is small and the house number is compatible | Auto-accept a configured confirmed alias with one footprint; configured exceptions, multiple footprints, complexes, and unknown pairs review |
| 7 | No valid footprint candidate, or record classification is cross-reference/unclear | Leave unmatched |
| 8 | A reviewer explicitly selects a valid footprint from the manual-review workspace | Accept the override; a reviewer can instead preserve an explicit `no_map_match` decision |

Standardization is deliberately conservative: Unicode/case/punctuation/spacing normalization, common street-suffix normalization, and preservation of rear, letter, fraction, plus, and range markers in the full house token.

Numeric address-range matching preserves street-side parity. A same-parity
range advances by two (`215–217` represents `215` and `217`, not `216`). If the
two written endpoints have different parity, only those explicit endpoints are
eligible; interior numbers are not inferred. This parity rule applies both to
Stage 2 range containment and Stage 4 number/range overlap.

## Current match results

| Stage | Status | Hail records |
|---:|---|---:|
| 0 | Excluded as razed | 5,451 |
| 1 | Accepted | 6,672 |
| 1 | Review | 29 |
| 2 | Accepted | 3,097 |
| 2 | Review | 125 |
| 3 | Accepted | 20 |
| 3 | Review | 2 |
| 4 | Accepted | 144 |
| 4 | Review | 643 |
| 5 | Accepted exact historic/detail addresses | 100 |
| 5 | Review | 21 |
| 6 | Accepted confirmed aliases | 252 |
| 6 | Review | 21 |
| 7 | Unmatched | 2,120 |
| 8 | Accepted manual overrides | 86 |
| 8 | Explicit no-map-match overrides | 1 |

Totals: 10,371 accepted Hail records, 841 review records, 2,121 unmatched/no-map-match records, and 5,451 excluded records.

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
| Hail | 9,005 |
| Assessor | 3,846 |
| Unknown | 5,385 |

There are 1,012 footprint records flagged for construction-year review because Hail records conflict or Hail and assessor differ by at least 50 years.

## Output files

- `data/processed/cambridge-buildings-enriched.geojson`: canonical processed footprint database.
- `public/data/cambridge-buildings.geojson`: byte-identical map-serving copy.
- `data/processed/hail-address-matches.csv`: audit row for every Hail record, including exclusions and unmatched records.
- `data/processed/hail-address-review.csv`: only candidates requiring manual review.
- `data/processed/hail-address-review-summary.md`: aggregate reasons the review
  rows were not confidently auto-matched.
- `data/processed/hail-manual-review.json`: compact review-application bundle,
  including original Hail details and proposed footprint candidates.
- `data/config/hail-street-aliases.json`: confirmed street spelling pairs and
  pairs explicitly reserved for manual review.
- `data/manual/hail-building-overrides.json`: durable, separate reviewer
  decisions keyed by Hail `building_id`; this is an input layer, not generated
  source data.
- `reports/manual-override-analysis.md`: repeatable summary of reviewer choices
  and evidence for possible future rules.

Run `npm run data:build` to regenerate the footprint map, audits, and review
bundle. Run `npm run overrides:analyze` after reviewing a street.

## Principal footprint properties

- Master and address: `BldgID`, `footprint_feature_index`, `Address`, `addresses`, `address_count`, `address_point_count`.
- Assessor: `assessor_gisid`, `assessor_gisids`, `assessor_pid`, `assessor_address`, `assessor_year_built`, `PropertyClass`, `Zoning`.
- Hail: `hail_match_count`, `hail_building_ids`, `hail_years`, `hail_year_built`, `hail_year_conflict`, `hail_primary_building_id`, `hail_match_stage`, `hail_classification`, `hail_building_type`, `hail_architect`, `hail_builder`, `hail_owner_at_construction`, `hail_summary`.
- Display: `year_built`, `year_built_source`, `year_difference_hail_assessor`, `year_needs_review`, `age`, `age_band`.

## Review workflow

Use `/review` on the local application. Records form one global priority queue:
the oldest complete construction years come first, records without complete
years come last, and ties favor entries with more populated building type/name,
architect, builder, owner, historic address, stories, and summary fields. The
left panel shows the Hail record, its original stage, review reason, and proposed candidates. The right panel
shows all Cambridge footprints; proposed candidates are highlighted, and any
number of proposed or neighboring footprints can be selected, including
footprints that were not proposed. A reviewer can also record `no_map_match`
and add a note.

Each saved decision is written atomically to the separate manual-override JSON.
For later rule analysis it retains the original stage, reason, proposed
`BldgID` list, the selected `bldgids` array (with legacy `bldgid` retaining the
first selection), and whether every selected footprint was proposed.
The data build applies matched decisions as Stage 8 and removes explicit
no-map-match decisions from the active review queue without modifying the Hail,
Address Points, assessor, or footprint sources. Clearing a decision restores
the original deterministic result on the next build.

The analysis script recommends only hypotheses supported by repeated outcomes;
it never changes matching rules automatically. Proven historical aliases or
other new rules should be added to configuration or pipeline code only after
validation on another street.
