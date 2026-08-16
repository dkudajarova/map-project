import "server-only"

import { notFound } from "next/navigation"

export function internalToolsEnabled(): boolean {
  return process.env.NODE_ENV === "development"
}

export function requireInternalTools(): void {
  if (!internalToolsEnabled()) notFound()
}
