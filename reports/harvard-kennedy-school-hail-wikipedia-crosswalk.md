# Harvard Kennedy School Hail and Wikipedia crosswalk

Generated: 2026-08-29

## Scope and sources

The review uses Harvard Kennedy School's current campus map and treats the
individual named buildings as separate footprints even where Cambridge address
points assign the shared address 79 JFK Street.

Primary Harvard sources:

- HKS, [campus map](https://www.hks.harvard.edu/sites/default/files/about_us/HKS_Campus_Map.pdf)
- Harvard Property Information Resource Center, [Littauer Center](https://harvardplanning.emuseum.com/sites/706/littauer-center-ksg)
- HKS/GSD, [Health Impact Assessment of the HKS campus](https://research.gsd.harvard.edu/hapi/files/2016/03/HIA-Report_Draft3-HKS-GSD-small.pdf)

## Results

| Building | Footprint | Address-point address | Construction date | Hail treatment |
|---|---|---|---:|---|
| Littauer Center | `398-1` | 79 JFK Street | 1978 | `kennedy-st_79_2` matched |
| Belfer Center | `398-5` | 79 JFK Street | 1983 | No building-specific Hail record |
| David Rubenstein Building | `398-9` | 79 JFK Street | 1986 | No building-specific Hail record |
| Taubman Building | `398-3` | 15 Eliot Street | 1989–1990 | `eliot-st_15_3` already matched |

The former automatic result attached `kennedy-st_79_2` to all three footprints
at 79 JFK Street, making Belfer and Rubenstein appear to have Littauer's 1978
date and generic classroom-building description. The manual decision now limits
that record to Littauer (`398-1`). The map retains the assessor years on Belfer
and Rubenstein because the Hail snapshot contains no building-specific records
for them; the documented dates above are therefore evidence for future sourced
metadata rather than invented Hail associations.

The Harvard Kennedy School Wikipedia article remains on Littauer. The Institute
of Politics at Harvard Kennedy School article is now also assigned to Littauer,
because the official HKS map locates the institute on Littauer levels 1 and 2.
