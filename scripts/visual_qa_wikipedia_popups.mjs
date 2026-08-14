import assert from "node:assert/strict"
import { mkdir } from "node:fs/promises"
import path from "node:path"
import { chromium } from "playwright-core"

const baseUrl = process.env.QA_BASE_URL ?? "http://localhost:3000"
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
const outputDirectory = path.resolve("reports/visual-qa")
const initialCenter = [-71.1056, 42.3736]
const initialZoom = 13
const samples = {
  single: { longitude: -71.10385412672662, latitude: 42.372209036195834, expected: 1 },
  multiple: { longitude: -71.11557290940956, latitude: 42.378522450933716, expected: 4 },
  unlinked: { longitude: -71.10550721435555, latitude: 42.37363305305104, expected: 0 },
}

function worldPoint(longitude, latitude, zoom) {
  const size = 512 * 2 ** zoom
  const radians = latitude * Math.PI / 180
  return {
    x: (longitude + 180) / 360 * size,
    y: (1 - Math.log(Math.tan(radians) + 1 / Math.cos(radians)) / Math.PI) / 2 * size,
  }
}

function screenPoint(sample, viewport) {
  const center = worldPoint(initialCenter[0], initialCenter[1], initialZoom)
  const target = worldPoint(sample.longitude, sample.latitude, initialZoom)
  return { x: viewport.width / 2 + target.x - center.x, y: viewport.height / 2 + target.y - center.y }
}

async function inspectSample(page, viewport, name, sample) {
  const existingPopup = page.locator(".maplibregl-popup")
  if (await existingPopup.isVisible()) {
    await existingPopup.locator(".maplibregl-popup-close-button").evaluate((button) => button.click())
  }
  const point = screenPoint(sample, viewport)
  await page.mouse.click(point.x, point.y)
  await page.waitForTimeout(250)
  const popup = page.locator(".maplibregl-popup-content")
  await popup.waitFor({ state: "visible" })
  const links = popup.locator(".building-popup__wikipedia a")
  assert.equal(await links.count(), sample.expected, `${name} popup article count`)
  for (const link of await links.all()) {
    const href = await link.getAttribute("href")
    assert.match(href ?? "", /^https:\/\/en\.wikipedia\.org\/wiki\//)
    assert.equal(await link.getAttribute("target"), "_blank")
    assert.match(await link.getAttribute("rel") ?? "", /noopener/)
  }
  await page.screenshot({ path: path.join(outputDirectory, `${viewport.width}-${name}.png`) })
}

await mkdir(outputDirectory, { recursive: true })
const browser = await chromium.launch({ executablePath: chromePath, headless: true })
try {
  for (const viewport of [{ width: 1200, height: 800 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport })
    await page.goto(baseUrl, { waitUntil: "domcontentloaded" })
    await page.locator(".map-message--loading").waitFor({ state: "hidden", timeout: 60_000 })
    await page.waitForTimeout(1_000)
    for (const [name, sample] of Object.entries(samples)) {
      await inspectSample(page, viewport, name, sample)
    }
    await page.close()
  }
} finally {
  await browser.close()
}

console.log("Wikipedia popup visual QA passed for desktop and mobile viewports.")
