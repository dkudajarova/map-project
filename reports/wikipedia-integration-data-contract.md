# Wikipedia integration data contract

## Purpose

This contract defines the stable inputs and generated outputs used to associate
English Wikipedia articles with Cambridge building footprints. Wikipedia page
IDs identify articles and Cambridge `BldgID` values identify footprints.

The retrieval and matching implementation must reject malformed records rather
than silently coercing them.

## Canonical files

| Path | Owner | Versioned | Purpose |
|---|---|---:|---|
| `data/processed/wikipedia-articles.json` | retrieval script | yes | Latest successful API snapshot |
| `data/manual/wikipedia-building-decisions.json` | human reviewer | yes | Persistent approvals and rejections |
| `data/processed/wikipedia-building-candidates.csv` | matching script | yes | Complete match audit |
| `data/processed/wikipedia-matches-to-review.csv` | matching script | yes | Current unresolved review queue |
| `data/processed/cambridge-buildings-enriched.geojson` | building-data build | yes | Canonical map-ready building output |
| `public/data/cambridge-buildings.geojson` | building-data build | yes | Browser-facing copy |

The API snapshot lives under `data/processed/` because this repository ignores
all of `data/raw/`. It is nevertheless source evidence: downstream builds must
not modify it.

## Retrieval command

Wikimedia requires automated requests to identify the client and provide real
operator contact information. Supply that identity without committing it:

```bash
WIKIMEDIA_USER_AGENT='CambridgeBuildingMapWikipediaBot/1.0 (https://example.com/contact)' npm run wikipedia:update
```

The script also accepts `--user-agent`. It covers the checked-in Cambridge city
boundary with one-kilometer bounding-box queries, rejects any tile that reaches
MediaWiki's 500-result ceiling, clips returned coordinates to the boundary,
sorts records by page ID, and only replaces the prior snapshot after a complete
successful retrieval.

## Article snapshot

The snapshot is a JSON object with these top-level fields:

| Field | Type | Requirement |
|---|---|---|
| `schema_version` | integer | Currently `1` |
| `retrieved_at` | string | UTC ISO 8601 timestamp |
| `source` | object | API URL, language, and query type |
| `articles` | array | Records sorted by ascending page ID |

Each article contains:

| Field | Type | Requirement |
|---|---|---|
| `page_id` | positive integer | Stable article identifier; unique in snapshot |
| `title` | non-empty string | Title returned by MediaWiki |
| `url` | string | Canonical HTTPS `en.wikipedia.org` article URL |
| `latitude` | number | Between -90 and 90 |
| `longitude` | number | Between -180 and 180 |

The snapshot represents the latest *successful* complete retrieval. A failed or
partial retrieval must not replace it.

## Manual decisions

`wikipedia-building-decisions.json` is an object with `version: 1` and a
`decisions` array. A decision contains:

| Field | Type | Requirement |
|---|---|---|
| `wikipedia_page_id` | positive integer | Unique in the decision file |
| `decision` | string | `approved` or `rejected` |
| `bldgid` | string or null | Required and non-empty for `approved`; null for article-level rejection |
| `wikipedia_title` | string | Article title when reviewed |
| `wikipedia_url` | string | Article URL when reviewed |
| `latitude`, `longitude` | number | Article coordinate when reviewed |
| `selected_latitude`, `selected_longitude` | number or null | Reviewer-adjusted marker coordinate for an approval |
| `selection_method` | string or null | `generated_candidate` or `manual_marker` |
| `review_note` | string | May be empty |
| `reviewed_at` | string | UTC ISO 8601 timestamp |

Generated scripts may read this file but must never rewrite it. An approval is
reused only while the target `BldgID` exists and the generated match has not
materially changed. Otherwise the article returns to the review queue without
deleting the prior decision.

A coordinate move greater than five meters is material. Human decisions take
precedence over generated confidence while their evidence remains current.
Spatial confidence never grants publication approval: contained, nearest, and
unmatched records require an explicit human decision. A missing previously
reviewed page is emitted as a stale decision rather than deleted.

One Wikipedia article maps to at most one footprint in version 1. One footprint
may have any number of approved Wikipedia articles.

## Candidate and review tables

Both generated CSV files use the same columns:

| Column | Meaning |
|---|---|
| `wikipedia_page_id` | Stable article ID |
| `wikipedia_title` | Current snapshot title |
| `wikipedia_url` | Current canonical URL |
| `latitude`, `longitude` | Current article coordinate |
| `match_method` | `contained`, `nearest`, or `none` |
| `match_distance_meters` | Zero for contained matches; blank if unmatched |
| `candidate_count` | Number of candidates produced by the applicable pass |
| `candidate_bldgids` | Candidate IDs separated by `|` |
| `matched_bldgid` | Selected generated candidate, if unambiguous |
| `confidence_status` | `strong`, `ambiguous`, or `unmatched` |
| `decision_status` | `approved`, `rejected`, `needs_review`, or `stale_decision` |
| `review_reason` | Deterministic explanation of the status |
| `previous_title` | Prior title when it changed; otherwise blank |
| `previous_latitude`, `previous_longitude` | Prior coordinate when changed; otherwise blank |

The review CSV contains only `needs_review` and `stale_decision` rows. The
candidate CSV contains every current article, including rejected articles, so
it remains a complete audit.

Spatial matching uses GeoPandas and Shapely in Massachusetts Mainland State
Plane (`EPSG:26986`), whose units are meters. A coordinate intersecting exactly
one dissolved `BldgID` geometry is a strong contained candidate. Otherwise the
nearest footprint within 25 meters is recorded for manual review; more distant
coordinates are unmatched. The source footprint layer currently contains two
features for each of `114-3`, `129-7`, and `218-2`, so geometries are dissolved
by `BldgID` before matching.

## Public building properties

Approved articles are grouped by `BldgID` during the existing building-data
build. The browser-facing representation will be finalized during map
integration after verifying how MapLibre 6 exposes nested GeoJSON properties.
Regardless of encoding, it must preserve page ID, title, and URL for every
approved article and must support multiple articles per footprint.

## Fixtures

Representative version-1 fixtures live in `tests/fixtures/wikipedia/`. They
cover article snapshots, Polygon and MultiPolygon footprints, an approval, and
an article-level rejection. Later stages will extend them with boundary,
ambiguous, nearest, moved, renamed, and missing-page cases.
