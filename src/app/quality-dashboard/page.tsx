import type { CSSProperties } from "react"
import Link from "next/link"
import { getQualityDashboardData } from "@/lib/qualityDashboard"
import { requireInternalTools } from "@/lib/internalTools"

const METADATA_COLORS = ["#e7e3dc", "#b9d5ce", "#6ea99c", "#df9a55", "#b94f37"]
const formatCount = (value: number) => new Intl.NumberFormat("en-US").format(value)
const formatPercent = (value: number) => value === 0 ? "0%" : value < 0.1 ? "<0.1%" : `${value.toFixed(1)}%`

export default function QualityDashboardPage() {
  requireInternalTools()

  const data = getQualityDashboardData()
  const hailGradient = `conic-gradient(${data.hail.outcomes.map((item, index) => {
    const start = data.hail.outcomes.slice(0, index).reduce((sum, entry) => sum + entry.percent, 0)
    return `${item.color} ${start}% ${start + item.percent}%`
  }).join(", ")})`
  const largestYearDifferenceBin = Math.max(
    ...data.footprintDiagnostics.constructionYearDifferenceDistribution.map((item) => item.count),
    1,
  )

  return <main className="quality-page">
    <header className="quality-hero"><div>
      <p className="quality-eyebrow">Cambridge building database</p><h1>Map enrichment quality</h1>
      <p className="quality-intro">Coverage and display-ready metadata across {formatCount(data.footprintTotal)} building footprints.</p>
    </div><Link href="/" className="quality-back">Return to building map</Link></header>

    <section className="quality-card" aria-labelledby="source-heading">
      <div className="quality-section-heading"><div><p className="quality-section-number">01</p><h2 id="source-heading">Footprint source coverage</h2></div><p>Share of all mapped footprints</p></div>
      <div className="quality-source-bar" aria-label="Source coverage distribution">{data.sourceCoverage.map((item) => <span key={item.label} style={{ width: `${item.percent}%`, backgroundColor: item.color }} title={`${item.label}: ${formatPercent(item.percent)}`} />)}</div>
      <div className="quality-source-grid">{data.sourceCoverage.map((item) => <article key={item.label} className="quality-source-stat"><i style={{ backgroundColor: item.color }} /><div><strong>{formatPercent(item.percent)}</strong><span>{item.label}</span><small>{formatCount(item.count)} footprints</small></div></article>)}</div>
      <p className="quality-method-note">“Other combinations” captures footprints with Wikipedia but no assessor record; it is shown so coverage totals remain complete.</p>
    </section>

    <section className="quality-card" aria-labelledby="diagnostics-heading">
      <div className="quality-section-heading"><div><p className="quality-section-number">02</p><h2 id="diagnostics-heading">Multiple records &amp; construction-year differences</h2></div><p>Footprint-level linkage diagnostics</p></div>
      <div className="quality-diagnostic-grid">
        <article><strong>{formatCount(data.footprintDiagnostics.multipleAssessorRecords)}</strong><span>More than one assessor record</span><small>{formatPercent(data.footprintDiagnostics.multipleAssessorRecords / data.footprintTotal * 100)} of footprints</small></article>
        <article><strong>{formatCount(data.footprintDiagnostics.multipleHailRecords)}</strong><span>More than one Hail record</span><small>{formatPercent(data.footprintDiagnostics.multipleHailRecords / data.footprintTotal * 100)} of footprints</small></article>
        <article><strong>{formatCount(data.footprintDiagnostics.multipleEitherSource)}</strong><span>More than one record from either source</span><small>Unique footprints; no double counting</small></article>
        <article className="quality-diagnostic-alert"><strong>{formatCount(data.footprintDiagnostics.constructionYearDifferenceOver50)}</strong><span>Construction years differ by over 50 years</span><small>{formatPercent(data.footprintDiagnostics.constructionYearDifferenceOver50 / data.footprintDiagnostics.comparableConstructionYears * 100)} of {formatCount(data.footprintDiagnostics.comparableConstructionYears)} comparable footprints</small></article>
      </div>
      <div className="quality-difference-chart" aria-label="Distribution of construction-year differences over 50 years">
        <div className="quality-difference-header"><strong>Difference</strong><span>Footprints</span></div>
        {data.footprintDiagnostics.constructionYearDifferenceDistribution.map((item) => <div className="quality-difference-row" key={item.label}><strong>{item.label}</strong><div><i style={{ width: `${item.count / largestYearDifferenceBin * 100}%`, backgroundColor: item.color }} title={`${item.label}: ${formatCount(item.count)} footprints (${formatPercent(item.percent)})`} /></div><span>{formatCount(item.count)} <small>{formatPercent(item.percent)}</small></span></div>)}
      </div>
      <p className="quality-method-note">Record counts use `assessor_record_count` and accepted `hail_match_count` on each footprint. Year differences are absolute values and are available only where the footprint has one unambiguous Hail construction year and an assessor construction year; the chart includes strictly greater than 50 years.</p>
    </section>

    <section className="quality-card" aria-labelledby="metadata-heading">
      <div className="quality-section-heading"><div><p className="quality-section-number">03</p><h2 id="metadata-heading">Displayable metadata by building age</h2></div><p>Architect · builder · building name · Wikipedia link</p></div>
      <div className="quality-metadata-legend" aria-label="Number of additional metadata fields">{METADATA_COLORS.map((color, count) => <span key={color}><i style={{ backgroundColor: color }} />{count} {count === 1 ? "field" : "fields"}</span>)}</div>
      <div className="quality-age-table"><div className="quality-age-header" aria-hidden="true"><span>Age range</span><span>Distribution within age range</span><span>Records</span></div>
        {data.ageMetadata.map((row) => <div className="quality-age-row" key={row.label}><strong>{row.label}</strong><div className="quality-stacked-bar" aria-label={`${row.label} metadata distribution`}>{row.percents.map((value, count) => value > 0 && <span key={count} style={{ width: `${value}%`, backgroundColor: METADATA_COLORS[count] }} title={`${count} fields: ${formatCount(row.counts[count])} (${formatPercent(value)})`}>{value >= 8 ? formatPercent(value) : ""}</span>)}</div><span>{formatCount(row.total)}</span></div>)}
      </div><p className="quality-method-note">Each field counts once when populated. Multiple Wikipedia articles on one footprint count as one displayable field.</p>
    </section>

    <section className="quality-card" aria-labelledby="hail-heading">
      <div className="quality-section-heading"><div><p className="quality-section-number">04</p><h2 id="hail-heading">Hail footprint mapping</h2></div><p>{formatCount(data.hail.eligibleTotal)} mapping-eligible records</p></div>
      <div className="quality-hail-layout"><div className="quality-donut" style={{ "--donut-gradient": hailGradient } as CSSProperties} role="img" aria-label={data.hail.outcomes.map((item) => `${item.label}: ${formatPercent(item.percent)}`).join(", ")}><div><strong>{formatCount(data.hail.eligibleTotal)}</strong><span>eligible records</span></div></div>
        <div className="quality-hail-stats">{data.hail.outcomes.map((item) => <article key={item.label}><i style={{ backgroundColor: item.color }} /><div><span>{item.label}</span><strong>{formatPercent(item.percent)}</strong></div><small>{formatCount(item.count)} records</small></article>)}</div>
      </div><p className="quality-method-note">Mapping-eligible records exclude {formatCount(data.hail.excludedTotal)} razed Hail rows and {formatCount(data.hail.sourceArtifactTotal)} admin-reviewed source artifacts marked no map match. “No footprint” now includes only unresolved records still pending review.</p>
    </section>
    <footer className="quality-footer">Calculated from the current map GeoJSON and complete Hail match audit · {new Date(data.generatedAt).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</footer>
  </main>
}
