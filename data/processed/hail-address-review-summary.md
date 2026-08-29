# Hail address manual-review summary

Generated: 2026-08-28

The review queue contains **0** Hail records that were not confidently auto-matched.

| Reason | Records | Share | Explanation |
|---|---:|---:|---|

## Street-name spelling differences

These Stage 6 review rows share a compatible house number but use a different street spelling. A confirmed alias can still appear here when a separate footprint or building-complex ambiguity remains.

| Hail street name | Address Point street name | Review records | Review basis |
|---|---|---:|---|

## Interpretation

- A review row is a candidate set, not a rejected match. `candidate_bldgids` and `candidate_addresses` contain the evidence to inspect.
- Multiple-footprint cases should be resolved using rear/suffix/range context and spatial evidence.
- Building-complex cases need a decision about whether one Hail entry applies to one footprint or several.
- Historical aliases should become automatic only after an explicit alias is validated and documented.
- Spelling-difference candidates must remain manual until the spelling correspondence is proven.
