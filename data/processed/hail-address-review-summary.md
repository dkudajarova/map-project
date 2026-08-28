# Hail address manual-review summary

Generated: 2026-08-28

The review queue contains **45** Hail records that were not confidently auto-matched.

| Reason | Records | Share | Explanation |
|---|---:|---:|---|
| Multiple plausible footprints | 31 | 68.9% | The street and base number agree, but suffix, rear, or range differences leave more than one plausible footprint. |
| Unproven historical address or alias | 10 | 22.2% | A historical address or street alias produced candidates, but the alias has not yet been proven for automatic matching. |
| Small street-name spelling difference | 4 | 8.9% | The number is compatible and the street spelling is close, but fuzzy street-name matches require manual confirmation. |

## Street-name spelling differences

These Stage 6 review rows share a compatible house number but use a different street spelling. A confirmed alias can still appear here when a separate footprint or building-complex ambiguity remains.

| Hail street name | Address Point street name | Review records | Review basis |
|---|---|---:|---|
| Hayward Street | Howard St | 1 | Small street-name spelling difference |
| Mason Street | Madison St | 1 | Small street-name spelling difference |
| Moulton Street | Milton St | 1 | Small street-name spelling difference |
| Mount Auburn Street | Mt Auburn St | 1 | Multiple plausible footprints |
| Webster Avenue | Western Ave | 1 | Small street-name spelling difference |

## Interpretation

- A review row is a candidate set, not a rejected match. `candidate_bldgids` and `candidate_addresses` contain the evidence to inspect.
- Multiple-footprint cases should be resolved using rear/suffix/range context and spatial evidence.
- Building-complex cases need a decision about whether one Hail entry applies to one footprint or several.
- Historical aliases should become automatic only after an explicit alias is validated and documented.
- Spelling-difference candidates must remain manual until the spelling correspondence is proven.
