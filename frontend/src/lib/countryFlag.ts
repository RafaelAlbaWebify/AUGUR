const ISO3_TO_ISO2: Record<string, string> = {
  ESP: 'ES',
  PRT: 'PT',
  IRL: 'IE',
}

export function countryFlag(iso2?: string, iso3?: string) {
  const code = (iso2 || (iso3 ? ISO3_TO_ISO2[iso3] : '') || '').toUpperCase()

  if (!/^[A-Z]{2}$/.test(code)) return '🌐'

  return String.fromCodePoint(
    ...[...code].map((letter) => 127397 + letter.charCodeAt(0)),
  )
}
