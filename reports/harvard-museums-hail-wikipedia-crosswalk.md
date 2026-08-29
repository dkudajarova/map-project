# Harvard museums Hail and Wikipedia crosswalk

Generated: 2026-08-29

## Scope and method

This batch covers the Harvard Museums of Science & Culture locations around
Divinity Avenue and Oxford Street, together with collection buildings whose
Wikipedia decisions were entangled with the same parcel. Historic building
names, official Harvard addresses, and physical campus position control over a
raw article coordinate or shared parcel address.

Primary Harvard sources:

- Harvard Museums of Science & Culture, [four-museum wayfinding map](https://peabody.harvard.edu/sites/g/files/omnuum4921/files/peabody/files/hmsc_wayfinding_map_brochure_12-16-21_final-ua.pdf)
- Harvard University, [official campus map](https://www.map.harvard.edu/pdf/8.5x11%20Campus%20Map.pdf)
- Peabody Museum, [visitor information](https://peabody.harvard.edu/visit)
- Peabody Museum, [Peabody and HMNH floor map](https://peabody.harvard.edu/sites/g/files/omnuum4921/files/peabody/files/peabody_map_dec_15_2021-ua.pdf)
- Harvard Planning, [Peabody Museum](https://harvardplanning.emuseum.com/sites/695/peabody-museum)
- Harvard Library, [Harvard-Yenching Library history](https://library.harvard.edu/libraries/harvard-yenching-library/about)

## Hail results

| Hail record | Historic/current building | Footprint | Result |
|---|---|---|---|
| `divinity-ave_6_2` | Semitic Museum / Harvard Museum of the Ancient Near East | `241-43` | Confirmed |
| `divinity-ave_11_2` | Peabody Museum | `241-17` | Confirmed |
| `divinity-ave_11` | Moved school cross-reference | none | Removed from `241-17` |

The Peabody Museum and Ancient Near East records were already assigned to the
right footprints, but Cambridge's parcel-level assessor year 2007 suppressed
their Hail metadata. These two verified surviving museum footprints are now
explicit exceptions to that safeguard. The exception list also includes the
separately verified Yenching Library and University Herbaria footprints audited
with this batch.

The HMSC Collection of Historical Scientific Instruments is in the Science
Center at 1 Oxford Street. Hail has no separate building record for the
collection, so no Hail association was invented.

## Wikipedia review

### Confirmed shared footprint

The following four articles remain on `241-17`:

- Harvard Museum of Natural History
- Harvard Mineralogical Museum
- Museum of Comparative Zoology
- University Museum (Harvard University)

This is intentional. They describe institutions, collections, or the historic
building housed in the same connected University Museum structure. Assigning
them to neighboring MCZ laboratories or Tozzer Library merely to make the links
one-per-footprint would be geographically misleading.

### Corrected decisions

| Wikipedia article | Previous result | Correct footprint |
|---|---|---|
| Harvard-Yenching Library | `241-48` (Fairchild Laboratory) | `241-49`, 2 Divinity Avenue |
| Harvard University Herbaria | Rejected | `241-59`, 22 Divinity Avenue |
| Harvard Collection of Historical Scientific Instruments | Rejected | `266-18`, Science Center, 1 Oxford Street |

The Harvard Museum of the Ancient Near East article remains correctly assigned
to `241-43`. The Wikipedia snapshot contains no geotagged standalone Peabody
Museum article, so the build cannot publish a Peabody link without inventing a
snapshot record.
