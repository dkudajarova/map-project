import assert from "node:assert/strict"
import test from "node:test"

import { parseWikipediaArticles } from "../../src/lib/wikipediaArticles.mjs"

test("parses multiple canonical Wikipedia articles", () => {
  const result = parseWikipediaArticles(JSON.stringify([
    { page_id: 2, title: "Second House", url: "https://en.wikipedia.org/wiki/Second_House" },
    { page_id: 1, title: "First House", url: "https://en.wikipedia.org/wiki/First_House" },
  ]))
  assert.equal(result.length, 2)
  assert.equal(result[0].title, "Second House")
})

test("rejects malformed JSON and non-array values", () => {
  assert.deepEqual(parseWikipediaArticles("{"), [])
  assert.deepEqual(parseWikipediaArticles('{"page_id":1}'), [])
  assert.deepEqual(parseWikipediaArticles(null), [])
})

test("rejects unsafe or non-canonical URLs", () => {
  const unsafeUrls = [
    "javascript:alert(1)",
    "http://en.wikipedia.org/wiki/House",
    "https://evil.example/wiki/House",
    "https://en.wikipedia.org.evil.example/wiki/House",
    "https://user@en.wikipedia.org/wiki/House",
    "https://en.wikipedia.org:444/wiki/House",
    "https://en.wikipedia.org/w/index.php?title=House",
  ]
  const result = parseWikipediaArticles(JSON.stringify(unsafeUrls.map((url, index) => ({
    page_id: index + 1,
    title: "Unsafe",
    url,
  }))))
  assert.deepEqual(result, [])
})

test("rejects invalid fields and duplicate page IDs", () => {
  const result = parseWikipediaArticles(JSON.stringify([
    { page_id: 1, title: "Valid House", url: "https://en.wikipedia.org/wiki/Valid_House" },
    { page_id: 1, title: "Duplicate", url: "https://en.wikipedia.org/wiki/Duplicate" },
    { page_id: -2, title: "Negative", url: "https://en.wikipedia.org/wiki/Negative" },
    { page_id: 3, title: "   ", url: "https://en.wikipedia.org/wiki/Blank" },
  ]))
  assert.deepEqual(result, [{ page_id: 1, title: "Valid House", url: "https://en.wikipedia.org/wiki/Valid_House" }])
})
