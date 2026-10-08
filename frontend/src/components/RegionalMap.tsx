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

type SourceNativeProperties = {
  geo_id?: string
  country_iso3?: string
  geography_system?: string
  geo_level?: string
  source_geo_code?: string
  name?: string
}

type SourceNativeFeature = GeoJSON.Feature<
  GeoJSON.Polygon | GeoJSON.MultiPolygon,
  SourceNativeProperties
>

type RegionalMapProps = {
  apiBase: string
  countryIso3: string
  countryIso2: string
  countryCenter?: { lat: number; lon: number } | null
  selectedRegion: string | null
  selectedCity: string | null
  selectableCountryIso2?: string[]
  onSelectCountry?: (countryIso2: string) => void
  onSelectRegion: (
    regionId: string,
    regionName: string,
    level: number | string,
    system?: string,
  ) => void
  onSelectCity: (cityCode: string, cityName: string) => void
}

const GISCO_BASE = 'https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson'
const GISCO_NUTS0_URL = `${GISCO_BASE}/NUTS_RG_20M_2024_4326_LEVL_0.geojson`
const GISCO_NUTS2_URL = `${GISCO_BASE}/NUTS_RG_20M_2024_4326_LEVL_2.geojson`
const GISCO_NUTS3_URL = `${GISCO_BASE}/NUTS_RG_20M_2024_4326_LEVL_3.geojson`
const GISCO_URBAN_AUDIT_CITY_URL = 'https://gisco-services.ec.europa.eu/distribution/v2/urau/geojson/URAU_LB_2024_4326_CITIES.geojson'
const REGIONS_VISIBLE_ZOOM = 5.5
const NUTS3_VISIBLE_ZOOM = 7
const CITIES_VISIBLE_ZOOM = 8.5


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
  apiBase,
  countryIso3,
  countryIso2,
  countryCenter = null,
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
  const nuts3LayerRef = useRef<L.GeoJSON | null>(null)
  const cityLayerRef = useRef<L.LayerGroup | null>(null)
  const sourceNativeLayerRef = useRef<L.GeoJSON | null>(null)
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [zoom, setZoom] = useState(3)
  const [subnationalAvailable, setSubnationalAvailable] = useState(true)
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
    nuts3LayerRef.current?.remove()
    cityLayerRef.current?.remove()
    sourceNativeLayerRef.current?.remove()
    countryLayerRef.current = null
    regionLayerRef.current = null
    nuts3LayerRef.current = null
    cityLayerRef.current = null
    sourceNativeLayerRef.current = null

    Promise.all([
      loadGeoJson(GISCO_NUTS0_URL),
      loadGeoJson(GISCO_NUTS2_URL),
      loadGeoJson(GISCO_NUTS3_URL),
      loadGeoJson(GISCO_URBAN_AUDIT_CITY_URL),
      loadGeoJson(
        `${apiBase}/api/geographies/geometry?country_iso3=${encodeURIComponent(countryIso3)}`,
      ).catch(() => ({
        type: 'FeatureCollection',
        features: [],
      } as GeoJSON.FeatureCollection)),
    ])
      .then(([countriesData, regionsData, nuts3Data, citiesData, sourceNativeData]) => {
        if (cancelled) return

        const countries = countriesData.features as CountryFeature[]
        const regions = (regionsData.features as RegionFeature[])
          .filter((feature) =>
            feature.properties?.CNTR_CODE === countryIso2
            && Number(feature.properties?.LEVL_CODE ?? 2) === 2
          )
        const nuts3Regions = (nuts3Data.features as RegionFeature[])
          .filter((feature) =>
            feature.properties?.CNTR_CODE === countryIso2
            && Number(feature.properties?.LEVL_CODE ?? 3) === 3
          )

        const countryCollection: GeoJSON.FeatureCollection = {
          type: 'FeatureCollection',
          features: countries,
        }

        const regionCollection: GeoJSON.FeatureCollection = {
          type: 'FeatureCollection',
          features: regions,
        }
        const nuts3Collection: GeoJSON.FeatureCollection = {
          type: 'FeatureCollection',
          features: nuts3Regions,
        }

        const selectableCountries = new Set(selectableCountryIso2)
        const cityFeatures = (citiesData.features as CityFeature[])
          .filter((feature) => {
            const code = cityCode(feature)
            return code.startsWith(countryIso2) && code.endsWith('C')
          })

        const sourceNativeFeatures = (
          sourceNativeData.features as SourceNativeFeature[]
        ).filter((feature) => {
          const system = feature.properties?.geography_system ?? ''
          return !['NUTS_2024', 'URBAN_AUDIT_2024'].includes(system)
        })

        const hasCountryGeometry = countries.some(
          (feature) => feature.properties?.CNTR_CODE === countryIso2,
        )
        const hasSubnational = (
          regions.length > 0
          || nuts3Regions.length > 0
          || cityFeatures.length > 0
          || sourceNativeFeatures.length > 0
        )
        setSubnationalAvailable(hasSubnational)

        if (!hasCountryGeometry && countryCenter) {
          map.setView(
            [countryCenter.lat, countryCenter.lon],
            5,
            { animate: false },
          )
        }

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

        const sourceNativeCollection: GeoJSON.FeatureCollection = {
          type: 'FeatureCollection',
          features: sourceNativeFeatures,
        }

        const sourceNativeLayer = L.geoJSON(
          sourceNativeCollection,
          {
            style: (feature) => {
              const native = feature as SourceNativeFeature | undefined
              const id = native?.properties?.source_geo_code ?? ''
              const selected = id === selectedRegion
              const level = native?.properties?.geo_level ?? ''
              const urban = ['city', 'fua'].includes(level.toLowerCase())
              return {
                className: selected
                  ? 'sourceNativeBoundary selectedSourceNativeBoundary'
                  : 'sourceNativeBoundary',
                color: selected ? '#ffffff' : urban ? '#74e6cf' : '#e2b66f',
                weight: selected ? 3.4 : 1.6,
                opacity: selected ? 1 : 0.88,
                fillColor: selected ? '#19b7d8' : urban ? '#2a9f8c' : '#a66e2c',
                fillOpacity: selected ? 0.28 : 0.07,
              }
            },
            interactive: true,
            onEachFeature: (feature, layer) => {
              const native = feature as SourceNativeFeature
              const props = native.properties ?? {}
              const id = props.source_geo_code ?? ''
              const level = props.geo_level ?? 'region'
              const system = props.geography_system ?? 'SOURCE_NATIVE'
              const name = props.name ?? id

              layer.bindTooltip(
                `${name} · ${id} · ${level.toUpperCase()} · ${system}`,
                {
                  sticky: true,
                  direction: 'top',
                  className: 'augurMapTooltip',
                },
              )
              layer.on('click', () => {
                onSelectRegionRef.current(id, name, level, system)
                const bounds = (layer as L.Polygon).getBounds()
                if (bounds.isValid()) {
                  map.fitBounds(bounds, { padding: [34, 34], maxZoom: 8.5 })
                }
              })
            },
          },
        )

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

        const nuts3Layer = L.geoJSON(nuts3Collection, {
          style: (feature) => {
            const region = feature as RegionFeature | undefined
            const id = region?.properties?.NUTS_ID ?? ''
            const selected = id === selectedRegion
            return {
              className: selected ? 'nuts3Boundary selectedNuts3Boundary' : 'nuts3Boundary',
              color: selected ? '#ffffff' : '#9dcfe8',
              weight: selected ? 3 : 1.1,
              opacity: selected ? 1 : 0.78,
              fillColor: selected ? '#16c7f2' : '#2b6d8b',
              fillOpacity: selected ? 0.30 : 0.035,
            }
          },
          interactive: true,
          onEachFeature: (feature, layer) => {
            const region = feature as RegionFeature
            const id = region.properties?.NUTS_ID ?? ''
            const name = regionName(region)

            layer.bindTooltip(`${name} · ${id} · NUTS 3`, {
              sticky: true,
              direction: 'top',
              className: 'augurMapTooltip',
            })

            layer.on('click', () => {
              onSelectRegionRef.current(id, name, 3)
              const bounds = (layer as L.Polygon).getBounds()
              if (bounds.isValid()) {
                map.fitBounds(bounds, { padding: [34, 34], maxZoom: 8.5 })
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
        nuts3LayerRef.current = nuts3Layer
        cityLayerRef.current = cityLayer
        sourceNativeLayerRef.current = sourceNativeLayer

        const redrawProgressiveLayers = () => {
          map.invalidateSize()

          regionLayer.eachLayer((layer) => {
            if (layer instanceof L.Path) layer.redraw()
          })
          nuts3Layer.eachLayer((layer) => {
            if (layer instanceof L.Path) layer.redraw()
          })
          cityLayer.eachLayer((layer) => {
            if (layer instanceof L.CircleMarker) layer.redraw()
          })
        }

        const applyProgressiveLayers = () => {
          const currentZoom = map.getZoom()

          if (currentZoom >= REGIONS_VISIBLE_ZOOM) {
            if (!map.hasLayer(sourceNativeLayer)) sourceNativeLayer.addTo(map)
            if (!map.hasLayer(regionLayer)) regionLayer.addTo(map)
          } else {
            if (map.hasLayer(sourceNativeLayer)) map.removeLayer(sourceNativeLayer)
            if (map.hasLayer(regionLayer)) map.removeLayer(regionLayer)
          }

          if (currentZoom >= NUTS3_VISIBLE_ZOOM) {
            if (!map.hasLayer(nuts3Layer)) nuts3Layer.addTo(map)
          } else if (map.hasLayer(nuts3Layer)) {
            map.removeLayer(nuts3Layer)
          }

          if (currentZoom >= CITIES_VISIBLE_ZOOM) {
            if (!map.hasLayer(cityLayer)) cityLayer.addTo(map)
          } else if (map.hasLayer(cityLayer)) {
            map.removeLayer(cityLayer)
          }

          requestAnimationFrame(redrawProgressiveLayers)
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
  }, [
    apiBase,
    countryIso3,
    countryIso2,
    countryCenter?.lat,
    countryCenter?.lon,
    selectableCountryKey,
  ])

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
    const layer = nuts3LayerRef.current
    if (!layer) return

    layer.setStyle((feature) => {
      const region = feature as RegionFeature | undefined
      const id = region?.properties?.NUTS_ID ?? ''
      const selected = id === selectedRegion
      return {
        className: selected ? 'nuts3Boundary selectedNuts3Boundary' : 'nuts3Boundary',
        color: selected ? '#ffffff' : '#9dcfe8',
        weight: selected ? 3 : 1.1,
        opacity: selected ? 1 : 0.78,
        fillColor: selected ? '#16c7f2' : '#2b6d8b',
        fillOpacity: selected ? 0.30 : 0.035,
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
          {!subnationalAvailable
            ? 'No integrated subnational source for this country yet'
            : zoom >= CITIES_VISIBLE_ZOOM
              ? 'Urban Audit cities + NUTS 3 visible'
              : zoom >= NUTS3_VISIBLE_ZOOM
                ? 'NUTS 3 safety context visible · zoom in for cities'
                : zoom >= REGIONS_VISIBLE_ZOOM
                  ? 'NUTS 2 regions visible · zoom in for NUTS 3'
                  : 'Zoom in to reveal available regional detail'}
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
        <button
          type="button"
          onClick={() => {
            if (subnationalAvailable) {
              zoomToCountry()
              return
            }
            if (countryCenter && mapRef.current) {
              mapRef.current.setView(
                [countryCenter.lat, countryCenter.lon],
                5,
                { animate: false },
              )
            }
          }}
          disabled={status !== 'ready'}
        >
          Focus country
        </button>
      </div>

      <small className="regionalMapSource">
        Base map: OpenStreetMap · European subnational overlays: Eurostat GISCO NUTS 2024 + Urban Audit 2024 · © EuroGeographics
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
