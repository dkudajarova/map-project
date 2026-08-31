This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Manual Hail review

Open [http://localhost:3000/review](http://localhost:3000/review) while the
development server is running. Review records in the global priority queue,
which orders the oldest known construction years first and breaks ties by
metadata completeness. Proposed footprints are orange, selected footprints are blue,
and any number of proposed or visible neighboring footprints can be toggled
directly on the map and saved against the same Hail record.
You can also record **No map match**.

The review API writes decisions only to
`data/manual/hail-building-overrides.json`; it does not edit any source
dataset. To layer saved decisions onto the generated Cambridge footprint map
and then summarize the review evidence, run:

```bash
npm run data:build
npm run overrides:analyze
```

The analysis is written to `reports/manual-override-analysis.md`. It reports
how often proposed candidates, neighboring footprints, and no-match decisions
were selected, and identifies repeated outcomes that may justify a future
deterministic rule. File writes are intended for a local Node server; a
read-only or ephemeral deployment will not persist review decisions.

## Wikipedia review

After running `npm run wikipedia:update` and `npm run wikipedia:match`, open
[http://localhost:3000/wikipedia-review](http://localhost:3000/wikipedia-review).
The workspace starts with a title-based historic-building shortlist and can be
switched to all candidates. Decisions are written only to
`data/manual/wikipedia-building-decisions.json`. Run `npm run wikipedia:match`
again to apply saved decisions to the generated audit and review queue.

## Building data

Rebuild the footprint-master map database with Cambridge Address Points,
assessor records, and staged Hail matches:

```bash
npm run data:build
```

The map reads `public/data/cambridge-buildings.geojson`. The canonical processed
copy, complete Hail match audit, and manual-review queue are written under
`data/processed/`. See
[`reports/building-database-methodology.md`](reports/building-database-methodology.md)
for matching stages, year-selection rules, output fields, and current counts.

### Cambridge Development Log

Source snapshots belong in `data/raw/development-logs/`. The build reads the
newest filename for each supported table, admits only projects whose status is
exactly `Complete` and whose `Year Complete` is filled and valid (1997 through
the current year), and matches them to footprints by map-lot, exact address, or
a conservative coordinate join. A matched completion year is the primary
source for `year_built`, ahead of the Assessor, Hail, and MIT fields, so it
controls both polygon color and popup content.

Refresh the two quarterly Open Data tables and rebuild with:

```bash
npm run development-logs:update
npm run data:build
```

The refresh command writes date-stamped, immutable CSV snapshots using the
official Cambridge Socrata datasets (`wjwg-93qh` for the current edition and
`a5ud-8kjv` for historical projects). The map-lot-enhanced export supplied for
this project remains the preferred duplicate when present. Review the build's
match summary before publishing; unmatched records remain inert instead of
being assigned to a questionable footprint.

## Admin-managed building fun facts

Published fun facts live in `data/manual/building-fun-facts.json`, separately
from source datasets and generated files. Each entry is keyed by footprint
`bldgid` and contains the admin-approved text plus source provenance:

```json
{
  "bldgid": "123-4",
  "text": "A concise fact approved by the app administrator.",
  "source": {
    "type": "wikipedia",
    "label": "Wikipedia: Example Building",
    "record_id": "123456",
    "url": "https://en.wikipedia.org/wiki/Example_Building"
  },
  "reviewed_at": "2026-08-17T12:00:00Z"
}
```

`source.type` accepts stable lowercase identifiers such as `wikipedia`, `hail`,
or a future dataset name. Suggested or AI-generated text should be added only
after admin review. Run `npm run data:build` to validate the file and publish
approved values to the footprint GeoJSON. Popups display the fact and its
source; an invalid/duplicate footprint ID, oversized fact, malformed source,
or unsafe source URL fails the build instead of publishing questionable data.

You can start editing the page by modifying `src/app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
