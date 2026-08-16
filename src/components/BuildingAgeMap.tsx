"use client";

import React, { useEffect, useRef, useState } from "react"
import * as maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import ageBands from "@/data/Age_bands.json"
import { parseWikipediaArticles } from "@/lib/wikipediaArticles.mjs"
import type { FeatureCollection, Polygon, MultiPolygon } from "geojson"

type BuildingProperties = {
  age_band?: string
  year_built?: number | string | null
  Condition_YearBuilt?: number | string
  wikipedia_article_count?: number
  wikipedia_articles_json?: string | null
  [key: string]: unknown
}

type BuildingFeatureCollection = FeatureCollection<
  Polygon | MultiPolygon,
  BuildingProperties
>

type AgeBand = {
  id: string
  label: string
  color: string
  [key: string]: unknown
}

const orderedAgeBands = ageBands as AgeBand[]
const allAgeBandIds = orderedAgeBands.map((band) => band.id)
const sourceId = "cambridge-buildings"
const fillLayerId = "building-age-fill"
const outlineLayerId = "building-age-outline"

const ageBandColors = orderedAgeBands.reduce<Record<string, string>>(
  (lookup, band) => {
    if (typeof band.id === "string" && typeof band.color === "string") {
      lookup[band.id] = band.color
    }
    return lookup
  },
  {},
)

const fillColorExpression = [
  "match",
  ["get", "age_band"],
  ...Object.entries(ageBandColors).flatMap(([key, color]) => [key, color]),
  "#999999",
] as const

function getValidConstructionYearCoverage(
  featureCollection: BuildingFeatureCollection,
): number {
  const total = featureCollection.features.length
  if (total === 0) return 0

  const validCount = featureCollection.features.filter((feature) => {
    const properties = feature.properties
    const year = properties?.year_built ?? properties?.Condition_YearBuilt

    return typeof year === "number" && Number.isFinite(year)
  }).length

  return (validCount / total) * 100
}

function displayValue(value: unknown): string | null {
  if (value === null || value === undefined) return null
  if (typeof value === "string") return value.trim() || null
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : null
  if (typeof value === "boolean") return String(value)
  return null
}

function validYear(value: unknown): number | null {
  const year =
    typeof value === "number"
      ? value
      : typeof value === "string" && value.trim() !== ""
        ? Number(value)
        : Number.NaN

  return Number.isInteger(year) && year >= 1600 && year <= new Date().getFullYear()
    ? year
    : null
}

function getPopupYearBuilt(properties: BuildingProperties): number | "Unknown" {
  const hailYear = validYear(properties.hail_year_built)
  const assessorYear = validYear(
    properties.assessor_year_built ?? properties.Condition_YearBuilt,
  )

  if (
    hailYear !== null &&
    (assessorYear === null || Math.abs(hailYear - assessorYear) <= 50)
  ) {
    return hailYear
  }

  return assessorYear ?? "Unknown"
}

function getBuildingPopupContent(properties: BuildingProperties): HTMLElement {
  const address = properties.address ?? properties.Address ?? "Unknown"
  const buildingName =
    properties.hail_building_name ?? properties.hail_building_type

  const rows: Array<[string, unknown]> = [
    ["Address", address],
    ["Building name", buildingName],
    ["Year built", getPopupYearBuilt(properties)],
    ["Architect", properties.hail_architect],
    ["Builder", properties.hail_builder],
  ]

  const container = document.createElement("div")
  const details = document.createElement("dl")
  details.className = "building-popup"
  for (const [label, value] of rows) {
    const displayed = displayValue(value)
    if (!displayed) continue
    const row = document.createElement("div")
    const term = document.createElement("dt")
    const description = document.createElement("dd")
    term.textContent = label
    description.textContent = displayed
    row.append(term, description)
    details.append(row)
  }
  container.append(details)

  const articles = parseWikipediaArticles(properties.wikipedia_articles_json)
  if (articles.length) {
    const section = document.createElement("section")
    section.className = "building-popup__wikipedia"
    const heading = document.createElement("p")
    heading.className = "building-popup__wikipedia-heading"
    heading.textContent = articles.length === 1 ? "Wikipedia article" : "Wikipedia articles"
    const list = document.createElement("ul")
    for (const article of articles) {
      const item = document.createElement("li")
      const link = document.createElement("a")
      link.href = article.url
      link.target = "_blank"
      link.rel = "noopener noreferrer"
      link.textContent = article.title
      item.append(link)
      list.append(item)
    }
    section.append(heading, list)
    container.append(section)
  }
  return container
}

export default function BuildingAgeMap({
  showInternalLinks = false,
}: {
  showInternalLinks?: boolean
}) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [coverage, setCoverage] = useState<number | null>(null)
  const [selectedBands, setSelectedBands] = useState<string[]>(allAgeBandIds)
  const [legendCollapsed, setLegendCollapsed] = useState(false)

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setLegendCollapsed(window.matchMedia("(max-width: 640px)").matches)
    })

    return () => window.cancelAnimationFrame(frame)
  }, [])

  useEffect(() => {
    if (mapRef.current || !mapContainerRef.current) return

    // Next.js can rewrite MapLibre's automatically resolved module-worker URL.
    // Serve the matching worker bundle directly so GeoJSON processing completes.
    maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs")

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: "https://tiles.openfreemap.org/styles/positron",
      center: [-71.1056, 42.3736],
      zoom: 13,
    })
    const popup = new maplibregl.Popup({
      closeButton: true,
      closeOnClick: false,
      maxWidth: "20rem",
    })
    const abortController = new AbortController()
    let openBuildingKey: string | null = null
    let interactionListenersAttached = false

    mapRef.current = map

    map.addControl(
      new maplibregl.NavigationControl({ showCompass: true }),
      "top-right",
    )
    map.addControl(
      new maplibregl.GeolocateControl({
        positionOptions: {
          enableHighAccuracy: true,
        },
        trackUserLocation: true,
      }),
      "top-right",
    )
    const handleMapError = (event: maplibregl.ErrorEvent) => {
      console.error("MapLibre error:", event.error)
    }

    const handlePopupClose = () => {
      openBuildingKey = null
    }

    const showBuildingPopup = (event: maplibregl.MapLayerMouseEvent) => {
      const properties = event.features?.[0]?.properties as
        | BuildingProperties
        | undefined
      if (!properties) return

      popup
        .setLngLat(event.lngLat)
        .setDOMContent(getBuildingPopupContent(properties))
        .addTo(map)
    }

    const getBuildingKey = (event: maplibregl.MapLayerMouseEvent) => {
      const feature = event.features?.[0]
      const properties = feature?.properties as BuildingProperties | undefined
      return String(
        feature?.id ??
          properties?.bldgid ??
          properties?.address ??
          properties?.Address ??
          "building",
      )
    }

    const handleBuildingMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer"
    }

    const handleBuildingMouseLeave = () => {
      map.getCanvas().style.cursor = ""
    }

    const handleBuildingClick = (event: maplibregl.MapLayerMouseEvent) => {
      const buildingKey = getBuildingKey(event)
      if (buildingKey === openBuildingKey) {
        popup.remove()
        return
      }

      openBuildingKey = buildingKey
      showBuildingPopup(event)
    }

    const attachInteractionListeners = () => {
      if (interactionListenersAttached) return
      map.on("mouseenter", fillLayerId, handleBuildingMouseEnter)
      map.on("mouseleave", fillLayerId, handleBuildingMouseLeave)
      map.on("click", fillLayerId, handleBuildingClick)
      interactionListenersAttached = true
    }

    popup.on("close", handlePopupClose)
    map.on("error", handleMapError)

    const handleMapLoad = async () => {
      try {
        const response = await fetch("/data/cambridge-buildings.geojson", {
          signal: abortController.signal,
        })
        if (!response.ok) {
          throw new Error(
            `Failed to load building data (${response.status} ${response.statusText})`,
          )
        }

        const data = (await response.json()) as BuildingFeatureCollection
        setCoverage(getValidConstructionYearCoverage(data))

        if (!map.getSource(sourceId)) {
          map.addSource(sourceId, {
            type: "geojson",
            data,
          })
        }

        if (!map.getLayer(fillLayerId)) {
          map.addLayer({
            id: fillLayerId,
            type: "fill",
            source: sourceId,
            paint: {
              "fill-color":
                fillColorExpression as unknown as maplibregl.ExpressionSpecification,
              "fill-opacity": 0.72,
            },
          })
        }

        if (!map.getLayer(outlineLayerId)) {
          map.addLayer({
            id: outlineLayerId,
            type: "line",
            source: sourceId,
            paint: {
              "line-color": "#000000",
              "line-opacity": 0.35,
              "line-width": 1,
            },
          })
        }

        attachInteractionListeners()
      } catch (loadError) {
        if (abortController.signal.aborted) return
        setError(
          loadError instanceof Error ? loadError.message : String(loadError),
        )
      } finally {
        if (!abortController.signal.aborted) setLoading(false)
      }
    }

    map.on("load", handleMapLoad)

    return () => {
      abortController.abort()
      map.off("load", handleMapLoad)
      map.off("error", handleMapError)
      if (interactionListenersAttached) {
        map.off("mouseenter", fillLayerId, handleBuildingMouseEnter)
        map.off("mouseleave", fillLayerId, handleBuildingMouseLeave)
        map.off("click", fillLayerId, handleBuildingClick)
      }
      popup.off("close", handlePopupClose)
      popup.remove()
      map.getCanvas().style.cursor = ""
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    const filter = [
      "in",
      ["get", "age_band"],
      ["literal", selectedBands],
    ] as maplibregl.FilterSpecification

    if (map.getLayer(fillLayerId)) {
      map.setFilter(fillLayerId, filter)
    }
    if (map.getLayer(outlineLayerId)) {
      map.setFilter(outlineLayerId, filter)
    }
  }, [selectedBands])

  function toggleAgeBand(bandId: string) {
    setSelectedBands((currentBands) =>
      currentBands.includes(bandId)
        ? currentBands.filter((id) => id !== bandId)
        : [...currentBands, bandId],
    )
  }

  return (
    <div className="map-shell">
      <div ref={mapContainerRef} className="map-container" />
      {loading && (
        <div className="map-message map-message--loading" role="status">
          Loading building data…
        </div>
      )}
      {error && (
        <div className="map-message map-message--error" role="alert">
          Error: {error}
        </div>
      )}
      {!loading && !error && coverage !== null && (
        <aside
          className={`map-legend${legendCollapsed ? " map-legend--collapsed" : ""}`}
          aria-labelledby="map-legend-title"
        >
          <div className="map-legend__header">
            <h2 id="map-legend-title" className="map-legend__title">
              Building age
            </h2>
            <button
              className="map-legend__toggle"
              type="button"
              aria-expanded={!legendCollapsed}
              aria-controls="map-legend-content"
              onClick={() => setLegendCollapsed((collapsed) => !collapsed)}
            >
              {legendCollapsed ? "Show" : "Hide"}
            </button>
          </div>
          <div id="map-legend-content" hidden={legendCollapsed}>
            <p className="map-legend__coverage">
              Construction year available for {coverage.toFixed(1)}% of mapped
              buildings
            </p>
            <div className="map-legend__actions">
              <button
                type="button"
                onClick={() => setSelectedBands(allAgeBandIds)}
                disabled={selectedBands.length === allAgeBandIds.length}
              >
                Select all
              </button>
              <button
                type="button"
                onClick={() => setSelectedBands([])}
                disabled={selectedBands.length === 0}
              >
                Clear all
              </button>
            </div>
            {showInternalLinks && (
              <>
                <a className="map-legend__review-link" href="/review">
                  Open manual review
                </a>
                <a className="map-legend__review-link" href="/quality-dashboard">
                  View enrichment quality
                </a>
              </>
            )}
            <ul className="map-legend__items">
              {orderedAgeBands.map((band) => (
                <li key={band.id} className="map-legend__item">
                  <input
                    id={`age-band-${band.id}`}
                    type="checkbox"
                    checked={selectedBands.includes(band.id)}
                    onChange={() => toggleAgeBand(band.id)}
                  />
                  <label htmlFor={`age-band-${band.id}`}>
                    <span
                      className="map-legend__swatch"
                      style={{ backgroundColor: band.color }}
                      aria-hidden="true"
                    />
                    <span>{band.label}</span>
                  </label>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      )}
    </div>
  )
}
