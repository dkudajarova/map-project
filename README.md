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
development server is running. Choose a street, then review its Hail records
one at a time. Proposed footprints are orange, the selected footprint is blue,
and any visible neighboring footprint can be selected directly on the map.
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
