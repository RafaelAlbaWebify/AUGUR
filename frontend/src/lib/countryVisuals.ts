export type CountryCity = {
  name: string
  lon: number
  lat: number
}

export type CountryVisual = {
  heroImage: string
  alt: string
  focalPoint?: string
  eyebrow?: string
  summary?: string
  cities?: CountryCity[]
}

const COUNTRY_VISUALS: Record<string, CountryVisual> = {
  ESP: {
    heroImage: '/country-images/ESP.svg',
    alt: 'Spain country visual',
    focalPoint: '50% 52%',
    eyebrow: 'Spain',
    summary: 'Large Southern European economy with strong urban networks, infrastructure and quality-of-life advantages, alongside labour and housing pressures.',
    cities: [
      { name: 'Madrid', lon: -3.7038, lat: 40.4168 },
      { name: 'Barcelona', lon: 2.1734, lat: 41.3851 },
      { name: 'Valencia', lon: -0.3763, lat: 39.4699 },
      { name: 'Sevilla', lon: -5.9845, lat: 37.3891 },
    ],
  },
  PRT: {
    heroImage: '/country-images/PRT.svg',
    alt: 'Portugal country visual',
    focalPoint: '50% 52%',
    eyebrow: 'Portugal',
    summary: 'Atlantic EU economy with strong livability and mobility appeal, a concentrated coastal labour market and housing affordability pressures in major cities.',
    cities: [
      { name: 'Lisboa', lon: -9.1393, lat: 38.7223 },
      { name: 'Porto', lon: -8.6291, lat: 41.1579 },
      { name: 'Braga', lon: -8.4265, lat: 41.5454 },
      { name: 'Faro', lon: -7.9304, lat: 37.0194 },
    ],
  },
  IRL: {
    heroImage: '/country-images/IRL.svg',
    alt: 'Ireland country visual',
    focalPoint: '50% 48%',
    eyebrow: 'Ireland',
    summary: 'Open high-income economy with a strong multinational employment base, English-speaking labour market and acute housing constraints in key urban areas.',
    cities: [
      { name: 'Dublin', lon: -6.2603, lat: 53.3498 },
      { name: 'Cork', lon: -8.4756, lat: 51.8985 },
      { name: 'Galway', lon: -9.0568, lat: 53.2707 },
      { name: 'Limerick', lon: -8.6305, lat: 52.6638 },
    ],
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
