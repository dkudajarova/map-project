# Appian Way HGSE Hail and Wikipedia crosswalk

Generated: 2026-08-29

## Scope and sources

This batch follows Harvard Graduate School of Education's official six-building
campus definition.

Primary Harvard sources:

- HGSE Operations, [campus map](https://operations.gse.harvard.edu/campus-info/hgse-campus-map)
- HGSE, [campus buildings and addresses](https://webmail.gse.harvard.edu/about/get-to-campus)
- HGSE, [history of the Read and Nichols House moves](https://www.gse.harvard.edu/sites/default/files/edmag/pdfs/2022-sum.pdf)
- Harvard Planning, [Larsen Hall](https://harvardplanning.emuseum.com/sites/418/larsen-hall)

## Results

| Hail record | Building | Current address | Footprint | Popup year |
|---|---|---|---|---|
| `appian-way_6_2` | Monroe C. Gutman Library | 6 Appian Way | `319-13` | 1970 |
| `appian-way_9-13` | Longfellow Hall | 13 Appian Way | `307-14` | 1929 |
| `appian-way_14_2` | Larsen Hall | 14 Appian Way | `319-7` | 1964 |
| `farwell-pl_11` | Nichols House | 7 Appian Way | `319-15` | 1828 |
| `farwell-pl_15_2` | Read House | 8 Appian Way | `319-12` | 1773 |
| `garden-st_3_2` | Westengard House | 3 Garden Street | `319-2` | 1851 |

Read House was previously marked as having no map match. Hail explicitly says
the 1773 house moved from Farwell Place in 1969, and HGSE identifies the
surviving building at 8 Appian Way. It is now matched to that footprint.

Read House's and Gutman Library's assessor value `1860`, and Westengard's
`1930`, are treated as narrowly scoped placeholders, allowing their accepted
Hail construction years to control the popups.

The Harvard Graduate School of Education Wikipedia article remains correctly
assigned to Longfellow Hall (`307-14`), the school's principal 13 Appian Way
address. The snapshot contains no separate geotagged articles for the other five
campus buildings.
