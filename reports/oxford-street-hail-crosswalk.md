# Oxford Street science and engineering Hail crosswalk

Generated: 2026-08-29

## Method

The Oxford Street precinct is matched by building name and physical campus
position rather than current street number alone. Harvard has renumbered
several physics and engineering buildings, while four distinct chemistry
footprints share the current address 12 Oxford Street.

Primary Harvard sources:

- Harvard Planning, [Fanny Peabody Mason Music Building and Paine Hall](https://harvardplanning.emuseum.com/sites/330/fanny-peabody-mason-music-building)
- Harvard Planning, [Jefferson Laboratory](https://harvardplanning.emuseum.com/sites/326/jefferson-laboratory)
- Harvard Planning, [Lyman Laboratory](https://harvardplanning.emuseum.com/sites/335/lyman-laboratory)
- Harvard Planning, [Pierce Hall](https://harvardplanning.emuseum.com/sites/435/pierce-hall)
- Harvard Planning, [Conant Chemistry Laboratory](https://harvardplanning.emuseum.com/sites/details/313B/conant-chemistry-laboratory)
- Harvard Planning, [Mallinckrodt Chemistry Laboratory](https://harvardplanning.emuseum.com/sites/details/313C/mallinckrodt-chemistry-laboratory)
- Harvard Planning, [Converse Chemistry Laboratory](https://harvardplanning.emuseum.com/sites/details/313A/converse-chemistry-laboratory)
- Harvard Planning, [Naito Laboratory](https://harvardplanning.emuseum.com/sites/195/naito)
- Harvard Planning, [Mallinckrodt-Hoffman Link](https://harvardplanning.emuseum.com/sites/309/mallinckrodthoffman-link)
- Harvard SEAS, [Oxford Street precinct map](https://seas.harvard.edu/sites/default/files/2019-11/HolidayLecture2019_Map.pdf)

## Applied name matches and corrections

| Hail record | Building | Current address | Footprint |
|---|---|---|---|
| `oxford-st_7r` | John Knowles Paine Hall / Music Building | 3 Oxford Street | `266-13` |
| `oxford-st_10_2` | Conant Chemistry Laboratory | 12 Oxford Street | `241-8` |
| `oxford-st_11` | Jefferson Physical Laboratory | 17 Oxford Street | `266-21` |
| `oxford-st_12_2` | Mallinckrodt Chemistry Laboratory | 12 Oxford Street | `241-45` |
| `oxford-st_12r` | Converse Memorial Laboratory | 12 Oxford Street | `241-4` |
| `oxford-st_14r` | Naito Laboratory | 12 Oxford Street | `241-10` |
| `oxford-st_15r` | Lyman Laboratory | 17 Oxford Street | `266-9` |
| `oxford-st_16_2` | Mallinckrodt-Hoffman Link | 18 Oxford Street | `241-41` |
| `oxford-st_29` | Pierce Hall | 25/29 Oxford Street | `266-7` |

## Confirmed existing matches

The address-based assignments for the Science Center (`266-18`), Gordon McKay
Laboratory (`266-16`), Cruft Laboratory (`266-5`), Hoffman Laboratory
(`241-47`), and Maxwell Dworkin (`266-2`) already resolve to the correct named
footprints.

The Hail dataset predates the Laboratory for Integrated Science and Engineering
(LISE), whose current 11 Oxford Street footprint is `266-12`. The Jefferson
record previously attached there was moved to Jefferson's `266-21` footprint.

Cambridge assigns the same assessor year, 2007, to the six addressed chemistry
complex footprints. This is a parcel-level placeholder rather than the
construction date of Conant, Converse, Mallinckrodt, Naito, the
Mallinckrodt-Hoffman Link, or Hoffman. The data build preserves its normal
post-2003 replacement-building safeguard but exempts these six verified
footprints so their accepted Hail associations and individual construction
years are published.
