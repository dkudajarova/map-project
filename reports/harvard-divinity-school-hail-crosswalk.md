# Harvard Divinity School Hail crosswalk

Generated: 2026-08-29

## Method

The Divinity School campus is matched by historic building name and position,
with current Harvard addresses used to confirm the campus boundary. This is
especially important at 45 Francis Avenue, where Cambridge assigns one current
address to both Swartz Hall and the attached HDS Library wing, while Hail lists
the two components separately under their historic names and addresses.

Primary Harvard sources:

- Harvard Divinity School, [campus map and directions](https://www.hds.harvard.edu/about/map-and-directions)
- Harvard Divinity School, [campus map PDF](https://www.hds.harvard.edu/resource/2021-hds-campus-mappdf)
- Harvard Divinity School, [bicentennial campus history](https://www.hds.harvard.edu/about/history-and-mission/hds-bicentennial)
- Harvard Planning, [Swartz Hall (formerly Andover Hall)](https://harvardplanning.emuseum.com/sites/366/andover-hall)
- Harvard Planning, [Divinity Hall](https://harvardplanning.emuseum.com/sites/317/divinity-hall)
- Harvard Planning, [Center for the Study of World Religions](https://harvardplanning.emuseum.com/sites/310/center-for-the-study-of-world-religions)

## Applied correction

| Hail record | Building | Current address | Footprint |
|---|---|---|---|
| `francis-ave_43` | Andover-Harvard Theological Library / HDS Library wing | 45 Francis Avenue | `241-2` |
| `francis-ave_45` | Andover Hall / Swartz Hall | 45 Francis Avenue | `241-5` |

The correction separates the two records that the address matcher could not
distinguish: the 1910 Andover Hall record is restricted to the main Swartz Hall
footprint, and the 1960 library record is assigned to its attached wing.

## Confirmed existing matches

| Hail record | Building | Current address | Footprint |
|---|---|---|---|
| `divinity-ave_12` | Divinity Hall | 14 Divinity Avenue | `241-28` |
| `francis-ave_42` | Center for the Study of World Religions | 42 Francis Avenue | `237-7` |
| `francis-ave_44` | Jewett House | 44 Francis Avenue | `237-6` |
| `francis-ave_47` | Rockefeller Hall | 47 Francis Avenue | `241-1` |
| `francis-ave_56` | Carriage House | 56 Francis Avenue | `237-4` |

Hail describes the 56 Francis building as a 1914 garage. Harvard's history and
current campus map identify it as the Carriage House of Jewett House, now used
by the Women's Studies in Religion Program. The adjacent 1913 house at Hail's
44 Francis Avenue is Jewett House and was already correctly address-matched to
its distinct footprint, `237-6`.

## Parcel-year safeguard

Cambridge assigns assessor year 2007 to the four Divinity School footprints on
parcel 241: Rockefeller Hall, the HDS Library wing, Swartz Hall, and Divinity
Hall. As with the verified Oxford Street chemistry footprints on the same
parcel, 2007 is not the construction date of these surviving buildings. The
build exempts only these named footprints from its normal post-2003 replacement
building safeguard, allowing their accepted Hail records and historic years to
be published without weakening the safeguard for neighboring museum and
research buildings.
