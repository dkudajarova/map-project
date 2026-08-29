# Harvard Yard Hail name crosswalk

Generated: 2026-08-28

## Method

Harvard Yard is treated as a campus-specific matching area rather than as a
continuation of its perimeter street addresses. The Cambridge Address Points
identify 32 Yard footprints with `BldgID` values beginning `318-`. Named Hail
records were matched to those footprints using current Harvard building names
and Harvard Yard addresses.

Primary reference sources:

- Harvard Environmental Health and Safety, [Building Evacuation Plans](https://www.ehs.harvard.edu/node/9170)
- Harvard Environmental Health and Safety, [Higher Education Act building inventory](https://www.ehs.harvard.edu/node/8336)
- Harvard Griffin GSAS, [Lehman Hall](https://gsas.harvard.edu/office/student-affairs/student-center/explore-lehman-hall)
- Harvard Planning, [Emerson Hall](https://harvardplanning.emuseum.com/sites/319/emerson-hall)
- Harvard History Department, [Robinson Hall](https://history.fas.harvard.edu/contact-0)
- Harvard Center for Public Service, [Phillips Brooks House](https://publicservice.fas.harvard.edu/contact-us)
- Existing approved Wikipedia coordinate-to-footprint decisions for Widener,
  Houghton, Sever, Boylston, Harvard, Holden, Holworthy, and related buildings

## Applied name matches

| Hail record | Building | Harvard/Cambridge address | Footprint(s) |
|---|---|---|---|
| `cambridge-st_1800_2` | Canaday Hall complex | 22 Harvard Yard | `318-1`, `318-9`, `318-10` |
| `cambridge-st_1800_4` | Memorial Church | 23 Harvard Yard | `318-13` |
| `cambridge-st_1820` | Thayer Hall | 21 Harvard Yard | `318-2` |
| `massachusetts-ave_1251-1339` | Wigglesworth Hall complex | 6 Harvard Yard | `318-32`, `318-36` |
| `massachusetts-ave_1285` | Widener Library | 31 Harvard Yard | `318-24` |
| `massachusetts-ave_1405_4` | Lehman Hall | 8 Harvard Yard | `318-25` |
| `massachusetts-ave_1425r` | Weld Hall | 3 Harvard Yard | `318-22` |
| `massachusetts-ave_1435_2` | Straus Hall | 10 Harvard Yard | `318-20` |
| `massachusetts-ave_1435r` | Matthews Hall | 9 Harvard Yard | `318-21` |
| `massachusetts-ave_1445_2` | Massachusetts Hall | 11 Harvard Yard | `318-18` |
| `massachusetts-ave_1451r` | University Hall | 1 Harvard Yard | `318-16` |
| `massachusetts-ave_1465` | Lionel Hall | 14 Harvard Yard | `318-11` |
| `massachusetts-ave_1485` | Mower Hall | 16 Harvard Yard | `318-5` |
| `massachusetts-ave_1495_2` | Phillips Brooks House | 18 Harvard Yard | `318-4` |
| `quincy-st_13` | Houghton Library | 29 Harvard Yard | `318-30` |
| `quincy-st_15` | Pusey Library | 27 Harvard Yard | `318-8` |
| `quincy-st_25_2` | Emerson Hall | 19 Quincy Street | `318-23` |
| `quincy-st_31_2` | Sever Hall | 25 Harvard Yard | `318-17` |
| `quincy-st_37_2` | Robinson Hall | 35 Quincy Street | `318-15` |

The existing Massachusetts Hall assignment was corrected from `318-20`
(10 Harvard Yard, Straus Hall) to `318-18` (11 Harvard Yard).

## Corrected source classifications

The Hail scraper incorrectly classified `cambridge-st_1800_4` (Memorial
Church) and `massachusetts-ave_1451r` (University Hall) as razed. Both source
rows were corrected to `razed=false` and `Current building` before their Yard
footprint matches were applied.

After applying the crosswalk, all 32 `318-*` footprints have at least one
accepted Hail association.

The assessor assigns the same year, 1850, to every `318-*` footprint. The data
build treats this as a parcel-level placeholder and uses each footprint's
single accepted Hail construction year for display. The original assessor year,
source difference, and review flag remain in the output for auditing.
