import { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl, { type GeoJSONSource, type Map } from 'maplibre-gl'
import { feature } from 'topojson-client'
import countriesTopology from 'world-atlas/countries-110m.json'
import 'maplibre-gl/dist/maplibre-gl.css'

type Country = {
  iso3: string
  name: string
}

type WorldMapProps = {
  countries: Country[]
  selectedCountry: string
  onSelectCountry: (iso3: string) => void
}

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
  ) as GeoJSON.FeatureCollection

  collection.features = collection.features.map((item) => {
    const id = String(item.id ?? '')
    return {
      ...item,
      properties: {
        ...(item.properties ?? {}),
        iso3: M49_TO_ISO3[id] ?? '',
      },
    }
  })

  return collection
}

const WORLD_GEOJSON = buildWorldGeoJson()

export default function WorldMap({
  countries,
  selectedCountry,
  onSelectCountry,
}: WorldMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<Map | null>(null)
  const onSelectRef = useRef(onSelectCountry)
  const registeredRef = useRef(new Set<string>())
  const [mapUnavailable, setMapUnavailable] = useState(false)

  const registered = useMemo(
    () => new Set(countries.map((country) => country.iso3)),
    [countries],
  )

  useEffect(() => {
    onSelectRef.current = onSelectCountry
  }, [onSelectCountry])

  useEffect(() => {
    registeredRef.current = registered
  }, [registered])

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    let map: Map

    try {
      map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [
          {
            id: 'background',
            type: 'background',
            paint: {
              'background-color': '#0d1117',
            },
          },
        ],
      },
      center: [4, 28],
      zoom: 1.15,
      minZoom: 0.7,
      maxZoom: 5,
      attributionControl: false,
      renderWorldCopies: false,
      })
    } catch {
      setMapUnavailable(true)
      return
    }

    mapRef.current = map

    map.on('load', () => {
      map.addSource('countries', {
        type: 'geojson',
        data: WORLD_GEOJSON,
      })

      map.addLayer({
        id: 'country-fill',
        type: 'fill',
        source: 'countries',
        paint: {
          'fill-color': [
            'case',
            ['==', ['get', 'iso3'], selectedCountry],
            '#8ea5bc',
            ['!=', ['get', 'iso3'], ''],
            '#40505f',
            '#171d24',
          ],
          'fill-opacity': [
            'case',
            ['!=', ['get', 'iso3'], ''],
            0.92,
            0.72,
          ],
        },
      })

      map.addLayer({
        id: 'country-borders',
        type: 'line',
        source: 'countries',
        paint: {
          'line-color': [
            'case',
            ['==', ['get', 'iso3'], selectedCountry],
            '#dce8f2',
            '#303a44',
          ],
          'line-width': [
            'case',
            ['==', ['get', 'iso3'], selectedCountry],
            1.8,
            0.55,
          ],
          'line-opacity': 0.9,
        },
      })

      map.on('mousemove', 'country-fill', (event) => {
        const iso3 = String(event.features?.[0]?.properties?.iso3 ?? '')
        map.getCanvas().style.cursor = registeredRef.current.has(iso3) ? 'pointer' : ''
      })

      map.on('mouseleave', 'country-fill', () => {
        map.getCanvas().style.cursor = ''
      })

      map.on('click', 'country-fill', (event) => {
        const iso3 = String(event.features?.[0]?.properties?.iso3 ?? '')
        if (registeredRef.current.has(iso3)) onSelectRef.current(iso3)
      })
    })

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map?.isStyleLoaded()) return

    map.setPaintProperty('country-fill', 'fill-color', [
      'case',
      ['==', ['get', 'iso3'], selectedCountry],
      '#8ea5bc',
      ['!=', ['get', 'iso3'], ''],
      '#40505f',
      '#171d24',
    ])

    map.setPaintProperty('country-borders', 'line-color', [
      'case',
      ['==', ['get', 'iso3'], selectedCountry],
      '#dce8f2',
      '#303a44',
    ])
  }, [selectedCountry])

  return (
    <section className="worldMapSection" aria-label="World country map">
      <div className="dimensionHeader">
        <div>
          <div className="label">WORLD VIEW</div>
          <h3>Registered country coverage</h3>
        </div>
        <span>local geometry · click a covered country</span>
      </div>

      <div className="worldMapFrame">
        <div ref={containerRef} className="worldMapCanvas" data-testid="world-map">
          {mapUnavailable && (
            <div className="worldMapFallback">
              Map rendering unavailable · country navigation remains active
            </div>
          )}
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
