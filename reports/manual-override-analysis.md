# Manual override analysis

Generated: 2026-08-11T17:04:11+00:00

This report analyzes the separate manual-override layer. It does not modify Hail, Address Points, assessor, or footprint source files.

## Overall decisions

| Measure | Records | Rate |
| --- | --- | --- |
| Reviewed | 18 | 100.0% |
| Matched to a proposed candidate | 18 | 100.0% |
| Matched to a neighboring/non-proposed building | 0 | 0.0% |
| All matched decisions | 18 | 100.0% |
| No map match | 0 | 0.0% |

## Results by street

| Street | Reviewed | Proposed | Neighbor | No match |
| --- | --- | --- | --- | --- |
| Allen Street | 4 | 4 | 0 | 0 |
| Allston Street | 13 | 13 | 0 | 0 |
| Appian Way | 1 | 1 | 0 | 0 |

## Replay against current deterministic rules

Saved decisions remain authoritative, but the pipeline also records what the current rules would have done before applying each override.

| Hail address | Reviewer BldgID | Generated stage | Generated status | Generated BldgID | Comparison |
| --- | --- | --- | --- | --- | --- |
| 14-20 Allen Street | 101-1 | 2 | review | — | still requires review |
| 15-17 Allen Street | 91-9 | 2 | accepted | 91-9 | reproduced automatically |
| 7-13 Allen Street | 91-11 | 2 | accepted | 91-11 | reproduced automatically |
| 8-10 Allen Street | 101-3 | 2 | accepted | 101-3 | reproduced automatically |
| 146-148 Allston Street | 719-12 | 2 | accepted | 719-12 | reproduced automatically |
| 150-152 Allston Street | 719-13 | 2 | accepted | 719-13 | reproduced automatically |
| 151-157 Allston Street | 713-24 | 2 | accepted | 713-24 | reproduced automatically |
| 156-160 Allston Street | 719-10 | 2 | accepted | 719-10 | reproduced automatically |
| 164-170 Allston Street | 719-5 | 2 | accepted | 719-5 | reproduced automatically |
| 215-217 Allston Street | 704-30 | 2 | accepted | 704-30 | reproduced automatically |
| 57-59 Allston Street | 724-18 | 2 | accepted | 724-18 | reproduced automatically |
| 58-62 Allston Street | 732-10 | 2 | accepted | 732-10 | reproduced automatically |
| 61-63 Allston Street | 724-2 | 2 | accepted | 724-2 | reproduced automatically |
| 64-66 Allston Street | 732-9 | 2 | accepted | 732-9 | reproduced automatically |
| 65-67 Allston Street | 724-1 | 2 | accepted | 724-1 | reproduced automatically |
| 72-74 Allston Street | 732-7 | 2 | accepted | 732-7 | reproduced automatically |
| 88-90 Allston Street | 729-1 | 2 | accepted | 729-1 | reproduced automatically |
| 9-13 Appian Way | 307-14 | 2 | accepted | 307-14 | reproduced automatically |

## Evidence by original review condition

| Stage | Reason | Outcome | Records |
| --- | --- | --- | --- |
| 4 | multiple_footprint_candidates | proposed | 18 |

## Candidate automatic rules

- The current deterministic rules reproduce 17 of 18 saved selections before overrides are applied; 0 produce a conflicting automatic building.
- Every reviewer selection was in the proposed candidate set. This validates candidate recall, but candidate membership alone is not a deterministic selection rule when more than one footprint was proposed.

These are hypotheses, not pipeline changes. The script intentionally requires repeated, consistent decisions and still recommends validation on another street.

## Decision detail

| Street | Hail address | Decision | Selected BldgID | Proposed BldgIDs | Proposed? | Note |
| --- | --- | --- | --- | --- | --- | --- |
| Allen Street | 14-20 Allen Street | matched | 101-1 | 101-1, 91-9 | yes | — |
| Allen Street | 15-17 Allen Street | matched | 91-9 | 101-1, 91-9 | yes | — |
| Allen Street | 7-13 Allen Street | matched | 91-11 | 101-3, 91-11 | yes | Verified via google map street view |
| Allen Street | 8-10 Allen Street | matched | 101-3 | 101-3, 91-11 | yes | — |
| Allston Street | 146-148 Allston Street | matched | 719-12 | 713-28, 719-12 | yes | — |
| Allston Street | 150-152 Allston Street | matched | 719-13 | 713-24, 719-13 | yes | — |
| Allston Street | 151-157 Allston Street | matched | 713-24 | 713-24, 719-10, 719-13 | yes | — |
| Allston Street | 156-160 Allston Street | matched | 719-10 | 713-24, 713-7, 719-10 | yes | — |
| Allston Street | 164-170 Allston Street | matched | 719-5 | 713-18, 719-5 | yes | — |
| Allston Street | 215-217 Allston Street | matched | 704-30 | 704-30, 711-6 | yes | — |
| Allston Street | 57-59 Allston Street | matched | 724-18 | 724-18, 732-10 | yes | the building is on the odd side of the street. |
| Allston Street | 58-62 Allston Street | matched | 732-10 | 724-18, 724-2, 732-10 | yes | — |
| Allston Street | 61-63 Allston Street | matched | 724-2 | 724-2, 732-10 | yes | — |
| Allston Street | 64-66 Allston Street | matched | 732-9 | 724-1, 732-9 | yes | — |
| Allston Street | 65-67 Allston Street | matched | 724-1 | 724-1, 732-9 | yes | — |
| Allston Street | 72-74 Allston Street | matched | 732-7 | 724-17, 732-7 | yes | — |
| Allston Street | 88-90 Allston Street | matched | 729-1 | 724-13, 729-1 | yes | — |
| Appian Way | 9-13 Appian Way | matched | 307-14 | 307-14, 319-3, 319-9 | yes | — |
