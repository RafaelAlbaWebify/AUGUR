export type CountryVisual = {
  heroImage: string
  alt: string
  focalPoint?: string
  eyebrow?: string
}

const COUNTRY_VISUALS: Record<string, CountryVisual> = {
  ESP: {
    heroImage: '/country-images/ESP.svg',
    alt: 'Spain country visual',
    focalPoint: '50% 52%',
    eyebrow: 'Spain',
  },
  PRT: {
    heroImage: '/country-images/PRT.svg',
    alt: 'Portugal country visual',
    focalPoint: '50% 52%',
    eyebrow: 'Portugal',
  },
  IRL: {
    heroImage: '/country-images/IRL.svg',
    alt: 'Ireland country visual',
    focalPoint: '50% 48%',
    eyebrow: 'Ireland',
  },
}

export const DEFAULT_COUNTRY_VISUAL: CountryVisual = {
  heroImage: '/country-images/default.svg',
  alt: 'Country landscape visual',
  focalPoint: '50% 50%',
}

export function countryVisual(iso3: string) {
  return COUNTRY_VISUALS[iso3] ?? DEFAULT_COUNTRY_VISUAL
}
