# Harvard Law School Hail name crosswalk

Generated: 2026-08-29

## Method

The Harvard Law School campus is treated as two connected, name-matched
complexes: the main academic buildings along Massachusetts Avenue and the
Graduate Commons/Gropius buildings along Everett Street. Cambridge Address
Points frequently assign one current address to multiple footprints, while the
Hail source uses older addresses within the same complex. Name, construction
history, and current Harvard addresses therefore control over an address-only
result.

Primary reference sources:

- Harvard Law School, [campus map and directions](https://hls.harvard.edu/wp-content/uploads/2022/08/HLS-Map-Directions.pdf)
- Harvard Law School, [department directory](https://hls.harvard.edu/campus-resources/department-directory/)
- Harvard Planning, [Austin Hall](https://harvardplanning.emuseum.com/sites/575/austin-hall)
- Harvard Planning, [Langdell Hall](https://harvardplanning.emuseum.com/sites/578/langdell-hall)
- Harvard Planning, [Story Hall](https://harvardplanning.emuseum.com/sites/562/story-hall)
- Harvard Planning, [Child Hall](https://harvardplanning.emuseum.com/sites/782/child-hall)
- Harvard Planning, [Harkness Commons](https://harvardplanning.emuseum.com/sites/805/harkness-commons)
- Harvard Planning, [Wasserstein Hall](https://harvardplanning.emuseum.com/sites/02541/wasserstein-hall)
- Harvard Law School, [Northwest Passage](https://hls.harvard.edu/today/northwest-passage/)

## Applied corrections

| Hail record | Building | Current Harvard address/status | Decision |
|---|---|---|---|
| `massachusetts-ave_1515` | Austin Hall | 1515 Massachusetts Avenue | Match only `266-14`; remove duplicate `266-15` |
| `massachusetts-ave_1535` | Langdell Hall Library | 1545 Massachusetts Avenue | Match `266-6` |
| `massachusetts-ave_1561r` | Hauser Hall | 1575 Massachusetts Avenue | Match `266-4` |
| `everett-st_12r` | Harkness Commons | 14 Everett Street; incorporated into the WCC complex | Match `253-6` |
| `everett-st_14` | Story Hall | 12 Everett Street | Match `253-9` |
| `everett-st_20r` | Child Hall | 26 Everett Street | Match `253-13` |
| `everett-st_10` | Former above-ground Everett garage | Demolished 2007 | No map match |
| `massachusetts-ave_1595` | Former Wyeth Hall | Demolished 2007 | No map match |

The five other named Gropius dormitory matches were already correct: Shaw
`253-2`, Holmes `253-3`, Ames `253-5`, Dane `253-8`, and Richards `253-7`.
Gannett House is also correctly represented by `massachusetts-ave_1511_2` on
`266-19`.

## Source coverage limitation

The Hail dataset records Langdell Hall at the historical rear address 1535(r)
Massachusetts Avenue and Hauser Hall at 1561(r), rather than their current
Harvard/Cambridge addresses of 1545 and 1575 Massachusetts Avenue. Both are
matched by name. The dataset contains no record for the newer
Wasserstein/Caspersen/Clinical building itself; no Hail record was invented for
that footprint.
