# Campus building-popup year audit

Generated: 2026-08-29

## Scope

This audit covers the named footprints in the Harvard Law School, Oxford Street
science and engineering, Harvard Divinity School, and Harvard museums batches.
It reviews the popup-facing `year_built` value, not merely the presence of an
accepted Hail association.

## Corrections

- Cambridge assessor year `1840` is recognized as a parcel placeholder for the
  Harvard Law Graduate Commons (`253-*`) and the Law/Oxford campus parcel
  (`266-*`).
- The verified parcel-241 Hail exceptions now include Fairchild Laboratory as
  well as the previously reviewed Oxford, Divinity, museum, Yenching, and
  Herbaria footprints.
- The Carriage House's assessor value `1860` is treated as an inaccurate parcel
  value; its Hail construction year is `1914`.
- When a verified placeholder footprint has several Hail phase records, the
  popup uses the primary `Current building` record. This changes Divinity Hall
  from `2007` to `1825` and the Peabody/University Museum footprint from `2007`
  to the primary Peabody Museum year `1876`, while retaining all phase years in
  `hail_years` for audit.
- The popup no longer falls back to an assessor value marked as a placeholder
  when no Hail year is available.

## Verification result

Across the 39 distinct footprints named in the four batch reports:

- 37 publish a Hail construction year.
- LISE (`266-12`) publishes `Unknown`, because the Hail source predates the
  building and no construction record is available in the current inputs.
- The secondary footprint at 1515 Massachusetts Avenue (`266-15`) publishes
  `Unknown`; the Austin Hall record remains correctly restricted to `266-14`.

No reviewed footprint now publishes the assessor parcel placeholders `1840`,
`1860`, or `2007` as its popup construction date.
