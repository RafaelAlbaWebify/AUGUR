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

type CityFeature = GeoJSON.Feature<
  GeoJSON.Point,
  Record<string, unknown>
>

type RegionalMapProps = {
  countryIso2: string
  selectedRegion: string | null
  selectedCity: string | null
  selectableCountryIso2?: string[]
  onSelectCountry?: (countryIso2: string) => void
  onSelectRegion: (regionId: string, regionName: string, level: number) => void
  onSelectCity: (cityCode: string, cityName: string) => void
}

const GISCO_BASE = 'https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson'
const GISCO_NUTS0_URL = `${GISCO_BASE}/NUTS_RG_20M_2024_4326_LEVL_0.geojson`
const GISCO_NUTS2_URL = `${GISCO_BASE}/NUTS_RG_20M_2024_4326_LEVL_2.geojson`
const GISCO_URBAN_AUDIT_CITY_URL = 'https://gisco-services.ec.europa.eu/distribution/v2/urau/geojson/URAU_LB_2024_4326_CITIES.geojson'
const REGIONS_VISIBLE_ZOOM = 5.5
const CITIES_VISIBLE_ZOOM = 7.5


const geoJsonCache = new Map<string, Promise<GeoJSON.FeatureCollection>>()

function loadGeoJson(url: string) {
  const cached = geoJsonCache.get(url)
  if (cached) return cached

  const request = fetch(url)
    .then((response) => {
      if (!response.ok) throw new Error(`GISCO HTTP ${response.status}: ${url}`)
      return response.json() as Promise<GeoJSON.FeatureCollection>
    })
    .catch((error) => {
      geoJsonCache.delete(url)
      throw error
    })

  geoJsonCache.set(url, request)
  return request
}

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

function cityCode(feature: CityFeature) {
  const props = feature.properties ?? {}
  const candidates = [
    props.URAU_CODE,
    props.URAU_ID,
    props.CITY_CODE,
    props.CODE,
    feature.id,
  ]

  return candidates
    .map((value) => typeof value === 'string' ? value.toUpperCase() : '')
    .find((value) => /^[A-Z]{2}\d{3}C$/.test(value))
    ?? ''
}

function cityName(feature: CityFeature) {
  const props = feature.properties ?? {}
  const candidates = [
    props.NAME_LATN,
    props.URAU_NAME,
    props.CITY_NAME,
    props.NAME,
    props.LABEL,
  ]

  return candidates.find((value) => typeof value === 'string' && value.trim())
    ?.toString()
    ?? cityCode(feature)
    ?? 'City'
}

export default function RegionalMap({
  countryIso2,
  selectedRegion,
  selectedCity,
  selectableCountryIso2 = [],
  onSelectCountry,
  onSelectRegion,
  onSelectCity,
}: RegionalMapProps) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const onSelectCountryRef = useRef(onSelectCountry)
  const onSelectRegionRef = useRef(onSelectRegion)
  const onSelectCityRef = useRef(onSelectCity)
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
    onSelectCityRef.current = onSelectCity
  }, [onSelectCity])

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
    const syncZoom = () => setZoom(map.getZoom())
    map.on('zoomend', syncZoom)

    mapRef.current = map

    const resizeObserver = new ResizeObserver(() => map.invalidateSize())
    resizeObserver.observe(hostRef.current)

    return () => {
      resizeObserver.disconnect()
      map.off('zoomend', syncZoom)
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    let cancelled = false
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

    Promise.all([
      loadGeoJson(GISCO_NUTS0_URL),
      loadGeoJson(GISCO_NUTS2_URL),
      loadGeoJson(GISCO_URBAN_AUDIT_CITY_URL),
    ])
      .then(([countriesData, regionsData, citiesData]) => {
        if (cancelled) return

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
        const cityFeatures = (citiesData.features as CityFeature[])
          .filter((feature) => {
            const code = cityCode(feature)
            return code.startsWith(countryIso2) && code.endsWith('C')
          })

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
          interactive: true,
          onEachFeature: (feature, layer) => {
            const country = feature as CountryFeature
            const code = country.properties?.CNTR_CODE ?? ''
            if (!selectableCountries.has(code)) return

            const name = countryName(country)
            layer.bindTooltip(`${name} · ${code}`, {
              sticky: true,
              direction: 'top',
              className: 'augurMapTooltip',
            })
            layer.on('click', () => {
              onSelectCountryRef.current?.(code)
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
          interactive: true,
          onEachFeature: (feature, layer) => {
            const region = feature as RegionFeature
            const id = region.properties?.NUTS_ID ?? ''
            const name = regionName(region)

            layer.bindTooltip(`${name} · ${id}`, {
              sticky: true,
              direction: 'top',
              className: 'augurMapTooltip',
            })

            layer.on('click', () => {
              onSelectRegionRef.current(id, name, 2)
              const bounds = (layer as L.Polygon).getBounds()
              if (bounds.isValid()) {
                map.fitBounds(bounds, { padding: [34, 34], maxZoom: 7 })
              }
            })
          },
        })

        const cityLayer = L.layerGroup(
          cityFeatures.map((feature) => {
            const [lon, lat] = feature.geometry.coordinates
            const code = cityCode(feature)
            const name = cityName(feature)
            const selected = code === selectedCity

            const marker = L.circleMarker([lat, lon], {
              radius: selected ? 7 : 5,
              color: selected ? '#ffffff' : '#7de3ff',
              weight: selected ? 2.5 : 1.5,
              fillColor: selected ? '#16c7f2' : '#1a95b8',
              fillOpacity: selected ? 0.96 : 0.82,
              className: selected ? 'urbanAuditCity selectedUrbanAuditCity' : 'urbanAuditCity',
            })

            ;(marker as L.CircleMarker & { augurCityCode?: string }).augurCityCode = code

            marker.bindTooltip(`${name} · ${code}`, {
              sticky: true,
              direction: 'top',
              className: 'augurMapTooltip',
            })

            marker.on('click', () => {
              onSelectCityRef.current(code, name)
              map.setView([lat, lon], Math.max(map.getZoom(), 9), { animate: false })
            })

            return marker
          }),
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
        if (cancelled) return
        setStatus('error')
      })

    return () => {
      cancelled = true
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

  useEffect(() => {
    const layer = cityLayerRef.current
    if (!layer) return

    layer.eachLayer((item) => {
      if (!(item instanceof L.CircleMarker)) return
      const marker = item as L.CircleMarker & { augurCityCode?: string }
      const selected = marker.augurCityCode === selectedCity
      marker.setRadius(selected ? 7 : 5)
      marker.setStyle({
        color: selected ? '#ffffff' : '#7de3ff',
        weight: selected ? 2.5 : 1.5,
        fillColor: selected ? '#16c7f2' : '#1a95b8',
        fillOpacity: selected ? 0.96 : 0.82,
      })
    })
  }, [selectedCity])

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

    if (!map.hasLayer(regionLayer)) {
      regionLayer.addTo(map)
    }

    const redrawRegions = () => {
      map.invalidateSize()
      regionLayer.eachLayer((layer) => {
        if (layer instanceof L.Path) layer.redraw()
      })
    }

    map.once('moveend', redrawRegions)

    const group = L.featureGroup(selectedLayers as L.Layer[])
    map.fitBounds(group.getBounds(), {
      padding: [24, 24],
      maxZoom: 6,
      animate: false,
    })

    if (map.getZoom() < REGIONS_VISIBLE_ZOOM) {
      map.setZoom(REGIONS_VISIBLE_ZOOM, { animate: false })
    }

    requestAnimationFrame(redrawRegions)
  }

  const resetToEurope = () => {
    if (status !== 'ready') return
    mapRef.current?.setView(EUROPE_VIEW, 3)
  }

  return (
    <section className="regionalMapView" aria-label="Interactive geographic map">
      <div className="mapZoomHint">
        <span>Zoom {zoom.toFixed(1)}</span>
        <strong>
          {zoom >= CITIES_VISIBLE_ZOOM
            ? 'Urban Audit cities visible'
            : zoom >= REGIONS_VISIBLE_ZOOM
              ? 'NUTS 2 regions visible · zoom in for cities'
              : 'Zoom in to reveal NUTS 2 regions'}
        </strong>
      </div>

      <div
        ref={hostRef}
        className="regionalMapCanvas leafletAugurMap"
        data-testid="regional-map"
        data-map-status={status}
        data-map-zoom={zoom.toFixed(1)}
        aria-label="Interactive map with progressive regional detail"
      />

      <div className="regionalMapActions">
        <button type="button" onClick={resetToEurope} disabled={status !== 'ready'}>Europe</button>
        <button type="button" onClick={zoomToCountry} disabled={status !== 'ready'}>Focus country</button>
      </div>

      <small className="regionalMapSource">
        Base map: OpenStreetMap · Eurostat GISCO NUTS 2024 + Urban Audit 2024 · © EuroGeographics · regions from zoom {REGIONS_VISIBLE_ZOOM} · official Urban Audit cities from zoom {CITIES_VISIBLE_ZOOM}
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
