import Link from "next/link"
import ManualReviewWorkspace from "@/components/ManualReviewWorkspace"
import { requireInternalTools } from "@/lib/internalTools"

export default function ReviewPage() {
  requireInternalTools()

  return (
    <main className="review-page">
      <header className="review-header">
        <div>
          <p className="review-header__eyebrow">Cambridge building database</p>
          <h1>Hail address manual review</h1>
        </div>
        <Link href="/" className="review-header__link">
          Return to building map
        </Link>
      </header>
      <ManualReviewWorkspace />
    </main>
  )
}
