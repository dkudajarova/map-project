import BuildingAgeMap from "@/components/BuildingAgeMap"
import { internalToolsEnabled } from "@/lib/internalTools"

export default function Page() {
  return (
    <main className="app-layout">
      <BuildingAgeMap showInternalLinks={internalToolsEnabled()} />
    </main>
  )
}
