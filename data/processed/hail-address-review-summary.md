# Hail address manual-review summary

Generated: 2026-08-31

The review queue contains **289** Hail records that were not confidently auto-matched.

| Reason | Records | Share | Explanation |
|---|---:|---:|---|
| Loose address near unclaimed footprint | 288 | 99.7% | A same-street Address Point is within 10 house numbers, and a nearby footprint with no accepted Hail match is proposed; its canonical address may be on a cross street. |
| Multiple plausible footprints | 1 | 0.3% | The street and base number agree, but suffix, rear, or range differences leave more than one plausible footprint. |

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
