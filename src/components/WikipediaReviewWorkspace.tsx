"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import * as maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"

type Decision = {
  decision: "approved" | "rejected"
  bldgid: string | null
  review_note: string
  selected_latitude?: number | null
  selected_longitude?: number | null
  selection_method?: "generated_candidate" | "manual_marker" | null
}

type WikipediaRecord = {
  wikipedia_page_id: number
  wikipedia_title: string
  wikipedia_url: string
  latitude: number
  longitude: number
  match_method: string
  match_distance_meters: number | null
  candidate_bldgids: string
  confidence_status: string
  review_reason: string
  historic_candidate: boolean
  decision: Decision | null
}

type Selection = {
  bldgid: string | null
  latitude: number
  longitude: number
  method: "generated_candidate" | "manual_marker"
}

const sourceId = "wikipedia-review-buildings"
const fillId = "wikipedia-review-fill"
const outlineId = "wikipedia-review-outline"

function recordsForMode(records: WikipediaRecord[], historicOnly: boolean) {
  return records.filter((record) => !historicOnly || record.historic_candidate)
}

function firstUnreviewedIndex(records: WikipediaRecord[]): number {
  const unreviewedIndex = records.findIndex((record) => !record.decision)
  return unreviewedIndex >= 0 ? unreviewedIndex : 0
}

function selectionFilter(bldgid: string | null): maplibregl.FilterSpecification {
  return ["==", ["get", "BldgID"], bldgid ?? ""]
}

function FootprintMap({
  record,
  selection,
  onSelect,
}: {
  record: WikipediaRecord
  selection: Selection
  onSelect: (selection: Selection) => void
}) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markerRef = useRef<maplibregl.Marker | null>(null)
  const onSelectRef = useRef(onSelect)
  const initialRef = useRef({ record, selection })

  useEffect(() => {
    onSelectRef.current = onSelect
  }, [onSelect])

  useEffect(() => {
    if (!containerRef.current) return
    const initial = initialRef.current
    maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs")
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: "https://tiles.openfreemap.org/styles/positron",
      center: [initial.selection.longitude, initial.selection.latitude],
      zoom: 18.5,
    })
    const marker = new maplibregl.Marker({ draggable: true, color: "#c2410c" })
      .setLngLat([initial.selection.longitude, initial.selection.latitude])
      .addTo(map)
    mapRef.current = map
    markerRef.current = marker

    function selectAt(longitude: number, latitude: number, moveMarker: boolean) {
      if (moveMarker) marker.setLngLat([longitude, latitude])
      const features = map.getLayer(fillId) ? map.queryRenderedFeatures(map.project([longitude, latitude]), {
        layers: [fillId],
      }) : []
      const bldgid = String(features[0]?.properties?.BldgID ?? "").trim() || null
      onSelectRef.current({ bldgid, longitude, latitude, method: "manual_marker" })
      if (map.getLayer(outlineId)) map.setFilter(outlineId, selectionFilter(bldgid))
    }

    marker.on("dragend", () => {
      const point = marker.getLngLat()
      selectAt(point.lng, point.lat, false)
    })
    map.on("load", async () => {
      const response = await fetch("/data/cambridge-buildings.geojson")
      if (!response.ok) return
      const data = await response.json()
      map.addSource(sourceId, { type: "geojson", data })
      map.addLayer({
        id: fillId,
        type: "fill",
        source: sourceId,
        paint: { "fill-color": "#64748b", "fill-opacity": 0.22 },
      })
      map.addLayer({
        id: outlineId,
        type: "line",
        source: sourceId,
        filter: selectionFilter(initial.selection.bldgid),
        paint: { "line-color": "#2563eb", "line-width": 4 },
      })
      map.on("click", fillId, (event) => {
        const bldgid =
          String(event.features?.[0]?.properties?.BldgID ?? "").trim() || null
        marker.setLngLat(event.lngLat)
        onSelectRef.current({
          bldgid,
          longitude: event.lngLat.lng,
          latitude: event.lngLat.lat,
          method: "manual_marker",
        })
        map.setFilter(outlineId, selectionFilter(bldgid))
      })
      map.on("mouseenter", fillId, () => {
        map.getCanvas().style.cursor = "pointer"
      })
      map.on("mouseleave", fillId, () => {
        map.getCanvas().style.cursor = ""
      })
    })
    map.addControl(new maplibregl.NavigationControl(), "top-right")
    return () => {
      marker.remove()
      map.remove()
      markerRef.current = null
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    const marker = markerRef.current
    if (!map || !marker) return
    marker.setLngLat([selection.longitude, selection.latitude])
    map.easeTo({ center: [selection.longitude, selection.latitude], zoom: 18.5 })
    if (map.getLayer(outlineId)) {
      map.setFilter(outlineId, selectionFilter(selection.bldgid))
    }
  }, [record.wikipedia_page_id, selection.bldgid, selection.latitude, selection.longitude])

  return (
    <div
      ref={containerRef}
      className="wikipedia-review__map-canvas"
      aria-label={`Footprints near ${record.wikipedia_title}`}
    />
  )
}

export default function WikipediaReviewWorkspace() {
  const [records, setRecords] = useState<WikipediaRecord[]>([])
  const [historicOnly, setHistoricOnly] = useState(true)
  const [index, setIndex] = useState(0)
  const [notes, setNotes] = useState<{ [pageId: number]: string }>({})
  const [selections, setSelections] = useState<{ [pageId: number]: Selection }>({})
  const [message, setMessage] = useState("")
  const [loading, setLoading] = useState(true)
  const filtered = useMemo(
    () => recordsForMode(records, historicOnly),
    [records, historicOnly],
  )
  const record = filtered[index]
  const candidates = record?.candidate_bldgids.split("|").filter(Boolean) ?? []
  const selection = record
    ? (selections[record.wikipedia_page_id] ?? {
        bldgid: record.decision?.bldgid ?? candidates[0] ?? null,
        latitude: record.decision?.selected_latitude ?? record.latitude,
        longitude: record.decision?.selected_longitude ?? record.longitude,
        method: record.decision?.selection_method ?? "generated_candidate",
      })
    : null

  useEffect(() => {
    fetch("/api/wikipedia-review", { cache: "no-store" })
      .then(async (response) => {
        const data = await response.json()
        if (!response.ok) throw new Error(data.error)
        setRecords(data.records)
        setIndex(firstUnreviewedIndex(recordsForMode(data.records, true)))
      })
      .catch((error) => setMessage(String(error)))
      .finally(() => setLoading(false))
  }, [])

  const note = record
    ? (notes[record.wikipedia_page_id] ?? record.decision?.review_note ?? "")
    : ""

  async function save(decision: "approved" | "rejected") {
    if (!record || !selection) return
    setMessage("Saving…")
    const response = await fetch("/api/wikipedia-review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        wikipedia_page_id: record.wikipedia_page_id,
        decision,
        bldgid: selection.bldgid,
        selected_latitude: selection.latitude,
        selected_longitude: selection.longitude,
        selection_method: selection.method,
        review_note: note,
      }),
    })
    const data = await response.json()
    if (!response.ok) {
      setMessage(data.error ?? "Could not save decision")
      return
    }
    setRecords((current) =>
      current.map((item) =>
        item.wikipedia_page_id === record.wikipedia_page_id
          ? { ...item, decision: data.decision }
          : item,
      ),
    )
    setMessage(`${decision === "approved" ? "Approved" : "Rejected"}: ${record.wikipedia_title}`)
    setIndex((current) => Math.min(current + 1, filtered.length - 1))
  }

  if (loading) return <p className="review-status">Loading Wikipedia candidates…</p>
  if (!record || !selection)
    return <p className="review-fatal">No candidates match this filter.</p>

  const reviewed = filtered.filter((item) => item.decision).length
  return (
    <section className="review-workspace wikipedia-review">
      <aside className="review-panel">
        <div className="review-street-picker">
          <label>
            <input
              type="checkbox"
              checked={historicOnly}
              onChange={(event) => {
                const nextHistoricOnly = event.target.checked
                setHistoricOnly(nextHistoricOnly)
                setIndex(firstUnreviewedIndex(recordsForMode(records, nextHistoricOnly)))
              }}
            />{" "}
            Likely historic-building subset
          </label>
          <p>{reviewed} of {filtered.length} reviewed</p>
        </div>
        <div className="review-street-picker">
          <label htmlFor="wikipedia-record-picker">Jump to record</label>
          <select
            id="wikipedia-record-picker"
            value={record.wikipedia_page_id}
            onChange={(event) => {
              const pageId = Number(event.target.value)
              const nextIndex = filtered.findIndex(
                (item) => item.wikipedia_page_id === pageId,
              )
              if (nextIndex >= 0) setIndex(nextIndex)
            }}
          >
            {filtered.map((item, itemIndex) => (
              <option key={item.wikipedia_page_id} value={item.wikipedia_page_id}>
                {item.decision ? "✓" : "○"} {itemIndex + 1}. {item.wikipedia_title} ({item.wikipedia_page_id})
              </option>
            ))}
          </select>
          <p>○ unreviewed · ✓ reviewed</p>
        </div>
        <nav className="review-record-nav">
          <button onClick={() => setIndex((value) => Math.max(0, value - 1))} disabled={index === 0}>Previous</button>
          <span>{index + 1} / {filtered.length}</span>
          <button onClick={() => setIndex((value) => Math.min(filtered.length - 1, value + 1))} disabled={index === filtered.length - 1}>Next</button>
        </nav>
        <article className="hail-review-card">
          <p className="review-kicker">{record.confidence_status} · {record.match_method}</p>
          <h2>{record.wikipedia_title}</h2>
          {record.decision && <p className="review-complete-badge">Saved: {record.decision.decision}</p>}
          <dl>
            <div><dt>Generated candidate</dt><dd>{candidates.join(", ") || "None"}</dd></div>
            <div><dt>Selected footprint</dt><dd>{selection.bldgid ?? "Move marker onto a footprint"}</dd></div>
            <div><dt>Distance</dt><dd>{record.match_distance_meters === null ? "—" : `${record.match_distance_meters} m`}</dd></div>
          </dl>
          <p className="hail-review-card__reason">Drag the orange marker onto the correct footprint, or click a footprint directly. The selected footprint is outlined in blue.</p>
          <p><a href={record.wikipedia_url} target="_blank" rel="noopener noreferrer">Read article on Wikipedia ↗</a></p>
        </article>
        <label className="review-note">
          Review note
          <textarea value={note} onChange={(event) => setNotes((current) => ({ ...current, [record.wikipedia_page_id]: event.target.value }))} rows={4} />
        </label>
        <div className="review-actions">
          <button className="review-action review-action--primary" disabled={!selection.bldgid} onClick={() => save("approved")}>Approve selected footprint</button>
          <button className="review-action review-action--no-match" onClick={() => save("rejected")}>Reject article link</button>
        </div>
        {message && <p className="review-feedback">{message}</p>}
      </aside>
      <div className="review-map-shell wikipedia-review__map">
        <FootprintMap
          record={record}
          selection={selection}
          onSelect={(value) =>
            setSelections((current) => ({
              ...current,
              [record.wikipedia_page_id]: value,
            }))
          }
        />
      </div>
    </section>
  )
}
