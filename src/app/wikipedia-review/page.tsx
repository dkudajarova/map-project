import Link from "next/link"
import WikipediaReviewWorkspace from "@/components/WikipediaReviewWorkspace"

export default function WikipediaReviewPage() {
  return <main className="review-page">
    <header className="review-header">
      <div><p className="review-header__eyebrow">Cambridge building database</p><h1>Wikipedia building review</h1></div>
      <Link href="/" className="review-header__link">Return to building map</Link>
    </header>
    <WikipediaReviewWorkspace />
  </main>
}
