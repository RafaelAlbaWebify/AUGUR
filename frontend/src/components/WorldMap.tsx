import { useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react'
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
const MIN_VIEW_WIDTH = 250
const MAX_VIEW_WIDTH = WIDTH

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
  const svgRef = useRef<SVGSVGElement | null>(null)
  const dragStartRef = useRef<{
    clientX: number
    clientY: number
    x: number
    y: number
    moved: boolean
  } | null>(null)
  const suppressClickRef = useRef(false)
  const [viewBox, setViewBox] = useState({
    x: 0,
    y: 0,
    width: WIDTH,
    height: HEIGHT,
  })

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


  function clampView(next: { x: number; y: number; width: number; height: number }) {
    const width = Math.min(MAX_VIEW_WIDTH, Math.max(MIN_VIEW_WIDTH, next.width))
    const height = width * (HEIGHT / WIDTH)
    const maxX = WIDTH - width
    const maxY = HEIGHT - height

    return {
      x: Math.min(maxX, Math.max(0, next.x)),
      y: Math.min(maxY, Math.max(0, next.y)),
      width,
      height,
    }
  }

  function zoomAt(factor: number, clientX?: number, clientY?: number) {
    const svg = svgRef.current
    const rect = svg?.getBoundingClientRect()

    const anchorX =
      rect && clientX !== undefined
        ? viewBox.x + ((clientX - rect.left) / rect.width) * viewBox.width
        : viewBox.x + viewBox.width / 2

    const anchorY =
      rect && clientY !== undefined
        ? viewBox.y + ((clientY - rect.top) / rect.height) * viewBox.height
        : viewBox.y + viewBox.height / 2

    const nextWidth = viewBox.width * factor
    const nextHeight = nextWidth * (HEIGHT / WIDTH)
    const ratioX = (anchorX - viewBox.x) / viewBox.width
    const ratioY = (anchorY - viewBox.y) / viewBox.height

    setViewBox(
      clampView({
        x: anchorX - nextWidth * ratioX,
        y: anchorY - nextHeight * ratioY,
        width: nextWidth,
        height: nextHeight,
      }),
    )
  }

  function resetView() {
    setViewBox({ x: 0, y: 0, width: WIDTH, height: HEIGHT })
  }

  function handlePointerDown(event: ReactPointerEvent<SVGSVGElement>) {
    event.currentTarget.setPointerCapture(event.pointerId)
    dragStartRef.current = {
      clientX: event.clientX,
      clientY: event.clientY,
      x: viewBox.x,
      y: viewBox.y,
      moved: false,
    }
  }

  function handlePointerMove(event: ReactPointerEvent<SVGSVGElement>) {
    const start = dragStartRef.current
    const svg = svgRef.current
    if (!start || !svg) return

    const rect = svg.getBoundingClientRect()
    const deltaX = ((event.clientX - start.clientX) / rect.width) * viewBox.width
    const deltaY = ((event.clientY - start.clientY) / rect.height) * viewBox.height

    if (Math.abs(event.clientX - start.clientX) > 3 || Math.abs(event.clientY - start.clientY) > 3) {
      start.moved = true
    }

    setViewBox(
      clampView({
        x: start.x - deltaX,
        y: start.y - deltaY,
        width: viewBox.width,
        height: viewBox.height,
      }),
    )
  }

  function handlePointerUp(event: ReactPointerEvent<SVGSVGElement>) {
    const start = dragStartRef.current
    if (start?.moved) {
      suppressClickRef.current = true
      window.setTimeout(() => {
        suppressClickRef.current = false
      }, 0)
    }

    dragStartRef.current = null
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
  }

  return (
    <section className="worldMapSection" aria-label="World country map">
      <div className="dimensionHeader">
        <div>
          <div className="label">WORLD VIEW</div>
          <h3>Registered country coverage</h3>
        </div>
        <span>local SVG geometry · zoom, pan & click a covered country</span>
      </div>

      <div className="worldMapFrame">
        <svg
          ref={svgRef}
          className="worldMapSvg"
          viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
          role="img"
          aria-label="Interactive world map"
          data-testid="world-map"
          onWheel={(event) => {
            event.preventDefault()
            zoomAt(event.deltaY < 0 ? 0.8 : 1.25, event.clientX, event.clientY)
          }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
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
                  if (isRegistered && !suppressClickRef.current) {
                    onSelectCountry(item.iso3)
                  }
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

        <div className="worldMapControls" aria-label="Map controls">
          <button type="button" aria-label="Zoom in" onClick={() => zoomAt(0.8)}>+</button>
          <button type="button" aria-label="Zoom out" onClick={() => zoomAt(1.25)}>−</button>
          <button type="button" aria-label="Reset map" onClick={resetView}>Reset</button>
        </div>

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
