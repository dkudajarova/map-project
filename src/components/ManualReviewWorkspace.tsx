"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import * as maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import type {
  Feature,
  FeatureCollection,
  MultiPolygon,
  Polygon,
} from "geojson"

type ManualOverride = {
  building_id: string
  decision: "matched" | "no_map_match"
  bldgid: string | null
  bldgids?: string[]
  note: string
  reviewed_at: string
}

type HailDetails = {
  building_id: string
  street_name: string
  address_raw: string
  normalized_address: string
  historic_address: string
  building_type: string
  stories: string
  construction_year: string
  architect: string
  builder: string
  owner_at_construction: string
  classification: string
  summary_raw: string
  source_page: string
}

type ReviewRecord = {
  building_id: string
  hail_address: string
  hail_street_name: string
  classification: string
  construction_year: string
  match_stage: string
  candidate_bldgids: string
  candidate_addresses: string
  candidate_street_names: string
  match_reason: string
  review_reason_summary: string
  priority_year: number | null
  priority_metadata_count: number
  hail: HailDetails
  override: ManualOverride | null
}

type ReviewResponse = {
  generated_at: string
  total_review_records: number
  override_count: number
  queue: "ambiguous" | "unmatched"
  queue_counts: { ambiguous: number; unmatched: number }
  records: ReviewRecord[]
  error?: string
}

type FootprintProperties = {
  BldgID?: string | null
  Address?: string | null
  addresses?: string | null
  year_built?: number | null
  [key: string]: unknown
}

type FootprintCollection = FeatureCollection<
  Polygon | MultiPolygon,
  FootprintProperties
>

const sourceId = "manual-review-buildings"
const baseFillId = "manual-review-base"
const outlineId = "manual-review-outline"
const candidateFillId = "manual-review-candidates"
const selectedFillId = "manual-review-selected"
const labelId = "manual-review-labels"
const svgMapWidth = 1000
const svgMapHeight = 700

function candidateIds(record: ReviewRecord | undefined): string[] {
  return record?.candidate_bldgids.split("|").filter(Boolean) ?? []
}

function overrideBuildingIds(override: ManualOverride | null | undefined): string[] {
  if (!override || override.decision !== "matched") return []
  return override.bldgids?.length
    ? override.bldgids
    : override.bldgid
      ? [override.bldgid]
      : []
}

function collectCoordinates(value: unknown, coordinates: Array<[number, number]>) {
  if (!Array.isArray(value)) return
  if (
    value.length >= 2 &&
    typeof value[0] === "number" &&
    typeof value[1] === "number"
  ) {
    coordinates.push([value[0], value[1]])
    return
  }
  for (const child of value) collectCoordinates(child, coordinates)
}

function boundsForFeatures(
  features: Array<Feature<Polygon | MultiPolygon, FootprintProperties>>,
): maplibregl.LngLatBounds | null {
  const coordinates: Array<[number, number]> = []
  for (const feature of features) {
    collectCoordinates(feature.geometry?.coordinates, coordinates)
  }
  if (!coordinates.length) return null
  const bounds = new maplibregl.LngLatBounds(coordinates[0], coordinates[0])
  for (const coordinate of coordinates.slice(1)) bounds.extend(coordinate)
  return bounds
}

function displayValue(value: string | undefined): string {
  return value?.trim() || "—"
}

type ProjectedViewport = {
  minLongitude: number
  maxLongitude: number
  minLatitude: number
  maxLatitude: number
}

function featureCoordinateBounds(
  feature: Feature<Polygon | MultiPolygon, FootprintProperties>,
): [number, number, number, number] | null {
  const coordinates: Array<[number, number]> = []
  collectCoordinates(feature.geometry.coordinates, coordinates)
  if (!coordinates.length) return null
  const longitudes = coordinates.map(([longitude]) => longitude)
  const latitudes = coordinates.map(([, latitude]) => latitude)
  return [
    Math.min(...longitudes),
    Math.min(...latitudes),
    Math.max(...longitudes),
    Math.max(...latitudes),
  ]
}

function geometryPath(
  geometry: Polygon | MultiPolygon,
  viewport: ProjectedViewport,
): string {
  const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates
  const longitudeSpan = viewport.maxLongitude - viewport.minLongitude
  const latitudeSpan = viewport.maxLatitude - viewport.minLatitude
  return polygons
    .flatMap((polygon) =>
      polygon.map((ring) =>
        ring
          .map(([longitude, latitude], index) => {
            const x = ((longitude - viewport.minLongitude) / longitudeSpan) * svgMapWidth
            const y = svgMapHeight - ((latitude - viewport.minLatitude) / latitudeSpan) * svgMapHeight
            return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`
          })
          .join(" ") + " Z",
      ),
    )
    .join(" ")
}

function FootprintFallbackMap({
  footprintById,
  proposedIds,
  selectedBldgIds,
  streetName,
  onSelect,
}: {
  footprintById: Map<
    string,
    Feature<Polygon | MultiPolygon, FootprintProperties>[]
  >
  proposedIds: string[]
  selectedBldgIds: string[]
  streetName: string
  onSelect: (bldgid: string) => void
}) {
  const [contextScale, setContextScale] = useState(1)
  const mapData = useMemo(() => {
    const focusIds = selectedBldgIds.length
      ? selectedBldgIds
      : contextScale < 0.5
        ? proposedIds.slice(0, 1)
        : proposedIds
    const anchors = focusIds.flatMap((id) => footprintById.get(id) ?? [])
    const anchorBounds = anchors.map(featureCoordinateBounds).filter(Boolean) as Array<
      [number, number, number, number]
    >
    if (!anchorBounds.length) return null

    const anchorMinLongitude = Math.min(...anchorBounds.map((bounds) => bounds[0]))
    const anchorMinLatitude = Math.min(...anchorBounds.map((bounds) => bounds[1]))
    const anchorMaxLongitude = Math.max(...anchorBounds.map((bounds) => bounds[2]))
    const anchorMaxLatitude = Math.max(...anchorBounds.map((bounds) => bounds[3]))
    const centerLongitude = (anchorMinLongitude + anchorMaxLongitude) / 2
    const centerLatitude = (anchorMinLatitude + anchorMaxLatitude) / 2
    const latitudeFactor = Math.max(Math.cos((centerLatitude * Math.PI) / 180), 0.2)
    const candidateWidth = (anchorMaxLongitude - anchorMinLongitude) * latitudeFactor
    const candidateHeight = anchorMaxLatitude - anchorMinLatitude
    let projectedWidth = Math.max(candidateWidth * 1.6, 0.00045) * contextScale
    let projectedHeight = Math.max(candidateHeight * 1.6, 0.00032) * contextScale
    const targetAspect = svgMapWidth / svgMapHeight
    if (projectedWidth / projectedHeight < targetAspect) {
      projectedWidth = projectedHeight * targetAspect
    } else {
      projectedHeight = projectedWidth / targetAspect
    }
    const longitudeWidth = projectedWidth / latitudeFactor
    const viewport: ProjectedViewport = {
      minLongitude: centerLongitude - longitudeWidth / 2,
      maxLongitude: centerLongitude + longitudeWidth / 2,
      minLatitude: centerLatitude - projectedHeight / 2,
      maxLatitude: centerLatitude + projectedHeight / 2,
    }

    const visible = [...footprintById.entries()].flatMap(([bldgid, features]) =>
      features.flatMap((feature) => {
        const bounds = featureCoordinateBounds(feature)
        if (
          !bounds ||
          bounds[2] < viewport.minLongitude ||
          bounds[0] > viewport.maxLongitude ||
          bounds[3] < viewport.minLatitude ||
          bounds[1] > viewport.maxLatitude
        ) {
          return []
        }
        return [{ bldgid, feature, bounds }]
      }),
    )
    return { viewport, visible }
  }, [contextScale, footprintById, proposedIds, selectedBldgIds])

  return (
    <div className="review-fallback-map" aria-label={`Building footprint map near ${streetName}`}>
      <div className="review-fallback-map__heading">
        <div>
          <strong>Building footprint map</strong>
          <span>{streetName}</span>
        </div>
        <div className="review-fallback-map__controls" aria-label="Map zoom controls">
          <button
            type="button"
            onClick={() => setContextScale((scale) => Math.min(scale * 1.5, 12))}
            aria-label="Show a wider area"
          >
            −
          </button>
          <button
            type="button"
            onClick={() => setContextScale((scale) => Math.max(scale / 1.5, 0.04))}
            aria-label="Zoom in"
          >
            +
          </button>
        </div>
      </div>
      {mapData ? (
        <svg
          className="review-fallback-map__svg"
          viewBox={`0 0 ${svgMapWidth} ${svgMapHeight}`}
          role="img"
          aria-label="Cambridge GIS building footprints"
        >
          <rect width={svgMapWidth} height={svgMapHeight} className="review-fallback-map__ground" />
          {mapData.visible.map(({ bldgid, feature, bounds }, featureIndex) => {
            const proposed = proposedIds.includes(bldgid)
            const selected = selectedBldgIds.includes(bldgid)
            const centerX =
              (((bounds[0] + bounds[2]) / 2 - mapData.viewport.minLongitude) /
                (mapData.viewport.maxLongitude - mapData.viewport.minLongitude)) *
              svgMapWidth
            const centerY =
              svgMapHeight -
              (((bounds[1] + bounds[3]) / 2 - mapData.viewport.minLatitude) /
                (mapData.viewport.maxLatitude - mapData.viewport.minLatitude)) *
                svgMapHeight
            const address =
              feature.properties?.Address ||
              feature.properties?.addresses ||
              "No canonical address"
            return (
              <g
                key={`${bldgid}-${featureIndex}`}
                className={
                  selected
                    ? "review-footprint review-footprint--selected"
                    : proposed
                      ? "review-footprint review-footprint--proposed"
                      : "review-footprint"
                }
                onClick={() => onSelect(bldgid)}
              >
                <path d={geometryPath(feature.geometry, mapData.viewport)} fillRule="evenodd">
                  <title>{`${bldgid} — ${address}`}</title>
                </path>
                <text x={centerX} y={centerY} className="review-footprint__id">
                  {bldgid}
                </text>
                <text x={centerX} y={centerY + 18} className="review-footprint__address">
                  {String(address)}
                </text>
              </g>
            )
          })}
          <text x={svgMapWidth - 24} y={34} className="review-fallback-map__north">N ↑</text>
        </svg>
      ) : (
        <p className="review-fallback-map__empty">No candidate geometry is available.</p>
      )}
      <p className="review-fallback-map__hint">
        Canonical addresses are shown for proposed and neighboring buildings. Click any
        footprint to select and focus it; use + to zoom in or − to show a wider area.
      </p>
    </div>
  )
}

export default function ManualReviewWorkspace() {
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const footprintsRef = useRef<FootprintCollection | null>(null)
  const [footprintById, setFootprintById] = useState(
    new Map<string, Feature<Polygon | MultiPolygon, FootprintProperties>[]>(),
  )
  const [records, setRecords] = useState<ReviewRecord[]>([])
  const [queueMode, setQueueMode] = useState<"ambiguous" | "unmatched">("ambiguous")
  const [queueCounts, setQueueCounts] = useState({ ambiguous: 0, unmatched: 0 })
  const [recordIndex, setRecordIndex] = useState(0)
  const [selectedBldgIds, setSelectedBldgIds] = useState<string[]>([])
  const [note, setNote] = useState("")
  const [loading, setLoading] = useState(true)
  const [footprintsLoaded, setFootprintsLoaded] = useState(false)
  const [mapReady, setMapReady] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [addressQuery, setAddressQuery] = useState("")
  const currentRecord = records[recordIndex]

  const footprintSummary = (bldgid: string) => {
    const features = footprintById.get(bldgid) ?? []
    const properties = features[0]?.properties
    return {
      bldgid,
      address: properties?.Address || properties?.addresses || "No canonical address",
      featureCount: features.length,
    }
  }

  const candidates = candidateIds(currentRecord).map(footprintSummary)
  const selectedNeighbors = selectedBldgIds
    .filter((id) => !candidateIds(currentRecord).includes(id))
    .map(footprintSummary)
  const reviewedCount = records.filter((record) => record.override).length
  const addressResults = useMemo(() => {
    const query = addressQuery.trim().toLocaleLowerCase()
    if (query.length < 2) return []
    return [...footprintById.entries()]
      .map(([bldgid, features]) => {
        const properties = features[0]?.properties
        const addresses = String(properties?.addresses || properties?.Address || "")
        const canonical = addresses.split("|").map((value) => value.trim()).filter(Boolean)
        const searchable = canonical.join(" | ").toLocaleLowerCase()
        const rank = searchable === query ? 0 : searchable.startsWith(query) ? 1 : searchable.includes(query) ? 2 : 3
        return { bldgid, address: canonical.join(" · ") || "No canonical address", rank }
      })
      .filter((result) => result.rank < 3)
      .sort((left, right) => left.rank - right.rank || left.address.localeCompare(right.address))
      .slice(0, 12)
  }, [addressQuery, footprintById])

  function toggleBuildingSelection(bldgid: string) {
    setSelectedBldgIds((current) =>
      current.includes(bldgid)
        ? current.filter((id) => id !== bldgid)
        : [...current, bldgid],
    )
  }

  const fetchReviewData = useCallback(async (queue: "ambiguous" | "unmatched") => {
    const response = await fetch(`/api/manual-review?queue=${queue}`, {
      cache: "no-store",
    })
    const data = (await response.json()) as ReviewResponse
    if (!response.ok || data.error) {
      throw new Error(data.error || `Review API failed (${response.status})`)
    }
    setRecords(data.records)
    setQueueMode(data.queue)
    setQueueCounts(data.queue_counts)
    const firstPending = data.records.findIndex((record) => !record.override)
    const nextIndex = firstPending >= 0 ? firstPending : 0
    const nextRecord = data.records[nextIndex]
    setRecordIndex(nextIndex)
    setSelectedBldgIds(overrideBuildingIds(nextRecord?.override))
    setNote(nextRecord?.override?.note ?? "")
    setMessage(null)
    return data
  }, [])

  async function switchQueue(queue: "ambiguous" | "unmatched") {
    if (queue === queueMode || loading) return
    try {
      setLoading(true); setError(null); setMessage(null); setAddressQuery("")
      await fetchReviewData(queue)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : String(loadError))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        setLoading(true)
        const [, footprintResponse] = await Promise.all([
          fetchReviewData("ambiguous"),
          fetch("/data/cambridge-buildings.geojson"),
        ])
        if (!footprintResponse.ok) {
          throw new Error(`Building data failed (${footprintResponse.status})`)
        }
        const footprints = (await footprintResponse.json()) as FootprintCollection
        if (cancelled) return
        footprintsRef.current = footprints
        const lookup = new Map<
          string,
          Feature<Polygon | MultiPolygon, FootprintProperties>[]
        >()
        for (const feature of footprints.features) {
          const id = String(feature.properties?.BldgID ?? "").trim()
          if (!id) continue
          const group = lookup.get(id) ?? []
          group.push(feature)
          lookup.set(id, group)
        }
        setFootprintById(lookup)
        setFootprintsLoaded(true)
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : String(loadError))
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [fetchReviewData])

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current || !footprintsRef.current) return
    maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs")
    let map: maplibregl.Map
    try {
      map = new maplibregl.Map({
        container: mapContainerRef.current,
        style: "https://tiles.openfreemap.org/styles/positron",
        center: [-71.1056, 42.3736],
        zoom: 13,
      })
    } catch (mapError) {
      console.warn("Using the SVG footprint map because WebGL is unavailable.", mapError)
      mapContainerRef.current.style.display = "none"
      return
    }
    mapRef.current = map
    map.on("error", (event) => {
      const message = String(event.error?.message ?? event.error ?? "")
      if (/webgl|gpuinitialization/i.test(message)) {
        console.warn("Using the SVG footprint map because WebGL is unavailable.", event.error)
        map.getContainer().style.display = "none"
      }
    })
    map.addControl(new maplibregl.NavigationControl(), "top-right")
    map.on("load", () => {
      map.addSource(sourceId, {
        type: "geojson",
        data: footprintsRef.current as FootprintCollection,
      })
      map.addLayer({
        id: baseFillId,
        type: "fill",
        source: sourceId,
        paint: { "fill-color": "#94a3b8", "fill-opacity": 0.22 },
      })
      map.addLayer({
        id: outlineId,
        type: "line",
        source: sourceId,
        paint: { "line-color": "#475569", "line-width": 0.8 },
      })
      map.addLayer({
        id: candidateFillId,
        type: "fill",
        source: sourceId,
        filter: ["in", ["get", "BldgID"], ["literal", []]],
        paint: { "fill-color": "#f59e0b", "fill-opacity": 0.72 },
      })
      map.addLayer({
        id: selectedFillId,
        type: "fill",
        source: sourceId,
        filter: ["==", ["get", "BldgID"], ""],
        paint: { "fill-color": "#2563eb", "fill-opacity": 0.82 },
      })
      map.addLayer({
        id: labelId,
        type: "symbol",
        source: sourceId,
        layout: {
          "text-field": [
            "format",
            ["coalesce", ["get", "BldgID"], ""],
            { "font-scale": 1 },
            "\n",
            {},
            ["coalesce", ["get", "Address"], "No address"],
            { "font-scale": 0.78 },
          ] as unknown as maplibregl.ExpressionSpecification,
          "text-size": 11,
          "text-allow-overlap": false,
          "text-padding": 3,
        },
        paint: {
          "text-color": "#0f172a",
          "text-halo-color": "#ffffff",
          "text-halo-width": 1.5,
        },
      })
      map.on("click", baseFillId, (event) => {
        const id = String(event.features?.[0]?.properties?.BldgID ?? "").trim()
        if (id) toggleBuildingSelection(id)
      })
      map.on("mouseenter", baseFillId, () => {
        map.getCanvas().style.cursor = "pointer"
      })
      map.on("mouseleave", baseFillId, () => {
        map.getCanvas().style.cursor = ""
      })
      setMapReady(true)
    })
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [footprintsLoaded])

  useEffect(() => {
    if (!currentRecord || !mapReady) return
    const map = mapRef.current
    if (!map?.isStyleLoaded()) return
    const ids = candidateIds(currentRecord)
    map.setFilter(candidateFillId, [
      "in",
      ["get", "BldgID"],
      ["literal", ids],
    ])
    map.setFilter(selectedFillId, ["==", ["get", "BldgID"], ""])
    const features = ids.flatMap(
      (id) => footprintById.get(id) ?? [],
    )
    const bounds = boundsForFeatures(features)
    if (bounds) map.fitBounds(bounds, { padding: 90, maxZoom: 18, duration: 450 })
  }, [currentRecord, footprintById, mapReady])

  useEffect(() => {
    const map = mapRef.current
    if (!map?.isStyleLoaded() || !mapReady) return
    map.setFilter(selectedFillId, [
      "in",
      ["get", "BldgID"],
      ["literal", selectedBldgIds],
    ])
  }, [mapReady, selectedBldgIds])

  function advanceAfter(index: number, updatedRecords: ReviewRecord[]) {
    const nextPending = updatedRecords.findIndex(
      (record, candidateIndex) => candidateIndex > index && !record.override,
    )
    if (nextPending >= 0) selectRecord(nextPending, updatedRecords)
  }

  function selectRecord(index: number, sourceRecords = records) {
    const nextRecord = sourceRecords[index]
    if (!nextRecord) return
    setRecordIndex(index)
    setSelectedBldgIds(overrideBuildingIds(nextRecord.override))
    setNote(nextRecord.override?.note ?? "")
    setMessage(null)
    setError(null)
    setAddressQuery("")
  }

  function selectAddressResult(bldgid: string) {
    if (!selectedBldgIds.includes(bldgid)) {
      setSelectedBldgIds((current) => [...current, bldgid])
    }
    const map = mapRef.current
    const bounds = boundsForFeatures(footprintById.get(bldgid) ?? [])
    if (map?.isStyleLoaded() && bounds) {
      map.fitBounds(bounds, { padding: 100, maxZoom: 18, duration: 450 })
    }
  }

  async function saveDecision(decision: "matched" | "no_map_match") {
    if (!currentRecord) return
    if (decision === "matched" && !selectedBldgIds.length) {
      setError("Select one or more proposed or neighboring buildings first.")
      return
    }
    try {
      setSaving(true)
      setError(null)
      const response = await fetch("/api/manual-review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          building_id: currentRecord.building_id,
          decision,
          bldgids: decision === "matched" ? selectedBldgIds : [],
          note,
        }),
      })
      const result = (await response.json()) as {
        error?: string
        override?: ManualOverride
      }
      if (!response.ok || result.error || !result.override) {
        throw new Error(result.error || `Save failed (${response.status})`)
      }
      const updated = records.map((record) =>
        record.building_id === currentRecord.building_id
          ? { ...record, override: result.override ?? null }
          : record,
      )
      setRecords(updated)
      setMessage(
        decision === "matched"
          ? `Saved match to ${selectedBldgIds.join(", ")}.`
          : "Saved no map match.",
      )
      advanceAfter(recordIndex, updated)
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : String(saveError))
    } finally {
      setSaving(false)
    }
  }

  async function clearDecision() {
    if (!currentRecord?.override) return
    try {
      setSaving(true)
      const response = await fetch("/api/manual-review", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ building_id: currentRecord.building_id }),
      })
      const result = (await response.json()) as { error?: string }
      if (!response.ok || result.error) {
        throw new Error(result.error || `Clear failed (${response.status})`)
      }
      setRecords((current) =>
        current.map((record) =>
          record.building_id === currentRecord.building_id
            ? { ...record, override: null }
            : record,
        ),
      )
      setSelectedBldgIds([])
      setNote("")
      setMessage("Cleared saved decision.")
    } catch (clearError) {
      setError(clearError instanceof Error ? clearError.message : String(clearError))
    } finally {
      setSaving(false)
    }
  }

  if (error && !records.length) {
    return <div className="review-fatal">Error: {error}</div>
  }

  return (
    <section className="review-workspace">
      <aside className="review-panel">
        <div className="review-street-picker">
          <strong>Priority review queue</strong>
          <p>
            {reviewedCount} of {records.length} reviewed. Oldest dated records
            appear first; ties favor richer metadata.
          </p>
        </div>
        <div className="review-queue-tabs" role="tablist" aria-label="Hail review queue">
          <button type="button" role="tab" aria-selected={queueMode === "ambiguous"} onClick={() => switchQueue("ambiguous")}>Ambiguous <span>{queueCounts.ambiguous}</span></button>
          <button type="button" role="tab" aria-selected={queueMode === "unmatched"} onClick={() => switchQueue("unmatched")}>Completely unmatched <span>{queueCounts.unmatched}</span></button>
        </div>

        {loading && <p className="review-status">Loading review data…</p>}
        {!loading && !currentRecord && (
          <p className="review-status">No records are pending manual review.</p>
        )}
        {currentRecord && (
          <>
            <nav className="review-record-nav" aria-label="Review record navigation">
              <button
                type="button"
                onClick={() => selectRecord(Math.max(0, recordIndex - 1))}
                disabled={recordIndex === 0 || saving}
              >
                Previous
              </button>
              <span>
                {recordIndex + 1} / {records.length}
              </span>
              <button
                type="button"
                onClick={() => selectRecord(Math.min(records.length - 1, recordIndex + 1))}
                disabled={recordIndex >= records.length - 1 || saving}
              >
                Next
              </button>
            </nav>

            <article className="hail-review-card">
              <div className="hail-review-card__heading">
                <div>
                  <p className="review-kicker">
                    Priority {recordIndex + 1} · {currentRecord.priority_year ?? "year unknown"}
                    {" · "}{currentRecord.priority_metadata_count}/7 metadata fields
                  </p>
                  <h2>{currentRecord.hail_address}</h2>
                </div>
                {currentRecord.override && (
                  <span className="review-complete-badge">Reviewed</span>
                )}
              </div>
              <dl>
                <div><dt>Hail ID</dt><dd>{currentRecord.building_id}</dd></div>
                <div><dt>Classification</dt><dd>{displayValue(currentRecord.hail.classification)}</dd></div>
                <div><dt>Building type</dt><dd>{displayValue(currentRecord.hail.building_type)}</dd></div>
                <div><dt>Construction year</dt><dd>{displayValue(currentRecord.hail.construction_year)}</dd></div>
                <div><dt>Stories</dt><dd>{displayValue(currentRecord.hail.stories)}</dd></div>
                <div><dt>Historic address</dt><dd>{displayValue(currentRecord.hail.historic_address)}</dd></div>
                <div><dt>Architect</dt><dd>{displayValue(currentRecord.hail.architect)}</dd></div>
                <div><dt>Builder</dt><dd>{displayValue(currentRecord.hail.builder)}</dd></div>
                <div><dt>Original owner</dt><dd>{displayValue(currentRecord.hail.owner_at_construction)}</dd></div>
              </dl>
              <p className="hail-review-card__summary">{currentRecord.hail.summary_raw}</p>
              <p className="hail-review-card__reason">
                <strong>Why review:</strong> {currentRecord.review_reason_summary || currentRecord.match_reason}
              </p>
            </article>

            <section className="candidate-list" aria-labelledby="candidate-title">
              <div className="candidate-list__heading">
                <h3 id="candidate-title">Proposed footprints</h3>
                <span>{candidates.length}</span>
              </div>
              {candidates.map((candidate) => (
                <button
                  type="button"
                  key={candidate.bldgid}
                  className={
                    selectedBldgIds.includes(candidate.bldgid)
                      ? "candidate-card candidate-card--selected"
                      : "candidate-card"
                  }
                  onClick={() => toggleBuildingSelection(candidate.bldgid)}
                >
                  <strong>{candidate.bldgid}</strong>
                  <span>{candidate.address}</span>
                </button>
              ))}
              {selectedNeighbors.map((selectedSummary) => (
                <div
                  key={selectedSummary.bldgid}
                  className="candidate-card candidate-card--neighbor"
                >
                  <span className="candidate-card__tag">Neighbor selected from map</span>
                  <strong>{selectedSummary.bldgid}</strong>
                  <span>{selectedSummary.address}</span>
                </div>
              ))}
              <p className="candidate-list__hint">
                Orange buildings are proposed candidates. Click any gray neighboring
                footprint on the map to add or remove it. Selected footprints are blue.
              </p>
            </section>

            <label className="review-note">
              Review note
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                rows={3}
                placeholder="Optional evidence or reasoning"
              />
            </label>

            {error && <p className="review-feedback review-feedback--error">{error}</p>}
            {message && <p className="review-feedback review-feedback--success">{message}</p>}

            <div className="review-actions">
              <button
                type="button"
                className="review-action review-action--primary"
                disabled={!selectedBldgIds.length || saving}
                onClick={() => saveDecision("matched")}
              >
                {saving ? "Saving…" : "Save selected buildings"}
              </button>
              <button
                type="button"
                className="review-action review-action--no-match"
                disabled={saving}
                onClick={() => saveDecision("no_map_match")}
              >
                No map match
              </button>
              {currentRecord.override && (
                <button
                  type="button"
                  className="review-action review-action--clear"
                  disabled={saving}
                  onClick={clearDecision}
                >
                  Clear saved decision
                </button>
              )}
            </div>
          </>
        )}
      </aside>

      <div className="review-map-shell">
        <div className="review-address-search">
          <label htmlFor="canonical-address-search">Find footprint by canonical address</label>
          <input id="canonical-address-search" type="search" value={addressQuery} onChange={(event) => setAddressQuery(event.target.value)} placeholder="e.g. 15 Brattle St" autoComplete="off" />
          {addressQuery.trim().length >= 2 && <div className="review-address-results">
            {addressResults.map((result) => <button type="button" key={result.bldgid} onClick={() => selectAddressResult(result.bldgid)}><span>{result.address}</span><small>{result.bldgid}{selectedBldgIds.includes(result.bldgid) ? " · selected" : ""}</small></button>)}
            {!addressResults.length && <p>No canonical addresses match.</p>}
          </div>}
        </div>
        <FootprintFallbackMap
          key={currentRecord?.building_id ?? "empty"}
          footprintById={footprintById}
          proposedIds={candidateIds(currentRecord)}
          selectedBldgIds={selectedBldgIds}
          streetName={currentRecord?.hail_street_name ?? "Priority review"}
          onSelect={toggleBuildingSelection}
        />
        <div ref={mapContainerRef} className="review-map" />
        <div className="review-map-legend">
          <span><i className="review-swatch review-swatch--candidate" /> Proposed</span>
          <span><i className="review-swatch review-swatch--selected" /> Selected</span>
          <span><i className="review-swatch review-swatch--neighbor" /> Neighbor</span>
        </div>
      </div>
    </section>
  )
}
