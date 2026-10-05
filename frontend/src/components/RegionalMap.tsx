import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

type MapProperties = {
  NUTS_ID?: string
  NUTS_NAME?: string
  NAME_LATN?: string
  CNTR_CODE?: string
  LEVL_CODE?: number
}

type RegionFeature = GeoJSON.Feature<
  GeoJSON.Polygon | GeoJSON.MultiPolygon,
  MapProperties
>

type CountryFeature = GeoJSON.Feature<
  GeoJSON.Polygon | GeoJSON.MultiPolygon,
  MapProperties
>

type CityMarker = {
  name: string
  lon: number
  lat: number
}

type RegionalMapProps = {
  countryIso2: string
  selectedRegion: string | null
  selectableCountryIso2?: string[]
  onSelectCountry?: (countryIso2: string) => void
  onSelectRegion: (regionId: string, regionName: string, level: number) => void
  cities?: CityMarker[]
}

const GISCO_BASE = 'https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson'
const GISCO_NUTS0_URL = `${GISCO_BASE}/NUTS_RG_20M_2024_4326_LEVL_0.geojson`
const GISCO_NUTS2_URL = `${GISCO_BASE}/NUTS_RG_20M_2024_4326_LEVL_2.geojson`
const REGIONS_VISIBLE_ZOOM = 5.5
const CITIES_VISIBLE_ZOOM = 6

const EUROPE_VIEW: L.LatLngExpression = [50.5, 8.5]

function countryName(feature: CountryFeature) {
  return feature.properties?.NAME_LATN
    ?? feature.properties?.NUTS_NAME
    ?? feature.properties?.CNTR_CODE
    ?? 'Country'
}

function regionName(feature: RegionFeature) {
  return feature.properties?.NAME_LATN
    ?? feature.properties?.NUTS_NAME
    ?? feature.properties?.NUTS_ID
    ?? 'Region'
}

export default function RegionalMap({
  countryIso2,
  selectedRegion,
  selectableCountryIso2 = [],
  onSelectCountry,
  onSelectRegion,
  cities = [],
}: RegionalMapProps) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const onSelectCountryRef = useRef(onSelectCountry)
  const onSelectRegionRef = useRef(onSelectRegion)
  const countryLayerRef = useRef<L.GeoJSON | null>(null)
  const regionLayerRef = useRef<L.GeoJSON | null>(null)
  const cityLayerRef = useRef<L.LayerGroup | null>(null)
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [zoom, setZoom] = useState(3)
  const selectableCountryKey = selectableCountryIso2.join(',')

  useEffect(() => {
    onSelectCountryRef.current = onSelectCountry
  }, [onSelectCountry])

  useEffect(() => {
    onSelectRegionRef.current = onSelectRegion
  }, [onSelectRegion])

  useEffect(() => {
    if (!hostRef.current || mapRef.current) return

    const map = L.map(hostRef.current, {
      center: EUROPE_VIEW,
      zoom: 3,
      minZoom: 2,
      maxZoom: 10,
      zoomSnap: 0.5,
      zoomDelta: 0.5,
      wheelPxPerZoomLevel: 90,
      attributionControl: true,
      worldCopyJump: true,
    })

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
      referrerPolicy: 'strict-origin-when-cross-origin',
    }).addTo(map)

    map.attributionControl.setPrefix('Leaflet')
    map.on('zoomend', () => setZoom(map.getZoom()))

    mapRef.current = map

    const resizeObserver = new ResizeObserver(() => map.invalidateSize())
    resizeObserver.observe(hostRef.current)

    return () => {
      resizeObserver.disconnect()
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    const controller = new AbortController()
    let progressiveHandler: (() => void) | null = null
    setStatus('loading')
    map.setView(EUROPE_VIEW, 3)

    countryLayerRef.current?.remove()
    regionLayerRef.current?.remove()
    cityLayerRef.current?.remove()
    countryLayerRef.current = null
    regionLayerRef.current = null
    cityLayerRef.current = null

    Promise.all([
      fetch(GISCO_NUTS0_URL, { signal: controller.signal }).then((response) => {
        if (!response.ok) throw new Error(`GISCO NUTS0 HTTP ${response.status}`)
        return response.json() as Promise<GeoJSON.FeatureCollection>
      }),
      fetch(GISCO_NUTS2_URL, { signal: controller.signal }).then((response) => {
        if (!response.ok) throw new Error(`GISCO NUTS2 HTTP ${response.status}`)
        return response.json() as Promise<GeoJSON.FeatureCollection>
      }),
    ])
      .then(([countriesData, regionsData]) => {
        if (controller.signal.aborted) return

        const countries = countriesData.features as CountryFeature[]
        const regions = (regionsData.features as RegionFeature[])
          .filter((feature) =>
            feature.properties?.CNTR_CODE === countryIso2
            && Number(feature.properties?.LEVL_CODE ?? 2) === 2
          )

        const countryCollection: GeoJSON.FeatureCollection = {
          type: 'FeatureCollection',
          features: countries,
        }

        const regionCollection: GeoJSON.FeatureCollection = {
          type: 'FeatureCollection',
          features: regions,
        }

        const selectableCountries = new Set(selectableCountryIso2)

        const countryLayer = L.geoJSON(countryCollection, {
          style: (feature) => {
            const country = feature as CountryFeature | undefined
            const code = country?.properties?.CNTR_CODE ?? ''
            const active = code === countryIso2
            const selectable = selectableCountries.has(code)
            return {
              className: [
                'countryBoundary',
                active ? 'selectedCountryBoundary' : '',
                selectable ? 'clickableCountryBoundary' : '',
              ].filter(Boolean).join(' '),
              color: active ? '#31a8d8' : '#71818c',
              weight: active ? 2 : 1,
              opacity: active ? 0.95 : 0.55,
              fillColor: active ? '#2587af' : '#b6c0c6',
              fillOpacity: active ? 0.16 : 0.04,
            }
          },
          onEachFeature: (feature, layer) => {
            const country = feature as CountryFeature
            const code = country.properties?.CNTR_CODE ?? ''
            const name = countryName(country)

            if (!selectableCountries.has(code)) return

            layer.bindTooltip(`${name} · ${code}`, {
              sticky: true,
              direction: 'top',
              className: 'augurMapTooltip',
            })

            const selectCountry = () => onSelectCountryRef.current?.(code)
            layer.on('click', selectCountry)
            layer.on('add', () => {
              const element = (layer as L.Path).getElement()
              if (!element) return
              element.setAttribute('role', 'button')
              element.setAttribute('aria-label', `${name} country`)
              element.setAttribute('tabindex', '0')
              element.addEventListener('keydown', (event: Event) => {
                const keyboardEvent = event as KeyboardEvent
                if (keyboardEvent.key === 'Enter' || keyboardEvent.key === ' ') {
                  keyboardEvent.preventDefault()
                  selectCountry()
                }
              })
            })
          },
        }).addTo(map)

        const regionLayer = L.geoJSON(regionCollection, {
          style: (feature) => {
            const region = feature as RegionFeature | undefined
            const id = region?.properties?.NUTS_ID ?? ''
            const selected = id === selectedRegion
            return {
              className: selected ? 'nuts2Boundary selectedNuts2Boundary' : 'nuts2Boundary',
              color: selected ? '#ffffff' : '#75d4ff',
              weight: selected ? 3.6 : 1.8,
              opacity: selected ? 1 : 0.92,
              fillColor: selected ? '#13b9ed' : '#2085ad',
              fillOpacity: selected ? 0.30 : 0.08,
            }
          },
          onEachFeature: (feature, layer) => {
            const region = feature as RegionFeature
            const id = region.properties?.NUTS_ID ?? ''
            const name = regionName(region)
            layer.bindTooltip(`${name} · ${id}`, {
              sticky: true,
              direction: 'top',
              className: 'augurMapTooltip',
            })
            const selectRegion = () => {
              onSelectRegionRef.current(id, name, 2)
              const bounds = (layer as L.Polygon).getBounds()
              if (bounds.isValid()) {
                map.fitBounds(bounds, { padding: [34, 34], maxZoom: 7 })
              }
            }

            layer.on('click', selectRegion)
            layer.on('add', () => {
              const element = (layer as L.Path).getElement()
              if (!element) return
              element.setAttribute('role', 'button')
              element.setAttribute('aria-label', `${name} · ${id}`)
              element.setAttribute('tabindex', '0')
              element.addEventListener('keydown', (event: Event) => {
                const keyboardEvent = event as KeyboardEvent
                if (keyboardEvent.key === 'Enter' || keyboardEvent.key === ' ') {
                  keyboardEvent.preventDefault()
                  selectRegion()
                }
              })
            })
          },
        })

        const cityLayer = L.layerGroup(
          cities.map((city) =>
            L.marker([city.lat, city.lon], {
              interactive: false,
              icon: L.divIcon({
                className: 'regionalCityMarker leafletCityMarker',
                html: `<span class="cityDot"></span><span class="cityLabel">${city.name}</span>`,
                iconSize: [90, 24],
                iconAnchor: [6, 12],
              }),
            })
          ),
        )

        countryLayerRef.current = countryLayer
        regionLayerRef.current = regionLayer
        cityLayerRef.current = cityLayer

        const applyProgressiveLayers = () => {
          const currentZoom = map.getZoom()

          if (currentZoom >= REGIONS_VISIBLE_ZOOM) {
            if (!map.hasLayer(regionLayer)) regionLayer.addTo(map)
          } else if (map.hasLayer(regionLayer)) {
            map.removeLayer(regionLayer)
          }

          if (currentZoom >= CITIES_VISIBLE_ZOOM) {
            if (!map.hasLayer(cityLayer)) cityLayer.addTo(map)
          } else if (map.hasLayer(cityLayer)) {
            map.removeLayer(cityLayer)
          }
        }

        progressiveHandler = applyProgressiveLayers
        map.on('zoomend', applyProgressiveLayers)
        applyProgressiveLayers()
        setStatus('ready')

      })
      .catch((error) => {
        if ((error as Error).name === 'AbortError') return
        setStatus('error')
      })

    return () => {
      controller.abort()
      if (progressiveHandler) map.off('zoomend', progressiveHandler)
    }
  }, [countryIso2, selectableCountryKey])

  useEffect(() => {
    const layer = regionLayerRef.current
    if (!layer) return

    layer.setStyle((feature) => {
      const region = feature as RegionFeature | undefined
      const id = region?.properties?.NUTS_ID ?? ''
      const selected = id === selectedRegion
      return {
        className: selected ? 'nuts2Boundary selectedNuts2Boundary' : 'nuts2Boundary',
        color: selected ? '#ffffff' : '#75d4ff',
        weight: selected ? 3.6 : 1.8,
        opacity: selected ? 1 : 0.92,
        fillColor: selected ? '#13b9ed' : '#2085ad',
        fillOpacity: selected ? 0.30 : 0.08,
      }
    })
  }, [selectedRegion])

  const zoomToCountry = () => {
    const map = mapRef.current
    const countryLayer = countryLayerRef.current
    if (!map || !countryLayer) return

    const selectedLayers = countryLayer.getLayers().filter((layer) => {
      const feature = (layer as L.Layer & { feature?: CountryFeature }).feature
      return feature?.properties?.CNTR_CODE === countryIso2
    })

    if (!selectedLayers.length) return

    const group = L.featureGroup(selectedLayers as L.Layer[])
    map.fitBounds(group.getBounds(), { padding: [24, 24], maxZoom: 6 })
    if (map.getZoom() < REGIONS_VISIBLE_ZOOM) {
      map.setZoom(REGIONS_VISIBLE_ZOOM)
    }
  }

  const resetToEurope = () => {
    mapRef.current?.setView(EUROPE_VIEW, 3)
  }

  return (
    <section className="regionalMapView" aria-label="Interactive geographic map">
      <div className="mapZoomHint">
        <span>Zoom {zoom.toFixed(1)}</span>
        <strong>{zoom >= REGIONS_VISIBLE_ZOOM ? 'NUTS 2 regions visible' : 'Zoom in to reveal NUTS 2 regions'}</strong>
      </div>

      <div
        ref={hostRef}
        className="regionalMapCanvas leafletAugurMap"
        data-testid="regional-map"
        aria-label="Interactive map with progressive regional detail"
      />

      <div className="regionalMapActions">
        <button type="button" onClick={resetToEurope}>Europe</button>
        <button type="button" onClick={zoomToCountry}>Focus country</button>
      </div>

      <small className="regionalMapSource">
        Base map: OpenStreetMap · boundaries: Eurostat GISCO NUTS 2024 · © EuroGeographics · regions appear from zoom {REGIONS_VISIBLE_ZOOM}
      </small>

      {status === 'loading' && <div className="regionalMapLoading">Loading geographic layers…</div>}
      {status === 'error' && (
        <div className="regionalMapLoading error">
          Map layers unavailable. Country-level evidence remains active.
        </div>
      )}
    </section>
  )
}
