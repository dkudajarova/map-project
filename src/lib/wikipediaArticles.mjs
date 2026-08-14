function displayValue(value) {
  if (value === null || value === undefined) return null
  if (typeof value === "string") return value.trim() || null
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : null
  if (typeof value === "boolean") return String(value)
  return null
}

function validWikipediaUrl(value) {
  if (typeof value !== "string") return null
  try {
    const url = new URL(value)
    if (
      url.protocol !== "https:" ||
      url.hostname !== "en.wikipedia.org" ||
      url.port ||
      url.username ||
      url.password ||
      !url.pathname.startsWith("/wiki/")
    ) {
      return null
    }
    return url.href
  } catch {
    return null
  }
}

export function parseWikipediaArticles(value) {
  if (typeof value !== "string" || !value.trim()) return []
  try {
    const parsed = JSON.parse(value)
    if (!Array.isArray(parsed)) return []
    const seenPageIds = new Set()
    return parsed.flatMap((item) => {
      if (!item || typeof item !== "object") return []
      const pageId = item.page_id
      const title = displayValue(item.title)
      const url = validWikipediaUrl(item.url)
      if (
        typeof pageId !== "number" ||
        !Number.isInteger(pageId) ||
        pageId <= 0 ||
        !title ||
        !url ||
        seenPageIds.has(pageId)
      ) {
        return []
      }
      seenPageIds.add(pageId)
      return [{ page_id: pageId, title, url }]
    })
  } catch {
    return []
  }
}
