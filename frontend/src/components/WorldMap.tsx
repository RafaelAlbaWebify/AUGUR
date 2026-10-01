import { useMemo } from 'react'
import { feature } from 'topojson-client'
import countriesTopology from 'world-atlas/countries-110m.json'

type Country = {
  iso3: string
  name: string
}

type WorldMapProps = {
  countries: Country[]
  selectedCountry: string
  onSelectCountry: (iso3: string) => void
}

type Geometry =
  | GeoJSON.Polygon
  | GeoJSON.MultiPolygon

const WIDTH = 1000
const HEIGHT = 500

const M49_TO_ISO3: Record<string, string> = {
  '724': 'ESP',
  '620': 'PRT',
  '372': 'IRL',
}

function buildWorldGeoJson() {
  const topology = countriesTopology as unknown as {
    type: 'Topology'
    objects: Record<string, unknown>
    arcs: unknown[]
    transform?: unknown
  }

  const collection = feature(
    topology as never,
    topology.objects.countries as never,
  ) as unknown as GeoJSON.FeatureCollection

  return {
    ...collection,
    features: collection.features.map((item) => ({
      ...item,
      properties: {
        ...(item.properties ?? {}),
        iso3: M49_TO_ISO3[String(item.id ?? '')] ?? '',
      },
    })),
  }
}

const WORLD_GEOJSON = buildWorldGeoJson()

function project([longitude, latitude]: number[]) {
  const x = ((longitude + 180) / 360) * WIDTH
  const y = ((90 - latitude) / 180) * HEIGHT
  return [x, y] as const
}

function ringPath(ring: number[][]) {
  if (!ring.length) return ''

  let path = ''
  let previousX: number | null = null

  for (const coordinate of ring) {
    const [x, y] = project(coordinate)
    const crossesAntimeridian =
      previousX !== null && Math.abs(x - previousX) > WIDTH / 2

    path += `${!path || crossesAntimeridian ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)} `
    previousX = x
  }

  return `${path}Z `
}

function geometryPath(geometry: Geometry | null) {
  if (!geometry) return ''

  if (geometry.type === 'Polygon') {
    return geometry.coordinates.map(ringPath).join('')
  }

  return geometry.coordinates
    .flatMap((polygon) => polygon.map(ringPath))
    .join('')
}

export default function WorldMap({
  countries,
  selectedCountry,
  onSelectCountry,
}: WorldMapProps) {
  const registered = useMemo(
    () => new Set(countries.map((country) => country.iso3)),
    [countries],
  )

  const features = useMemo(
    () =>
      WORLD_GEOJSON.features.map((item) => ({
        iso3: String(item.properties?.iso3 ?? ''),
        path: geometryPath(item.geometry as Geometry | null),
      })),
    [],
  )

  return (
    <section className="worldMapSection" aria-label="World country map">
      <div className="dimensionHeader">
        <div>
          <div className="label">WORLD VIEW</div>
          <h3>Registered country coverage</h3>
        </div>
        <span>local SVG geometry · click a covered country</span>
      </div>

      <div className="worldMapFrame">
        <svg
          className="worldMapSvg"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-label="Interactive world map"
          data-testid="world-map"
        >
          <rect width={WIDTH} height={HEIGHT} className="worldMapOcean" />

          {features.map((item, index) => {
            const isRegistered = registered.has(item.iso3)
            const isSelected = item.iso3 === selectedCountry

            return (
              <path
                key={`${item.iso3 || 'world'}-${index}`}
                d={item.path}
                className={[
                  'worldCountry',
                  isRegistered ? 'registered' : '',
                  isSelected ? 'selected' : '',
                ].filter(Boolean).join(' ')}
                data-country={item.iso3 || undefined}
                aria-label={isRegistered ? item.iso3 : undefined}
                role={isRegistered ? 'button' : undefined}
                tabIndex={isRegistered ? 0 : undefined}
                onClick={() => {
                  if (isRegistered) onSelectCountry(item.iso3)
                }}
                onKeyDown={(event) => {
                  if (
                    isRegistered &&
                    (event.key === 'Enter' || event.key === ' ')
                  ) {
                    event.preventDefault()
                    onSelectCountry(item.iso3)
                  }
                }}
              />
            )
          })}
        </svg>

        <div className="worldMapLegend">
          {countries.map((country) => (
            <button
              key={country.iso3}
              type="button"
              className={country.iso3 === selectedCountry ? 'active' : ''}
              onClick={() => onSelectCountry(country.iso3)}
            >
              <span />
              {country.name}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
