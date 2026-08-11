# Hail–Cambridge address crosswalk data profile

> **Superseded for current Hail counts:** this exploratory profile was produced
> before the `razed` logic was corrected. Use
> [`building-database-methodology.md`](building-database-methodology.md) for the
> implemented matcher, current counts, and construction-year display rules.

Date profiled: 2026-08-10

## Scope and conclusion

This report profiles four local source datasets without modifying them:

1. `data/raw/Hail_buildings_dataset.csv`
2. `data/processed/Cambridge_Property_Database_FY2016-FY2026_20260805_deduped.geojson`
3. `cambridgegis_data/Address/Address_Points/ADDRESS_AddressPoints.geojson`
4. `cambridgegis_data/Basemap/Buildings/BASEMAP_Buildings.geojson`

Hail records whose `razed` value is `true` were excluded from every Hail statistic and relationship test. Of 18,784 total Hail rows, 15,787 were excluded and 2,997 non-razed rows were profiled.

**Conclusion:** Address Points can serve as the authoritative bridge from a current, unambiguous address to both a building footprint and an assessor parcel. Its populated identifiers have excellent referential coverage: 99.84% of Address Point rows with a `BldgID` link to a footprint, and 99.81% of Address Point rows link from `ml` to assessor `gisid`. It is not, however, a complete or inherently one-to-one historical-address crosswalk. Under a conservative exploratory address normalization, only 1,969 of 2,997 active Hail records (65.70%) resolve to one Address Point `BldgID` and one assessor `gisid`, with both IDs present in their target datasets. Another 970 Hail rows (32.37%) have no Address Point address match. Ambiguous and unmatched cases must therefore remain unresolved for later stages rather than be forced.

## Methods and definitions

- Logical missing values include JSON null, empty/whitespace strings, and the string sentinels `None`, `null`, and `nan` (case-insensitive).
- Duplicate counts are exact-value counts unless explicitly labeled canonical.
- The exploratory canonical address comparison lowercased text, removed punctuation and repeated whitespace, converted Unicode to ASCII where possible, and standardized common street suffixes such as `Street` → `st` and `Avenue` → `ave`. This was used only to measure likely relationships; it is not a final matcher.
- A “one-to-many” relationship counts distinct target values per source value, not duplicate rows pointing to the same target.
- Percentages use row counts unless the text explicitly says “distinct IDs” or “distinct addresses.”
- The assessor input is already a processed, cross-year deduplicated product; the statistics describe that file, not every raw fiscal-year record.

## Dataset inventory and schema

| Dataset | Profiled records | Geometry | Fields | Intended grain |
|---|---:|---|---:|---|
| Hail buildings (non-razed only) | 2,997 | None (CSV) | 17 | Historical building/address entry |
| Cambridge assessor, FY2016–FY2026 deduped | 13,219 | 13,148 Point; 71 missing | 74 | Deduplicated assessor property record |
| Address Points | 21,107 | 21,107 Point | 13 | Address/entrance point |
| Building footprints | 18,236 | 18,228 Polygon; 8 MultiPolygon | 10 | Building footprint feature |

### Hail buildings

Fields: `building_id`, `street_name`, `address_raw`, `normalized_address`, `address_min`, `address_max`, `historic_address`, `building_type`, `stories`, `construction_year`, `architect`, `builder`, `owner_at_construction`, `razed`, `source_page`, `source_anchor`, `summary_raw`.

All fields are stored as strings. Key quality among the 2,997 non-razed rows:

| Field | Missing | Missing rate | Distinct | Duplicate values | Rows in duplicate values | Maximum multiplicity |
|---|---:|---:|---:|---:|---:|---:|
| `building_id` | 0 | 0.00% | 2,997 | 0 | 0 | 1 |
| `normalized_address` | 0 | 0.00% | 2,896 | 97 | 198 | 4 |
| `address_raw` | 0 | 0.00% | 2,757 | 191 | 431 | 5 |
| `construction_year` | 234 | 7.81% | 201 populated year values | 166 | 2,728 | 65 |
| `razed` | 0 | 0.00% | — | — | — | — |

`building_id` is a suitable row identifier in the active Hail subset. Address duplication is expected because the register can contain multiple structures or episodes at an address. Consequently, a Hail address alone must not be treated as a building identifier.

### Cambridge assessor data

The 74 properties comprise metadata fields; identifiers and location; assessment and sale values; ownership; exterior, interior, systems, condition, parking, basement, zoning, and property-class attributes; plus deduplication provenance.

Important fields include:

- Identity/location: `pid`, `gisid`, `map_lot`, `address`, `unit`, `bldgnum`, `latitude`, `longitude`.
- Time/provenance: `yearofassessment`, `:id`, `:created_at`, `:updated_at`, `:version`, `__dedupe_source_count__`, `__dedupe_address_variants__`, `__dedupe_selected_address__`.
- Building attributes: `condition_yearbuilt`, `propertyclass`, `stateclasscode`, `exterior_*`, `interior_*`, `systems_*`, and `condition_*`.
- Valuation/ownership: `landvalue`, `buildingvalue`, `assessedvalue`, `previousassessedvalue`, `saleprice`, `saledate`, `owner_*`.

All important linkage fields are strings in this GeoJSON.

| Field | Missing | Missing rate | Distinct | Duplicate values | Rows in duplicate values | Maximum multiplicity |
|---|---:|---:|---:|---:|---:|---:|
| `pid` | 0 | 0.00% | 13,153 | 66 | 132 | 2 |
| `gisid` | 1 | 0.01% | 13,218 | 0 | 0 | 1 |
| `map_lot` | 0 | 0.00% | 13,215 | 4 | 8 | 2 |
| `address` | 0 | 0.00% | 13,013 | 171 | 377 | 5 |
| `latitude`, `longitude` | 71 each | 0.54% | — | — | — | — |
| `condition_yearbuilt` | 0 | 0.00% | — | — | — | — |

`gisid` is the cleanest unique parcel identifier in this file. `pid` is not unique despite the file’s deduped name. The four duplicated `map_lot` values are `184-192`, `196-163`, `246A-61`, and `259-17-135`; therefore `map_lot` also cannot be assumed globally unique without validation.

### Address Points

Fields: `address_id`, `Full_Addr`, `StNm`, `StName`, `BldgID`, `ml`, `Entry`, `TYPE`, `lat`, `lon`, `EditDate`, `created_date`, `last_edited_date`.

`address_id`, `lat`, and `lon` are numeric; the linking and address fields are strings.

| Field | Missing | Missing rate | Distinct | Duplicate values | Rows in duplicate values | Maximum multiplicity |
|---|---:|---:|---:|---:|---:|---:|
| `address_id` | 0 | 0.00% | 20,858 | 182 | 431 | 17 |
| `Full_Addr` | 0 | 0.00% | 20,859 | 181 | 429 | 17 |
| `BldgID` | 473 | 2.24% | 12,992 | 4,785 | 12,427 | 29 |
| `ml` | 0 | 0.00% | 12,596 | 4,739 | 13,250 | 147 |
| `Entry` | 12 | 0.06% | — | — | — | — |
| `lat`, `lon` | 0 each | 0.00% | — | — | — | — |
| `created_date` | 20,267 | 96.02% | — | — | — | — |
| `last_edited_date` | 16,211 | 76.80% | — | — | — | — |

The near-identical duplication profiles of `address_id` and `Full_Addr` warrant treating `address_id` as non-unique in this extract. Multiple Address Point rows can represent entrances or repeated features for the same displayed address.

### Building footprints

Fields: `BldgID`, `TYPE`, `BASE_ELEV`, `ELEV_GL`, `ELEV_SL`, `TOP_GL`, `TOP_SL`, `EditDate`, `created_date`, `last_edited_date`.

`BldgID` and the type/date fields are strings; elevation fields are numeric.

| Field | Missing | Missing rate | Distinct | Duplicate values | Rows in duplicate values | Maximum multiplicity |
|---|---:|---:|---:|---:|---:|---:|
| `BldgID` | 0 | 0.00% | 18,233 | 3 | 6 | 2 |

The duplicated footprint IDs are `114-3`, `218-2`, and `129-7`, each appearing twice. A downstream process should either dissolve/aggregate these geometries by `BldgID` or explicitly retain multipart membership; it should not silently select the first feature.

## Cross-dataset identifier relationships

### Address Points `BldgID` → footprint `BldgID`

| Metric | Result |
|---|---:|
| Address Point rows with populated `BldgID` | 20,634 / 21,107 (97.76%) |
| Those rows matching a footprint | 20,602 / 20,634 (99.84%) |
| Distinct Address Point `BldgID` values matching a footprint | 12,969 / 12,992 (99.82%) |
| Footprint rows represented by an Address Point `BldgID` | 12,972 / 18,236 (71.13%) |
| Distinct Address Point `BldgID` values absent from footprints | 23 (32 Address Point rows) |
| Footprint `BldgID` values absent from Address Points | 5,264 |

This is a highly reliable exact join when `BldgID` is populated, but it is not complete in either direction. Missing Address Point `BldgID`s and footprints without addresses are expected exception classes, not evidence that an address should be assigned by loose text similarity.

### Address Points `ml` → assessor `gisid`

| Metric | Result |
|---|---:|
| Address Point rows with populated `ml` | 21,107 / 21,107 (100.00%) |
| Those rows matching assessor `gisid` | 21,066 / 21,107 (99.81%) |
| Distinct `ml` values matching assessor `gisid` | 12,591 / 12,596 (99.96%) |
| Assessor `gisid` values represented by Address Points | 12,591 / 13,218 (95.26%) |
| Distinct unmatched Address Point `ml` values | 5 (41 rows) |
| Assessor `gisid` values absent from Address Points | 627 |

The five unmatched `ml` values are `--MD`, `--RR`, `165-59`, `ROAD`, and `Watertown`. Four are evident nonstandard/sentinel geography values; `165-59` should be investigated as a genuine stale or missing parcel link.

Joining `ml` to assessor `map_lot` is materially worse: only 16,416 of 21,107 Address Point rows (77.77%) match, versus 99.81% for `gisid`. Therefore the deterministic parcel join should be **`Address Points.ml = assessor.gisid`**, with `map_lot` used only for secondary validation or specifically modeled unit/parcel cases.

### Address text → Address Points → both targets

Within Address Points:

- Of 20,859 distinct exact `Full_Addr` values, 20,394 have at least one populated `BldgID`; 20,271 map to exactly one distinct `BldgID`, while 123 map to multiple building IDs (maximum 17).
- `Full_Addr` maps to exactly one `ml` for 20,841 distinct addresses and to multiple `ml` values for 18 (maximum 5).
- `BldgID` maps to exactly one distinct address for 8,237 building IDs and multiple addresses for 4,755 (maximum 29). This is expected for buildings with multiple numbered addresses or entrances.
- `ml` maps to exactly one distinct address for 7,945 parcels and multiple addresses for 4,651 (maximum 147). A parcel is therefore not an address-level identifier.
- `ml` maps to one `BldgID` for 11,538 values and multiple building IDs for 790 (maximum 36).
- `BldgID` maps to one `ml` for 12,559 values and multiple parcels for 433 (maximum 18).

These relationships show that Address Points is a good crosswalk table, but the real-world model is not globally one-to-one: one building can have many addresses, one parcel can contain many buildings, and a building can cross parcel boundaries.

## Hail coverage (non-razed records only)

The exploratory canonical comparison of Hail `normalized_address` to Address Points `Full_Addr` produced:

| Resolution status | Hail rows | Rate |
|---|---:|---:|
| One `BldgID` and one `ml`, both valid in target datasets | 1,969 | 65.70% |
| One `BldgID` and one `ml`, but footprint ID absent | 2 | 0.07% |
| Address Point match, but `BldgID` missing | 27 | 0.90% |
| Multiple `BldgID`, one parcel | 25 | 0.83% |
| One `BldgID`, multiple parcels | 2 | 0.07% |
| Multiple `BldgID` and multiple parcels | 2 | 0.07% |
| No Address Point address match | 970 | 32.37% |
| **Total** | **2,997** | **100.00%** |

Thus 1,971 Hail records (65.77%) reach a unique building/parcel pair through Address Points, and 1,969 (65.70%) also pass exact target-ID existence checks. Examples of legitimate ambiguity include:

- `120 Auburn Street`: two `BldgID`s, one parcel.
- `145 Brattle Street`: three `BldgID`s and two parcels.
- `32 Jefferson Street`: one `BldgID`, two parcels.

Examples with no current Address Point match include `17 Aberdeen Avenue`, `20 Albany Street`, and `40 Albany Street`. These may reflect historic numbering, changed street names, range/compound-address representation, or gaps in current layers. They should proceed to controlled historical/range/spatial stages rather than fuzzy matching by default.

For comparison, canonical address text alone matches 2,027 Hail rows to at least one Address Point row, but only 1,157 directly to an assessor address. This is further evidence that Address Points should be the bridge and that direct Hail-to-assessor text matching should not be the primary route.

## Recommended deterministic matching stages

No matcher is implemented here. A later implementation should produce candidate sets, confidence/reason codes, and an auditable trace at every stage.

1. **Eligibility and source validation**
   - Exclude Hail rows where normalized `razed = true` before generating candidates.
   - Preserve `building_id` as the Hail row key.
   - Reject or quarantine missing/invalid target IDs; do not interpret sentinel `ml` values as parcels.

2. **Conservative exact address match**
   - Parse Hail and Address Point addresses into house number/range, suffix, street name, and street type.
   - Apply only documented, reversible normalization: case, punctuation, whitespace, directional conventions, and a controlled street-suffix dictionary.
   - Match exact parsed components to `Full_Addr`/`StNm` + `StName`.
   - Accept automatically only when the resulting candidate set has exactly one distinct `BldgID` and one distinct `ml`.

3. **Exact target-ID validation**
   - Require `Address Points.BldgID = footprints.BldgID`.
   - Require `Address Points.ml = assessor.gisid`.
   - Record missing target IDs as exceptions. Do not substitute `map_lot` for `gisid` automatically.

4. **Range and compound-address expansion**
   - Use Hail `address_min`, `address_max`, `address_raw`, and parsed Address Point `StNm` to test explicit containment in a numeric range on the same canonical street.
   - Model odd/even parity and letter/rear suffixes; do not treat every integer inside a range as equivalent without these checks.
   - Retain all candidates when a range covers multiple buildings or parcels.

5. **Controlled aliases and historical addresses**
   - Apply a reviewed table of historic street names, renamed streets, and number changes using Hail `historic_address` and source evidence.
   - Store the alias rule and source used. Avoid unconstrained edit-distance matching.

6. **Spatial confirmation, not silent reassignment**
   - For matched Address Points, verify point-in-footprint or a documented small nearest-footprint tolerance and compare the resulting `BldgID`.
   - Validate parcel membership using a parcel geometry layer if introduced later; assessor points alone cannot prove polygon containment.
   - Use spatial disagreement to lower confidence or flag review, not to overwrite exact IDs silently.

7. **Ambiguity handling and review queue**
   - Never collapse multi-building or multi-parcel candidates by row order.
   - Rank only with deterministic evidence such as address role (`Entry`), range fit, footprint containment, parcel containment, building type, and compatible construction year.
   - Leave unresolved ties unmatched and export candidate IDs plus reason codes for review.

8. **Optional last-resort similarity stage**
   - If later authorized, restrict fuzzy comparison to candidates on a known street/alias and compatible number/range; impose explicit thresholds and manual review.
   - Do not allow citywide fuzzy address matching to create final links.

## Proposed output fields for a future matcher

A future crosswalk should retain at least:

- `hail_building_id`
- `address_point_id` (and source feature index because `address_id` is not unique here)
- `bldgid`
- `assessor_gisid`
- `assessor_pid`
- `match_stage`
- `match_status` (`matched`, `ambiguous`, `unmatched`, `invalid_target`)
- `confidence_class`
- `candidate_count_address_points`, `candidate_count_bldgids`, `candidate_count_parcels`
- `address_normalization_rule`, `alias_rule`, `range_rule`
- `footprint_validation`, `parcel_validation`
- `review_reason`

The source feature index is important because Address Point `address_id` has 182 duplicated values spanning 431 rows. Likewise, a matched footprint result must tolerate the three duplicated `BldgID` values by representing all component geometries or a deterministic aggregate.

## Decision

Use Address Points as the central deterministic bridge, with `BldgID` for footprints and `ml = assessor.gisid` for parcels. Treat a crosswalk as reliable only after candidate cardinality and target existence checks. For the current non-razed Hail subset, this yields a strong high-confidence first stage covering about two-thirds of records; the remaining third requires range, historical-alias, and spatial review stages and must not be force-matched.
