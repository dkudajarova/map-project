# Hail address manual-review summary

Generated: 2026-08-17

The review queue contains **714** Hail records that were not confidently auto-matched.

| Reason | Records | Share | Explanation |
|---|---:|---:|---|
| Multiple plausible footprints | 509 | 71.3% | The street and base number agree, but suffix, rear, or range differences leave more than one plausible footprint. |
| Building complex may span footprints | 179 | 25.1% | The address resolves, but the Hail entry is a building complex and may represent more than one footprint. |
| Unproven historical address or alias | 18 | 2.5% | A historical address or street alias produced candidates, but the alias has not yet been proven for automatic matching. |
| Small street-name spelling difference | 8 | 1.1% | The number is compatible and the street spelling is close, but fuzzy street-name matches require manual confirmation. |

## Street-name spelling differences

These Stage 6 review rows share a compatible house number but use a different street spelling. A confirmed alias can still appear here when a separate footprint or building-complex ambiguity remains.

| Hail street name | Address Point street name | Review records | Review basis |
|---|---|---:|---|
| Allen Drive | Bishop Allen Dr | 4 | Building complex may span footprints |
| Columbia Terrace | Columbia Ter | 2 | Building complex may span footprints |
| Gerry'S Landing Road | Gerrys Landing Rd | 2 | Multiple plausible footprints |
| Kennedy Street | Tenney St | 2 | Multiple plausible footprints; Small street-name spelling difference |
| Lake View Avenue | Lakeview Ave | 2 | Multiple plausible footprints |
| Broadway Terrace | Broadway Ter | 1 | Multiple plausible footprints |
| Buckingham Street | Buckingham Pl | 1 | Small street-name spelling difference |
| Fayette Park | Fayette Pk | 1 | Building complex may span footprints |
| Garden Street | Garden Ct | 1 | Small street-name spelling difference |
| Hayward Street | Howard St | 1 | Small street-name spelling difference |
| Hilliard Street | Hilliard Pl | 1 | Multiple plausible footprints |
| Hilliard Street | Willard St | 1 | Multiple plausible footprints |
| Holworthy Terrace | Holworthy Ter | 1 | Multiple plausible footprints |
| Longfellow Park | Longfellow Pk | 1 | Multiple plausible footprints |
| Mason Street | Madison St | 1 | Small street-name spelling difference |
| Moulton Street | Milton St | 1 | Small street-name spelling difference |
| Mount Pleasant Street | Mt Pleasant St | 1 | Multiple plausible footprints |
| Union Terrace | Union Ter | 1 | Building complex may span footprints |
| Walker Terrace | Walker Ter | 1 | Building complex may span footprints |
| Washburn Terrace | Washburn Ter | 1 | Building complex may span footprints |
| Webster Avenue | Western Ave | 1 | Small street-name spelling difference |
| Willard Street | Hilliard St | 1 | Small street-name spelling difference |

## Interpretation

- A review row is a candidate set, not a rejected match. `candidate_bldgids` and `candidate_addresses` contain the evidence to inspect.
- Multiple-footprint cases should be resolved using rear/suffix/range context and spatial evidence.
- Building-complex cases need a decision about whether one Hail entry applies to one footprint or several.
- Historical aliases should become automatic only after an explicit alias is validated and documented.
- Spelling-difference candidates must remain manual until the spelling correspondence is proven.
