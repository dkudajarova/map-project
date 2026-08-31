# MIT campus and One Kendall Square Hail crosswalk

Generated: 2026-08-31

## Scope and method

This crosswalk resolves Hail records that contain an explicit MIT building
number even when their historical street address no longer agrees with current
Cambridge Address Points. It also treats One Kendall Square as a multi-building
campus because its numbered buildings use a shared property address.

The principal source is MIT Facilities' public `MIT_BUILDINGS` GIS layer. It
publishes the MIT facility number, building name, street address, ownership,
floor count, construction date, and polygon geometry. Each MIT polygon was
projected to Massachusetts State Plane and compared with the Cambridge
footprint layer; the selected matches have direct, dominant geometric overlap.

Primary sources:

- MIT Facilities, [public MIT buildings GIS layer](https://maps.mit.edu/pub/rest/services/demos/Map/MapServer/24)
- MIT Office of Facilities Management and Stewardship, [how MIT buildings are numbered](https://web.mit.edu/ofms-space/www/textdocs/wbid.html)
- MIT Facilities, [leased-building address directory](https://web.mit.edu/facilities/services/non-facilities.html)
- MIT Facilities, [official campus map](https://web.mit.edu/facilities/maps/campusmap_index.pdf)
- Lyme Properties, [One Kendall Square adaptive-reuse history](https://www.lymeproperties.com/one-kendall-square)
- Alexandria Real Estate Equities, [2022 property listing](https://s2.q4cdn.com/884574073/files/doc_downloads/sec/2022-10-K.pdf)
- SAH Archipedia, [One Kendall Square / Boston Woven Hose](https://sah-archipedia.org/buildings/MA-01-CS2)

## MIT-number results

| Hail record | Hail designation | MIT facility | Cambridge footprint | Result |
|---|---|---|---|---|
| `ames-st_27` | Whitaker, Building 56 | 56 | `668-56` | Confirmed |
| `ames-st_27r` | Dorrance, Building 16 | 16 | `668-16` | Confirmed |
| `memorial-dr_150r` | Green Building | 54 | `668-54` | Confirmed |
| `memorial-dr_182-222` | Main Group, Buildings 1-4 and 10 | 1, 2, 3, 4, 10 | `668-1`, `668-2`, `668-3`, `668-4`, `668-10` | Confirmed multi-footprint record |
| `vassar-st_37` | Building 45 | 45 | `667-3` | Confirmed |
| `vassar-st_50_2` | Fairchild, Buildings 36 and 38 | 36, 38 | `668-36`, `668-38` | Corrected; removed Building 34 |
| `vassar-st_50r` | Compton, Building 26 | 26 | `668-26` | Corrected from Buildings 34/36/38 |
| `vassar-st_52` | Building 34 | 34 | `668-34` | Confirmed |
| `vassar-st_54r` | Building 24 | 24 | `668-24` | Confirmed |
| `vassar-st_60` | Microsystems Technology Laboratories | 39 | `668-39` | Corrected from shared-address group |
| `vassar-st_60r_2` | Chemical Engineering Laboratory | 12 | `668-12` | Corrected from shared-address group |
| `vassar-st_73` | Metals Processing Laboratory | 41 | `667-7` | Confirmed |

Existing matches for Buildings 14, 18, 31, 37, 42, 43, 48, 50, 51, 57, 66,
and 68 were checked against the same GIS layer and retained. Hail records for
suffix buildings absent from the current public layer, and buildings known to
have been razed, were not reassigned merely from proximity.

## One Kendall Square

MIT's public GIS identifies its leased facility `NE83` as **Building 300, One
Kendall Square**. Its polygon overlaps Cambridge footprint `557-8` by 95.5%,
providing an independent anchor between the complex numbering and Cambridge
geometry.

Hail's `hampshire-st_15` entry explicitly describes “15-29 & rear Kendall
Square One office park, 1983-1990.” Contemporary property listings identify
Buildings 100, 200, 300, 400, 500, 600/700, and 1400 as the operating campus
created during that period. The umbrella record is therefore attached to:

| One Kendall designation | Cambridge footprint |
|---|---|
| Building 100 | `557-6` |
| Building 200 | `557-18` |
| Building 300 / MIT `NE83` | `557-8` |
| Building 400 | `557-19` |
| Building 500 | `557-1` |
| Building 600/700 | `557-17` |
| Building 1400 | `557-16` |

Building 1000 (`557-5`) and the cinema/theater building (`417-28`) postdate the
office-park record's stated 1983-1990 period and are not included. The surviving
Boston Woven Hose factory records at 21, 25 rear, and 29 Hampshire Street remain
unresolved individually: the public MIT layer proves the campus anchor but does
not establish which reused industrial shell corresponds to each historical
factory address. Those require the 1944 factory plan or equivalent archival
footprint evidence before assignment.

## Broader coverage

The public MIT layer contains 172 facilities. A spatial audit found 161 MIT
facilities overlapping current Cambridge footprints, including 62 facilities
whose 68 intersecting footprints had no accepted Hail record before this batch.
This makes MIT facility identifiers a useful future matching key, but only Hail
records with an explicit building number or equally specific named-building
evidence were overridden here.
