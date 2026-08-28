# Hail address manual-review summary

Generated: 2026-08-27

The review queue contains **317** Hail records that were not confidently auto-matched.

| Reason | Records | Share | Explanation |
|---|---:|---:|---|
| Multiple plausible footprints | 290 | 91.5% | The street and base number agree, but suffix, rear, or range differences leave more than one plausible footprint. |
| Unproven historical address or alias | 18 | 5.7% | A historical address or street alias produced candidates, but the alias has not yet been proven for automatic matching. |
| Small street-name spelling difference | 8 | 2.5% | The number is compatible and the street spelling is close, but fuzzy street-name matches require manual confirmation. |
| Building complex may span footprints | 1 | 0.3% | The address resolves, but the Hail entry is a building complex and may represent more than one footprint. |

## Street-name spelling differences

These Stage 6 review rows share a compatible house number but use a different street spelling. A confirmed alias can still appear here when a separate footprint or building-complex ambiguity remains.

| Hail street name | Address Point street name | Review records | Review basis |
|---|---|---:|---|
| Mount Auburn Street | Mt Auburn St | 11 | Multiple plausible footprints |
| Medeiros Avenue | Cardinal Medeiros Ave | 3 | Multiple plausible footprints |
| Gerry'S Landing Road | Gerrys Landing Rd | 2 | Multiple plausible footprints |
| Lake View Avenue | Lakeview Ave | 2 | Multiple plausible footprints |
| Buckingham Street | Buckingham Pl | 1 | Small street-name spelling difference |
| Coolidge Hill Street | Coolidge Hill | 1 | Multiple plausible footprints |
| Garden Street | Garden Ct | 1 | Small street-name spelling difference |
| Hayward Street | Howard St | 1 | Small street-name spelling difference |
| Holworthy Terrace | Holworthy Ter | 1 | Multiple plausible footprints |
| Kennedy Street | JFK St | 1 | Multiple plausible footprints |
| Longfellow Park | Longfellow Pk | 1 | Multiple plausible footprints |
| Mason Street | Madison St | 1 | Small street-name spelling difference |
| Moulton Street | Milton St | 1 | Small street-name spelling difference |
| Pemberton Street | Pemberton Ct | 1 | Small street-name spelling difference |
| Pleasant Street | Pleasant Pl | 1 | Small street-name spelling difference |
| Webster Avenue | Western Ave | 1 | Small street-name spelling difference |

## Interpretation

- A review row is a candidate set, not a rejected match. `candidate_bldgids` and `candidate_addresses` contain the evidence to inspect.
- Multiple-footprint cases should be resolved using rear/suffix/range context and spatial evidence.
- Building-complex cases need a decision about whether one Hail entry applies to one footprint or several.
- Historical aliases should become automatic only after an explicit alias is validated and documented.
- Spelling-difference candidates must remain manual until the spelling correspondence is proven.
