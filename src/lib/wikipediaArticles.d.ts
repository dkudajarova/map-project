export type WikipediaArticle = {
  page_id: number
  title: string
  url: string
}

export function parseWikipediaArticles(value: unknown): WikipediaArticle[]
