import { useEffect, useMemo, useState } from 'react'

export type CountryView = 'overview' | 'outlook' | 'profile' | 'indicators' | 'skills'
export type AugurView = CountryView | 'dimension' | 'compare'

export type AugurRoute =
  | {
      kind: 'country'
      view: CountryView
      countryIso3: string
    }
  | {
      kind: 'dimension'
      view: 'dimension'
      countryIso3: string
      dimension: string
    }
  | {
      kind: 'compare'
      view: 'compare'
      countries: string[]
    }

const DEFAULT_COUNTRY = 'ESP'
const DEFAULT_COMPARE = ['IRL', 'ESP', 'PRT']

function normalizedIso3(value: string | null | undefined) {
  const code = (value ?? '').toUpperCase()
  return /^[A-Z]{3}$/.test(code) ? code : null
}

function normalizedDimension(value: string | null | undefined) {
  const dimension = (value ?? '').toLowerCase()
  return /^[a-z][a-z0-9_]*$/.test(dimension) ? dimension : null
}

export function parseAugurRoute(location: Location = window.location): AugurRoute {
  const path = location.pathname.replace(/\/+$/, '') || '/'
  const countryMatch = path.match(/^\/country\/([A-Za-z]{3})\/(overview|outlook|profile|indicators|skills)$/)

  if (countryMatch) {
    return {
      kind: 'country',
      countryIso3: countryMatch[1].toUpperCase(),
      view: countryMatch[2] as CountryView,
    }
  }

  const dimensionMatch = path.match(/^\/country\/([A-Za-z]{3})\/dimension\/([a-zA-Z0-9_]+)$/)
  if (dimensionMatch) {
    const dimension = normalizedDimension(dimensionMatch[2])
    if (dimension) {
      return {
        kind: 'dimension',
        view: 'dimension',
        countryIso3: dimensionMatch[1].toUpperCase(),
        dimension,
      }
    }
  }

  if (path === '/compare') {
    const params = new URLSearchParams(location.search)
    const countries = (params.get('countries') ?? '')
      .split(',')
      .map((item) => normalizedIso3(item))
      .filter((item): item is string => Boolean(item))

    const unique = [...new Set(countries)].slice(0, 3)

    return {
      kind: 'compare',
      view: 'compare',
      countries: unique.length >= 2 ? unique : DEFAULT_COMPARE,
    }
  }

  return {
    kind: 'country',
    countryIso3: DEFAULT_COUNTRY,
    view: 'overview',
  }
}

export function routeHref(route: AugurRoute) {
  if (route.kind === 'compare') {
    return `/compare?countries=${route.countries.join(',')}`
  }

  if (route.kind === 'dimension') {
    return `/country/${route.countryIso3}/dimension/${route.dimension}`
  }

  return `/country/${route.countryIso3}/${route.view}`
}

export function countryRoute(
  countryIso3: string,
  view: CountryView,
): AugurRoute {
  return {
    kind: 'country',
    countryIso3,
    view,
  }
}

export function dimensionRoute(
  countryIso3: string,
  dimension: string,
): AugurRoute {
  return {
    kind: 'dimension',
    countryIso3,
    view: 'dimension',
    dimension,
  }
}

export function compareRoute(countries: string[]): AugurRoute {
  const unique = [...new Set(countries.map((item) => item.toUpperCase()))].slice(0, 3)
  return {
    kind: 'compare',
    view: 'compare',
    countries: unique.length >= 2 ? unique : DEFAULT_COMPARE,
  }
}

export function useAugurRoute() {
  const [route, setRoute] = useState<AugurRoute>(() => parseAugurRoute())

  useEffect(() => {
    const canonical = routeHref(parseAugurRoute())
    const current = `${window.location.pathname}${window.location.search}`

    if (current === '/' || current !== canonical) {
      window.history.replaceState({}, '', canonical)
      setRoute(parseAugurRoute())
    }

    const handlePopState = () => setRoute(parseAugurRoute())
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const navigate = useMemo(
    () => (next: AugurRoute, options?: { replace?: boolean }) => {
      const href = routeHref(next)
      if (options?.replace) window.history.replaceState({}, '', href)
      else window.history.pushState({}, '', href)
      setRoute(next)
      window.scrollTo({ top: 0, behavior: 'auto' })
    },
    [],
  )

  return { route, navigate }
}
