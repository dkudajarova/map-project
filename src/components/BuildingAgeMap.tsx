"use client";

import React, { useEffect, useRef, useState } from "react"
import * as maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import ageBands from "../data/Age_bands.json"
import type { FeatureCollection, Polygon, MultiPolygon } from "geojson"

type BuildingProperties = {
  age_band?: string
  Condition_YearBuilt?: number | string
  [key: string]: unknown
}

type BuildingFeatureCollection = FeatureCollection<
  Polygon | MultiPolygon,
  BuildingProperties
>

type AgeBand = {
  id: string
  color: string
  [key: string]: unknown
}

const ageBandColors = (ageBands as AgeBand[]).reduce<Record<string, string>>(
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
    const year = feature.properties?.Condition_YearBuilt
    if (typeof year === "number") {
      return Number.isFinite(year)
    }
    if (typeof year === "string") {
      return /^\d{3,4}$/.test(year.trim())
    }
    return false
  }).length

  return Math.round((validCount / total) * 100)
}

export default function BuildingAgeMap() {
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [coverage, setCoverage] = useState<number | null>(null)

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

    mapRef.current = map

    map.addControl(
      new maplibregl.NavigationControl({ showCompass: true }),
      "top-right",
    )
    const sourceId = "cambridge-buildings"
    const fillLayerId = "building-age-fill"
    const outlineLayerId = "building-age-outline"

    map.on("error", (event) => {
      console.error("MapLibre error:", event.error)
    })

    map.on("load", async () => {
      try {
        const response = await fetch("/data/cambridge-buildings.geojson")
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
      } catch (loadError) {
        setError(
          loadError instanceof Error ? loadError.message : String(loadError),
        )
      } finally {
        setLoading(false)
      }
    })

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  return (
    <div style={{ position: "relative", width: "100vw", height: "100vh" }}>
      <div ref={mapContainerRef} style={{ width: "100%", height: "100%" }} />
      {loading && (
        <div
          style={{
            position: "absolute",
            top: 16,
            left: 16,
            zIndex: 1,
            padding: 12,
            backgroundColor: "rgba(255,255,255,0.9)",
            borderRadius: 8,
            boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
          }}
        >
          Loading building data…
        </div>
      )}
      {error && (
        <div
          style={{
            position: "absolute",
            top: 16,
            left: 16,
            zIndex: 1,
            padding: 12,
            backgroundColor: "rgba(255,235,235,0.95)",
            borderRadius: 8,
            color: "#900",
            boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
          }}
        >
          Error: {error}
        </div>
      )}
      {!loading && !error && coverage !== null && (
        <div
          style={{
            position: "absolute",
            bottom: 16,
            left: 16,
            zIndex: 1,
            padding: 12,
            backgroundColor: "rgba(255,255,255,0.9)",
            borderRadius: 8,
            boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
          }}
        >
          Construction year coverage: {coverage}%
        </div>
      )}
    </div>
  )
}
