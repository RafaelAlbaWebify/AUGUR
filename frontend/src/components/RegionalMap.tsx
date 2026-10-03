import { useEffect, useMemo, useState } from 'react'

type RegionFeature = {
  type: 'Feature'
  properties?: {
    NUTS_ID?: string
    NUTS_NAME?: string
    NAME_LATN?: string
    CNTR_CODE?: string
    LEVL_CODE?: number
  }
  geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon | null
}

type CityMarker = {
  name: string
  lon: number
  lat: number
}

type RegionalMapProps = {
  countryIso2: string
  selectedRegion: string | null
  onSelectRegion: (regionId: string, regionName: string) => void
  cities?: CityMarker[]
  showRegionList?: boolean
}

type Bounds = {
  minLon: number
  maxLon: number
  minLat: number
  maxLat: number
}

const GISCO_NUTS2_URL =
  'https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_4326_LEVL_2.geojson'

function coordinatesOf(geometry: RegionFeature['geometry']): number[][] {
  if (!geometry) return []
  if (geometry.type === 'Polygon') return geometry.coordinates.flat()
  return geometry.coordinates.flat(2)
}

function computeBounds(features: RegionFeature[]): Bounds | null {
  const coordinates = features.flatMap((feature) => coordinatesOf(feature.geometry))
  if (!coordinates.length) return null

  return {
    minLon: Math.min(...coordinates.map(([lon]) => lon)),
    maxLon: Math.max(...coordinates.map(([lon]) => lon)),
    minLat: Math.min(...coordinates.map(([, lat]) => lat)),
    maxLat: Math.max(...coordinates.map(([, lat]) => lat)),
  }
}

function projector(bounds: Bounds, width: number, height: number) {
  const pad = 18
  const lonRange = Math.max(0.001, bounds.maxLon - bounds.minLon)
  const latRange = Math.max(0.001, bounds.maxLat - bounds.minLat)
  const scale = Math.min(
    (width - pad * 2) / lonRange,
    (height - pad * 2) / latRange,
  )
  const projectedWidth = lonRange * scale
  const projectedHeight = latRange * scale
  const offsetX = (width - projectedWidth) / 2
  const offsetY = (height - projectedHeight) / 2

  return ([lon, lat]: number[]) => [
    offsetX + (lon - bounds.minLon) * scale,
    height - (offsetY + (lat - bounds.minLat) * scale),
  ] as const
}

function pathFor(
  geometry: RegionFeature['geometry'],
  bounds: Bounds,
  width: number,
  height: number,
) {
  if (!geometry) return ''
  const project = projector(bounds, width, height)

  function ringPath(ring: number[][]) {
    return ring.map((coordinate, index) => {
      const [x, y] = project(coordinate)
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`
    }).join(' ') + ' Z'
  }

  if (geometry.type === 'Polygon') {
    return geometry.coordinates.map(ringPath).join(' ')
  }

  return geometry.coordinates
    .flatMap((polygon) => polygon.map(ringPath))
    .join(' ')
}

export default function RegionalMap({
  countryIso2,
  selectedRegion,
  onSelectRegion,
  cities = [],
  showRegionList = false,
}: RegionalMapProps) {
  const [features, setFeatures] = useState<RegionFeature[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [hoveredRegion, setHoveredRegion] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setStatus('loading')

    fetch(GISCO_NUTS2_URL, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`GISCO HTTP ${response.status}`)
        return response.json()
      })
      .then((data: GeoJSON.FeatureCollection) => {
        if (controller.signal.aborted) return
        const filtered = (data.features as RegionFeature[])
          .filter((feature) =>
            feature.properties?.CNTR_CODE === countryIso2 &&
            Number(feature.properties?.LEVL_CODE ?? 2) === 2
          )
          .sort((a, b) =>
            (a.properties?.NAME_LATN ?? a.properties?.NUTS_NAME ?? '')
              .localeCompare(b.properties?.NAME_LATN ?? b.properties?.NUTS_NAME ?? '')
          )
        setFeatures(filtered)
        setStatus(filtered.length ? 'ready' : 'error')
      })
      .catch((error) => {
        if ((error as Error).name === 'AbortError') return
        setFeatures([])
        setStatus('error')
      })

    return () => controller.abort()
  }, [countryIso2])

  const bounds = useMemo(() => computeBounds(features), [features])
  const activeFeature = features.find((feature) =>
    feature.properties?.NUTS_ID === (hoveredRegion ?? selectedRegion)
  )

  if (status === 'loading') {
    return <div className="regionalMapState">Loading official NUTS 2 regions…</div>
  }

  if (status === 'error' || !bounds) {
    return (
      <div className="regionalMapState error">
        Regional geometry unavailable. Country-level evidence remains active.
      </div>
    )
  }

  return (
    <section className="regionalMapView" aria-label="Selectable NUTS 2 regions">
      <div className="regionalMapCanvas">
        <svg
          viewBox="0 0 520 320"
          role="img"
          aria-label="Selectable NUTS 2 regional map"
          data-testid="regional-map"
        >
          {features.map((feature) => {
            const id = feature.properties?.NUTS_ID ?? ''
            const name = feature.properties?.NAME_LATN ?? feature.properties?.NUTS_NAME ?? id
            return (
              <path
                key={id}
                d={pathFor(feature.geometry, bounds, 520, 320)}
                className={[
                  'nutsRegion',
                  selectedRegion === id ? 'selected' : '',
                  hoveredRegion === id ? 'hovered' : '',
                ].filter(Boolean).join(' ')}
                tabIndex={0}
                role="button"
                aria-label={name}
                onMouseEnter={() => setHoveredRegion(id)}
                onMouseLeave={() => setHoveredRegion(null)}
                onFocus={() => setHoveredRegion(id)}
                onBlur={() => setHoveredRegion(null)}
                onClick={() => onSelectRegion(id, name)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    onSelectRegion(id, name)
                  }
                }}
              />
            )
          })}

          {cities.map((city) => {
            const [cx, cy] = projector(bounds, 520, 320)([city.lon, city.lat])
            return (
              <g className="regionalCityMarker" key={city.name} transform={`translate(${cx} ${cy})`}>
                <circle r="4.5" />
                <circle r="8.5" className="halo" />
                <text x="10" y="3">{city.name}</text>
              </g>
            )
          })}
        </svg>

        <div className="regionalMapLabel">
          <span>{activeFeature?.properties?.NUTS_ID ?? 'NUTS 2'}</span>
          <strong>
            {activeFeature?.properties?.NAME_LATN ??
              activeFeature?.properties?.NUTS_NAME ??
              'Select a region'}
          </strong>
        </div>
      </div>

      {showRegionList && (
        <div className="regionalRegionList" aria-label="Regions">
          {features.map((feature) => {
            const id = feature.properties?.NUTS_ID ?? ''
            const name = feature.properties?.NAME_LATN ?? feature.properties?.NUTS_NAME ?? id
            return (
              <button
                key={id}
                type="button"
                className={selectedRegion === id ? 'active' : ''}
                onClick={() => onSelectRegion(id, name)}
              >
                <span>{id}</span>
                {name}
              </button>
            )
          })}
        </div>
      )}

      <small className="regionalMapSource">
        Geography: Eurostat GISCO · NUTS 2024 · level 2 · EPSG:4326
      </small>
    </section>
  )
}
