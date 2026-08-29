export type CanonicalAddressProperties = {
  address?: string | null
  Address?: string | null
  address_count?: number | string | null
}

export function hasCanonicalCambridgeAddress(
  properties: CanonicalAddressProperties | null | undefined,
): boolean {
  const addressCount = Number(properties?.address_count)
  const address = properties?.address ?? properties?.Address

  return (
    Number.isFinite(addressCount) &&
    addressCount > 0 &&
    typeof address === "string" &&
    address.trim() !== ""
  )
}
