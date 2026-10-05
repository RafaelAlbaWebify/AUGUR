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

function pointInRing(lng: number, lat: number, ring: GeoJSON.Position[]) {
  let inside = false

  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0]
    const yi = ring[i][1]
    const xj = ring[j][0]
    const yj = ring[j][1]

    const intersects =
      ((yi > lat) !== (yj > lat))
      && (lng < ((xj - xi) * (lat - yi)) / ((yj - yi) || Number.EPSILON) + xi)

    if (intersects) inside = !inside
  }

  return inside
}

function pointInPolygon(
  lng: number,
  lat: number,
  polygon: GeoJSON.Position[][],
) {
  if (!polygon.length || !pointInRing(lng, lat, polygon[0])) return false

  for (let holeIndex = 1; holeIndex < polygon.length; holeIndex += 1) {
    if (pointInRing(lng, lat, polygon[holeIndex])) return false
  }

  return true
}

function featureContainsPoint(
  feature: CountryFeature | RegionFeature,
  lng: number,
  lat: number,
) {
  if (!feature.geometry) return false

  if (feature.geometry.type === 'Polygon') {
    return pointInPolygon(lng, lat, feature.geometry.coordinates)
  }

  return feature.geometry.coordinates.some((polygon) =>
    pointInPolygon(lng, lat, polygon)
  )
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
  const selectableCountryIso2Ref = useRef(selectableCountryIso2)
  const countryLayerRef = useRef<L.GeoJSON | null>(null)
  const regionLayerRef = useRef<L.GeoJSON | null>(null)
  const cityLayerRef = useRef<L.LayerGroup | null>(null)
  const countryFeaturesRef = useRef<CountryFeature[]>([])
  const regionFeaturesRef = useRef<RegionFeature[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [zoom, setZoom] = useState(3)
  const [center, setCenter] = useState({ lat: 50.5, lng: 8.5 })
  const selectableCountryKey = selectableCountryIso2.join(',')

  useEffect(() => {
    onSelectCountryRef.current = onSelectCountry
  }, [onSelectCountry])

  useEffect(() => {
    selectableCountryIso2Ref.current = selectableCountryIso2
  }, [selectableCountryKey])

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
    const syncViewState = () => {
      const currentCenter = map.getCenter()
      setZoom(map.getZoom())
      setCenter({ lat: currentCenter.lat, lng: currentCenter.lng })
    }
    map.on('zoomend', syncViewState)
    map.on('moveend', syncViewState)

    const handleMapClick = (event: L.LeafletMouseEvent) => {
      const { lat, lng } = event.latlng

      if (map.getZoom() >= REGIONS_VISIBLE_ZOOM) {
        const region = regionFeaturesRef.current.find((feature) =>
          featureContainsPoint(feature, lng, lat)
        )

        if (region) {
          const id = region.properties?.NUTS_ID ?? ''
          const name = regionName(region)
          onSelectRegionRef.current(id, name, 2)

          const bounds = L.geoJSON(region).getBounds()
          if (bounds.isValid()) {
            map.fitBounds(bounds, { padding: [34, 34], maxZoom: 7 })
          }
          return
        }
      }

      const country = countryFeaturesRef.current.find((feature) =>
        selectableCountryIso2Ref.current.includes(feature.properties?.CNTR_CODE ?? '')
        && featureContainsPoint(feature, lng, lat)
      )

      const code = country?.properties?.CNTR_CODE
      if (code) onSelectCountryRef.current?.(code)
    }

    const handleMapMouseMove = (event: L.LeafletMouseEvent) => {
      const { lat, lng } = event.latlng
      const overRegion = map.getZoom() >= REGIONS_VISIBLE_ZOOM
        && regionFeaturesRef.current.some((feature) => featureContainsPoint(feature, lng, lat))
      const overCountry = countryFeaturesRef.current.some((feature) =>
        selectableCountryIso2Ref.current.includes(feature.properties?.CNTR_CODE ?? '')
        && featureContainsPoint(feature, lng, lat)
      )

      map.getContainer().style.cursor = overRegion || overCountry ? 'pointer' : ''
    }

    map.on('click', handleMapClick)
    map.on('mousemove', handleMapMouseMove)
    mapRef.current = map

    const resizeObserver = new ResizeObserver(() => map.invalidateSize())
    resizeObserver.observe(hostRef.current)

    return () => {
      resizeObserver.disconnect()
      map.off('click', handleMapClick)
      map.off('mousemove', handleMapMouseMove)
      map.off('zoomend', syncViewState)
      map.off('moveend', syncViewState)
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
    map.getContainer().style.cursor = ''
    map.setView(EUROPE_VIEW, 3)

    countryLayerRef.current?.remove()
    regionLayerRef.current?.remove()
    cityLayerRef.current?.remove()
    countryLayerRef.current = null
    regionLayerRef.current = null
    cityLayerRef.current = null
    countryFeaturesRef.current = []
    regionFeaturesRef.current = []

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
        countryFeaturesRef.current = countries
        regionFeaturesRef.current = regions

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
          interactive: false,
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
          interactive: false,
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
        map.invalidateSize()
        map.fire('moveend')

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
    const regionLayer = regionLayerRef.current
    if (status !== 'ready' || !map || !countryLayer || !regionLayer) return

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
    if (!map.hasLayer(regionLayer)) {
      regionLayer.addTo(map)
    }
  }

  const resetToEurope = () => {
    if (status !== 'ready') return
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
        data-map-status={status}
        data-map-zoom={zoom.toFixed(1)}
        data-map-center-lat={center.lat.toFixed(6)}
        data-map-center-lng={center.lng.toFixed(6)}
        aria-label="Interactive map with progressive regional detail"
      />

      <div className="regionalMapActions">
        <button type="button" onClick={resetToEurope} disabled={status !== 'ready'}>Europe</button>
        <button type="button" onClick={zoomToCountry} disabled={status !== 'ready'}>Focus country</button>
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
