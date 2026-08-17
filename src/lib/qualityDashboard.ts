import "server-only"

import { readFileSync } from "node:fs"
import path from "node:path"

type BuildingProperties = {
  assessor_record_count?: number | null
  hail_match_count?: number | null
  wikipedia_article_count?: number | null
  hail_architect?: string | null
  hail_builder?: string | null
  hail_building_name?: string | null
  age_band?: string | null
  year_difference_hail_assessor?: number | null
}

type FeatureCollection = { features: Array<{ properties?: BuildingProperties }> }
export type DashboardDatum = { label: string; count: number; percent: number; color: string }
export type AgeMetadataRow = { label: string; total: number; counts: number[]; percents: number[] }
export type QualityDashboardData = {
  generatedAt: string
  footprintTotal: number
  sourceCoverage: DashboardDatum[]
  ageMetadata: AgeMetadataRow[]
  hail: {
    eligibleTotal: number
    excludedTotal: number
    sourceArtifactTotal: number
    outcomes: DashboardDatum[]
  }
  footprintDiagnostics: {
    multipleAssessorRecords: number
    multipleHailRecords: number
    multipleEitherSource: number
    comparableConstructionYears: number
    constructionYearDifferenceOver50: number
    constructionYearDifferenceDistribution: DashboardDatum[]
  }
}

const AGE_ORDER = ["pre-1780", "1780_1820", "1820_1850", "1850_1880", "1880-1900", "1900-1930", "1930-1980", "1980-present", "unknown"]
const AGE_LABELS: Record<string, string> = {
  "pre-1780": "Before 1780", "1780_1820": "1780–1820", "1820_1850": "1820–1850",
  "1850_1880": "1850–1880", "1880-1900": "1880–1900", "1900-1930": "1900–1930",
  "1930-1980": "1930–1980", "1980-present": "1980–present", unknown: "Unknown age",
}
const SOURCE_COLORS: Record<string, string> = {
  "No data source": "#d8d4cc", "Assessor only": "#bdd7d0", "Assessor + Hail": "#4f9184",
  "Assessor + Wikipedia": "#d8a85b", "All three sources": "#c85b3c", "Other combinations": "#745b80",
}
const HAIL_COLORS = ["#337968", "#dc9a3d", "#b9543c"]
const YEAR_DIFFERENCE_BINS = [
  { label: "51–75 years", minimum: 51, maximum: 75, color: "#d7b26d" },
  { label: "76–100 years", minimum: 76, maximum: 100, color: "#cf8a52" },
  { label: "101–125 years", minimum: 101, maximum: 125, color: "#c56845" },
  { label: "126–150 years", minimum: 126, maximum: 150, color: "#ad4e3d" },
  { label: "151–175 years", minimum: 151, maximum: 175, color: "#813f3b" },
  { label: "176+ years", minimum: 176, maximum: Number.POSITIVE_INFINITY, color: "#57343a" },
]

function asCount(value: unknown) { const parsed = Number(value); return Number.isFinite(parsed) ? parsed : 0 }
function present(value: unknown) { return typeof value === "string" ? value.trim().length > 0 : Boolean(value) }
function percent(count: number, total: number) { return total === 0 ? 0 : (count / total) * 100 }

function parseCsv(text: string): string[][] {
  const rows: string[][] = []; let row: string[] = []; let field = ""; let quoted = false
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index]
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') { field += '"'; index += 1 }
      else if (character === '"') quoted = false
      else field += character
    } else if (character === '"') quoted = true
    else if (character === ",") { row.push(field); field = "" }
    else if (character === "\n") { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = "" }
    else field += character
  }
  if (field || row.length) { row.push(field.replace(/\r$/, "")); rows.push(row) }
  return rows
}

export function getQualityDashboardData(): QualityDashboardData {
  const root = process.cwd()
  const buildingsPath = path.join(root, "public/data/cambridge-buildings.geojson")
  const hailPath = path.join(root, "data/processed/hail-address-matches.csv")
  const buildings = JSON.parse(readFileSync(buildingsPath, "utf8")) as FeatureCollection
  const sourceCounts = new Map<string, number>(); const ageCounts = new Map<string, number[]>()
  let multipleAssessorRecords = 0
  let multipleHailRecords = 0
  let multipleEitherSource = 0
  const constructionYearDifferences: number[] = []

  for (const feature of buildings.features) {
    const properties = feature.properties ?? {}
    const assessorRecordCount = asCount(properties.assessor_record_count)
    const hailRecordCount = asCount(properties.hail_match_count)
    const assessor = assessorRecordCount > 0
    const hail = hailRecordCount > 0
    const wikipedia = asCount(properties.wikipedia_article_count) > 0
    let sourceLabel = "Other combinations"
    if (!assessor && !hail && !wikipedia) sourceLabel = "No data source"
    else if (assessor && !hail && !wikipedia) sourceLabel = "Assessor only"
    else if (assessor && hail && !wikipedia) sourceLabel = "Assessor + Hail"
    else if (assessor && !hail && wikipedia) sourceLabel = "Assessor + Wikipedia"
    else if (assessor && hail && wikipedia) sourceLabel = "All three sources"
    sourceCounts.set(sourceLabel, (sourceCounts.get(sourceLabel) ?? 0) + 1)

    if (assessorRecordCount > 1) multipleAssessorRecords += 1
    if (hailRecordCount > 1) multipleHailRecords += 1
    if (assessorRecordCount > 1 || hailRecordCount > 1) multipleEitherSource += 1
    const yearDifference = properties.year_difference_hail_assessor
    if (typeof yearDifference === "number" && Number.isFinite(yearDifference)) {
      constructionYearDifferences.push(yearDifference)
    }

    const metadataCount = [properties.hail_architect, properties.hail_builder, properties.hail_building_name, wikipedia].filter(present).length
    const ageBand = properties.age_band || "unknown"
    const distribution = ageCounts.get(ageBand) ?? [0, 0, 0, 0, 0]
    distribution[metadataCount] += 1; ageCounts.set(ageBand, distribution)
  }

  const footprintTotal = buildings.features.length
  const sourceCoverage = ["No data source", "Assessor only", "Assessor + Hail", "Assessor + Wikipedia", "All three sources", "Other combinations"]
    .map((label) => ({ label, count: sourceCounts.get(label) ?? 0, percent: percent(sourceCounts.get(label) ?? 0, footprintTotal), color: SOURCE_COLORS[label] }))
    .filter((item) => item.count > 0)
  const ageMetadata = AGE_ORDER.map((ageBand) => {
    const counts = ageCounts.get(ageBand) ?? [0, 0, 0, 0, 0]; const total = counts.reduce((sum, count) => sum + count, 0)
    return { label: AGE_LABELS[ageBand] ?? ageBand, total, counts, percents: counts.map((count) => percent(count, total)) }
  }).filter((row) => row.total > 0)

  const hailRows = parseCsv(readFileSync(hailPath, "utf8")); const header = hailRows[0] ?? []
  const statusIndex = header.indexOf("match_status")
  const overrideDecisionIndex = header.indexOf("override_decision")
  if (statusIndex < 0 || overrideDecisionIndex < 0) {
    throw new Error("Hail match audit is missing match_status or override_decision")
  }
  const hailCounts = new Map<string, number>()
  let sourceArtifactTotal = 0
  for (const row of hailRows.slice(1)) {
    if (row[overrideDecisionIndex] === "no_map_match") {
      sourceArtifactTotal += 1
      continue
    }
    const status = row[statusIndex]
    if (status) hailCounts.set(status, (hailCounts.get(status) ?? 0) + 1)
  }
  const eligibleTotal = ["accepted", "review", "unmatched"].reduce((sum, status) => sum + (hailCounts.get(status) ?? 0), 0)
  const hailLabels: Array<[string, string]> = [["accepted", "Confirmed on footprint"], ["review", "Ambiguous · pending review"], ["unmatched", "No footprint · pending review"]]
  const differencesOver50 = constructionYearDifferences.filter((difference) => difference > 50)

  return {
    generatedAt: new Date().toISOString(), footprintTotal, sourceCoverage, ageMetadata,
    hail: {
      eligibleTotal,
      excludedTotal: hailCounts.get("excluded") ?? 0,
      sourceArtifactTotal,
      outcomes: hailLabels.map(([status, label], index) => { const count = hailCounts.get(status) ?? 0; return { label, count, percent: percent(count, eligibleTotal), color: HAIL_COLORS[index] } }),
    },
    footprintDiagnostics: {
      multipleAssessorRecords,
      multipleHailRecords,
      multipleEitherSource,
      comparableConstructionYears: constructionYearDifferences.length,
      constructionYearDifferenceOver50: differencesOver50.length,
      constructionYearDifferenceDistribution: YEAR_DIFFERENCE_BINS.map((bin) => {
        const count = differencesOver50.filter(
          (difference) => difference >= bin.minimum && difference <= bin.maximum,
        ).length
        return { label: bin.label, count, percent: percent(count, differencesOver50.length), color: bin.color }
      }),
    },
  }
}
