import { promises as fs } from "node:fs"
import path from "node:path"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"

type OverrideDecision = "matched" | "no_map_match"

type ManualOverride = {
  building_id: string
  decision: OverrideDecision
  bldgid: string | null
  bldgids?: string[]
  street_name: string
  hail_address: string
  note: string
  reviewed_at: string
  original_match_stage?: string
  original_match_reason?: string
  review_reason_category?: string
  original_candidate_bldgids?: string[]
  selected_was_proposed?: boolean | null
}

type ReviewRecord = {
  building_id: string
  hail_address: string
  hail_street_name: string
  candidate_bldgids: string
  candidate_addresses: string
  hail?: Record<string, unknown>
  [key: string]: unknown
}

type ReviewBundle = {
  generated_at: string
  record_count: number
  records: ReviewRecord[]
}

type OverrideFile = {
  version: number
  overrides: ManualOverride[]
}

const projectRoot = process.cwd()
const reviewBundlePath = path.join(
  projectRoot,
  "data/processed/hail-manual-review.json",
)
const overridePath = path.join(
  projectRoot,
  "data/manual/hail-building-overrides.json",
)
const footprintPath = path.join(
  projectRoot,
  "cambridgegis_data/Basemap/Buildings/BASEMAP_Buildings.geojson",
)

let validBuildingIdsPromise: Promise<Set<string>> | null = null

async function readJson<T>(filePath: string): Promise<T> {
  return JSON.parse(await fs.readFile(filePath, "utf8")) as T
}

async function readOverrides(): Promise<OverrideFile> {
  try {
    return await readJson<OverrideFile>(overridePath)
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error
    return { version: 2, overrides: [] }
  }
}

async function validBuildingIds(): Promise<Set<string>> {
  if (!validBuildingIdsPromise) {
    validBuildingIdsPromise = readJson<{
      features: Array<{ properties?: { BldgID?: unknown } }>
    }>(footprintPath).then(
      (data) =>
        new Set(
          data.features
            .map((feature) => String(feature.properties?.BldgID ?? "").trim())
            .filter(Boolean),
        ),
    )
  }
  return validBuildingIdsPromise
}

async function writeOverrides(data: OverrideFile): Promise<void> {
  await fs.mkdir(path.dirname(overridePath), { recursive: true })
  const temporaryPath = `${overridePath}.${process.pid}.${Date.now()}.tmp`
  await fs.writeFile(temporaryPath, `${JSON.stringify(data, null, 2)}\n`, "utf8")
  await fs.rename(temporaryPath, overridePath)
}

function cleanString(value: unknown, maximumLength: number): string {
  return typeof value === "string" ? value.trim().slice(0, maximumLength) : ""
}

function cleanBuildingIds(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return [...new Set(value.map((item) => cleanString(item, 100)).filter(Boolean))]
}

function overrideBuildingIds(override: ManualOverride | undefined): string[] {
  if (!override || override.decision !== "matched") return []
  const ids = cleanBuildingIds(override.bldgids)
  return ids.length ? ids : override.bldgid ? [override.bldgid] : []
}

const priorityMetadataFields = [
  "building_type",
  "architect",
  "builder",
  "owner_at_construction",
  "historic_address",
  "stories",
  "summary_raw",
] as const

function reviewPriority(record: ReviewRecord) {
  const hail = record.hail ?? {}
  const yearText = String(hail.construction_year ?? record.construction_year ?? "")
  const year = /^\d{4}$/.test(yearText) ? Number(yearText) : null
  const metadataCount = priorityMetadataFields.filter(
    (field) => String(hail[field] ?? "").trim().length > 0,
  ).length
  return { year, metadataCount }
}

export async function GET() {
  try {
    const [bundle, overrideFile] = await Promise.all([
      readJson<ReviewBundle>(reviewBundlePath),
      readOverrides(),
    ])
    const overrideById = new Map(
      overrideFile.overrides.map((override) => [
        override.building_id,
        { ...override, bldgids: overrideBuildingIds(override) },
      ]),
    )
    const records = bundle.records
      .map((record) => {
        const priority = reviewPriority(record)
        return {
          ...record,
          override: overrideById.get(record.building_id) ?? null,
          priority_year: priority.year,
          priority_metadata_count: priority.metadataCount,
        }
      })
      .sort((left, right) => {
        if (left.priority_year === null && right.priority_year !== null) return 1
        if (left.priority_year !== null && right.priority_year === null) return -1
        if (left.priority_year !== right.priority_year) {
          return (left.priority_year ?? 0) - (right.priority_year ?? 0)
        }
        if (left.priority_metadata_count !== right.priority_metadata_count) {
          return right.priority_metadata_count - left.priority_metadata_count
        }
        return left.hail_address.localeCompare(right.hail_address)
      })

    return Response.json({
      generated_at: bundle.generated_at,
      total_review_records: bundle.record_count,
      override_count: overrideFile.overrides.length,
      records,
    })
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : String(error) },
      { status: 500 },
    )
  }
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as Record<string, unknown>
    const buildingId = cleanString(body.building_id, 200)
    const decision = cleanString(body.decision, 30) as OverrideDecision
    const requestedBuildingIds = cleanBuildingIds(body.bldgids)
    const legacyBuildingId = cleanString(body.bldgid, 100)
    const bldgids = requestedBuildingIds.length
      ? requestedBuildingIds
      : legacyBuildingId
        ? [legacyBuildingId]
        : []
    const note = cleanString(body.note, 2000)
    if (!buildingId || !["matched", "no_map_match"].includes(decision)) {
      return Response.json({ error: "Invalid building_id or decision" }, { status: 400 })
    }

    const [bundle, overrideFile] = await Promise.all([
      readJson<ReviewBundle>(reviewBundlePath),
      readOverrides(),
    ])
    const reviewRecord = bundle.records.find(
      (record) => record.building_id === buildingId,
    )
    const existing = overrideFile.overrides.find(
      (override) => override.building_id === buildingId,
    )
    if (!reviewRecord && !existing) {
      return Response.json({ error: "Hail record is not in the review queue" }, { status: 404 })
    }
    if (decision === "matched") {
      const validIds = await validBuildingIds()
      if (!bldgids.length || bldgids.some((id) => !validIds.has(id))) {
        return Response.json({ error: "Select one or more valid footprint BldgIDs" }, { status: 400 })
      }
    }

    const override: ManualOverride = {
      building_id: buildingId,
      decision,
      bldgid: decision === "matched" ? bldgids[0] : null,
      bldgids: decision === "matched" ? bldgids : [],
      street_name:
        String(reviewRecord?.hail_street_name ?? existing?.street_name ?? ""),
      hail_address: String(
        reviewRecord?.hail_address ?? existing?.hail_address ?? "",
      ),
      note,
      reviewed_at: new Date().toISOString(),
      original_match_stage: String(
        reviewRecord?.match_stage ?? existing?.original_match_stage ?? "",
      ),
      original_match_reason: String(
        reviewRecord?.match_reason ?? existing?.original_match_reason ?? "",
      ),
      review_reason_category: String(
        reviewRecord?.review_reason_category ??
          existing?.review_reason_category ??
          "",
      ),
      original_candidate_bldgids: reviewRecord
        ? String(reviewRecord.candidate_bldgids ?? "")
            .split("|")
            .map((candidate) => candidate.trim())
            .filter(Boolean)
        : (existing?.original_candidate_bldgids ?? []),
      selected_was_proposed:
        decision === "matched"
          ? reviewRecord
            ? bldgids.every((id) =>
                String(reviewRecord.candidate_bldgids ?? "")
                  .split("|")
                  .includes(id),
              )
            : (existing?.selected_was_proposed ?? null)
          : null,
    }
    const overrides = overrideFile.overrides.filter(
      (item) => item.building_id !== buildingId,
    )
    overrides.push(override)
    overrides.sort((left, right) =>
      `${left.street_name}\u0000${left.hail_address}\u0000${left.building_id}`.localeCompare(
        `${right.street_name}\u0000${right.hail_address}\u0000${right.building_id}`,
      ),
    )
    await writeOverrides({ version: Math.max(overrideFile.version, 2), overrides })
    return Response.json({
      ok: true,
      override: { ...override, bldgids: overrideBuildingIds(override) },
      override_count: overrides.length,
    })
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : String(error) },
      { status: 500 },
    )
  }
}

export async function DELETE(request: Request) {
  try {
    const body = (await request.json()) as Record<string, unknown>
    const buildingId = cleanString(body.building_id, 200)
    if (!buildingId) {
      return Response.json({ error: "Invalid building_id" }, { status: 400 })
    }
    const overrideFile = await readOverrides()
    const overrides = overrideFile.overrides.filter(
      (item) => item.building_id !== buildingId,
    )
    await writeOverrides({ version: Math.max(overrideFile.version, 2), overrides })
    return Response.json({ ok: true, override_count: overrides.length })
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : String(error) },
      { status: 500 },
    )
  }
}
