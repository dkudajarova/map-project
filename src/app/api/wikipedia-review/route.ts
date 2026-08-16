import { promises as fs } from "node:fs"
import path from "node:path"
import { requireInternalTools } from "@/lib/internalTools"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"

type ReviewRecord = Record<string, string>
type Decision = {
  wikipedia_page_id: number
  decision: "approved" | "rejected"
  bldgid: string | null
  wikipedia_title: string
  wikipedia_url: string
  latitude: number
  longitude: number
  selected_latitude?: number | null
  selected_longitude?: number | null
  selection_method?: "generated_candidate" | "manual_marker" | null
  review_note: string
  reviewed_at: string
}

const projectRoot = process.cwd()
const reviewPath = path.join(projectRoot, "data/processed/wikipedia-matches-to-review.csv")
const decisionsPath = path.join(projectRoot, "data/manual/wikipedia-building-decisions.json")
const footprintPath = path.join(projectRoot, "cambridgegis_data/Basemap/Buildings/BASEMAP_Buildings.geojson")
const historicPattern = /\b(house|hall|church|chapel|library|school|theat(?:er|re)|museum|building|tower|observatory|club|center|centre|institute|station|historic district|cottages?|arsenal|armory|factory|laboratory|boathouse|synagogue|temple)\b/i

function parseCsv(text: string): ReviewRecord[] {
  const rows: string[][] = []
  let row: string[] = [], field = "", quoted = false
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index]
    if (quoted && character === '"' && text[index + 1] === '"') { field += '"'; index += 1 }
    else if (character === '"') quoted = !quoted
    else if (character === "," && !quoted) { row.push(field); field = "" }
    else if ((character === "\n" || character === "\r") && !quoted) {
      if (character === "\r" && text[index + 1] === "\n") index += 1
      row.push(field); if (row.some(Boolean)) rows.push(row); row = []; field = ""
    } else field += character
  }
  if (field || row.length) { row.push(field); rows.push(row) }
  const [headers = [], ...values] = rows
  return values.map((valuesRow) => Object.fromEntries(headers.map((header, index) => [header, valuesRow[index] ?? ""])))
}

async function readDecisions(): Promise<{ version: 1; decisions: Decision[] }> {
  try {
    return JSON.parse(await fs.readFile(decisionsPath, "utf8"))
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error
    return { version: 1, decisions: [] }
  }
}

async function writeDecisions(data: { version: 1; decisions: Decision[] }) {
  const temporaryPath = `${decisionsPath}.${process.pid}.${Date.now()}.tmp`
  await fs.writeFile(temporaryPath, `${JSON.stringify(data, null, 2)}\n`, "utf8")
  await fs.rename(temporaryPath, decisionsPath)
}

let validBuildingIdsPromise: Promise<Set<string>> | null = null
function validBuildingIds() {
  if (!validBuildingIdsPromise) {
    validBuildingIdsPromise = fs.readFile(footprintPath, "utf8").then((text) => {
      const data = JSON.parse(text) as { features: Array<{ properties?: { BldgID?: unknown } }> }
      return new Set(data.features.map((feature) => String(feature.properties?.BldgID ?? "").trim()).filter(Boolean))
    })
  }
  return validBuildingIdsPromise
}

export async function GET() {
  requireInternalTools()

  try {
    const [csv, decisionFile] = await Promise.all([fs.readFile(reviewPath, "utf8"), readDecisions()])
    const decisionById = new Map(decisionFile.decisions.map((decision) => [decision.wikipedia_page_id, decision]))
    const records = parseCsv(csv).map((record) => ({
      ...record,
      wikipedia_page_id: Number(record.wikipedia_page_id),
      latitude: Number(record.latitude),
      longitude: Number(record.longitude),
      match_distance_meters: record.match_distance_meters ? Number(record.match_distance_meters) : null,
      wikipedia_title: record.wikipedia_title,
      confidence_status: record.confidence_status,
      historic_candidate: historicPattern.test(record.wikipedia_title),
      decision: decisionById.get(Number(record.wikipedia_page_id)) ?? null,
    })).sort((left, right) => {
      if (left.historic_candidate !== right.historic_candidate) return left.historic_candidate ? -1 : 1
      const rank = { strong: 0, ambiguous: 1, unmatched: 2 } as const
      const difference = (rank[left["confidence_status"] as keyof typeof rank] ?? 3) - (rank[right["confidence_status"] as keyof typeof rank] ?? 3)
      return difference || String(left["wikipedia_title"]).localeCompare(String(right["wikipedia_title"]))
    })
    return Response.json({ records, decision_count: decisionFile.decisions.length })
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : String(error) }, { status: 500 })
  }
}

export async function POST(request: Request) {
  requireInternalTools()

  try {
    const body = await request.json() as Record<string, unknown>
    const pageId = Number(body.wikipedia_page_id)
    const decision = body.decision
    const bldgid = typeof body.bldgid === "string" ? body.bldgid.trim().slice(0, 100) : ""
    const selectedLatitude = Number(body.selected_latitude)
    const selectedLongitude = Number(body.selected_longitude)
    const selectionMethod = body.selection_method === "manual_marker" ? "manual_marker" : "generated_candidate"
    const note = typeof body.review_note === "string" ? body.review_note.trim().slice(0, 2000) : ""
    if (!Number.isInteger(pageId) || !["approved", "rejected"].includes(String(decision))) {
      return Response.json({ error: "Invalid page ID or decision" }, { status: 400 })
    }
    const records = parseCsv(await fs.readFile(reviewPath, "utf8"))
    const record = records.find((item) => Number(item.wikipedia_page_id) === pageId)
    if (!record) return Response.json({ error: "Article is not in the review queue" }, { status: 404 })
    if (decision === "approved") {
      const validIds = await validBuildingIds()
      const validCoordinate = Number.isFinite(selectedLatitude) && Number.isFinite(selectedLongitude)
        && selectedLatitude >= 42.34 && selectedLatitude <= 42.41
        && selectedLongitude >= -71.17 && selectedLongitude <= -71.05
      if (!bldgid || !validIds.has(bldgid) || !validCoordinate) {
        return Response.json({ error: "Place the marker on a valid Cambridge building before approving" }, { status: 400 })
      }
    }
    const decisionFile = await readDecisions()
    const saved: Decision = {
      wikipedia_page_id: pageId,
      decision: decision as Decision["decision"],
      bldgid: decision === "approved" ? bldgid : null,
      wikipedia_title: record.wikipedia_title,
      wikipedia_url: record.wikipedia_url,
      latitude: Number(record.latitude),
      longitude: Number(record.longitude),
      selected_latitude: decision === "approved" ? selectedLatitude : null,
      selected_longitude: decision === "approved" ? selectedLongitude : null,
      selection_method: decision === "approved" ? selectionMethod : null,
      review_note: note,
      reviewed_at: new Date().toISOString(),
    }
    const decisions = decisionFile.decisions.filter((item) => item.wikipedia_page_id !== pageId)
    decisions.push(saved)
    decisions.sort((left, right) => left.wikipedia_page_id - right.wikipedia_page_id)
    await writeDecisions({ version: 1, decisions })
    return Response.json({ ok: true, decision: saved, decision_count: decisions.length })
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : String(error) }, { status: 500 })
  }
}
