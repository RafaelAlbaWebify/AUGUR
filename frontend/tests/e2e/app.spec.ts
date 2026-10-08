import { expect, test, type Page } from '@playwright/test'

const countries = [
  { iso2: 'ES', iso3: 'ESP', name: 'Spain', region: 'Europe', subregion: 'Southern Europe', currency: 'EUR', eu_member: true, eurozone_member: true, oecd_member: true },
  { iso2: 'PT', iso3: 'PRT', name: 'Portugal', region: 'Europe', subregion: 'Southern Europe', currency: 'EUR', eu_member: true, eurozone_member: true, oecd_member: true },
  { iso2: 'IE', iso3: 'IRL', name: 'Ireland', region: 'Europe', subregion: 'Northern Europe', currency: 'EUR', eu_member: true, eurozone_member: true, oecd_member: true },
  { iso2: 'DE', iso3: 'DEU', name: 'Germany', region: 'Europe', subregion: 'Western Europe', currency: 'EUR', eu_member: true, eurozone_member: true, oecd_member: true, latitude: 52.52, longitude: 13.405, analysis_status: 'available' },
  { iso2: 'AU', iso3: 'AUS', name: 'Australia', region: 'East Asia & Pacific', subregion: null, currency: 'AUD', eu_member: false, eurozone_member: false, oecd_member: true, latitude: -35.2809, longitude: 149.13, analysis_status: 'available' },
]

function metric(country: string) {
  const value = country === 'ESP' ? 10.4 : country === 'PRT' ? 6.4 : 4.5
  return {
    country_iso3: country,
    indicator_id: 'unemployment_rate',
    name: 'Unemployment, total (% of total labor force)',
    dimension: 'productive_capacity',
    period: 2025,
    value,
    unit: 'percent',
    source_id: 'EUROSTAT',
  }
}

function overviewMetrics(country: string) {
  const base = metric(country)
  return [
    base,
    {
      country_iso3: country,
      indicator_id: 'actual_individual_consumption_index',
      name: 'Actual individual consumption per capita',
      dimension: 'prosperity',
      period: 2025,
      value: country === 'ESP' ? 91 : country === 'PRT' ? 87 : 100,
      unit: 'index_eu27_2020_100',
      source_id: 'EUROSTAT',
    },
    {
      country_iso3: country,
      indicator_id: 'real_gdp_per_capita',
      name: 'Real GDP per capita',
      dimension: 'prosperity',
      period: 2025,
      value: country === 'ESP' ? 32600 : country === 'PRT' ? 28300 : 61200,
      unit: 'constant_2015_usd_per_person',
      source_id: 'WORLD_BANK',
    },
    {
      country_iso3: country,
      indicator_id: 'imf_unemployment_rate',
      name: 'Unemployment rate (IMF WEO)',
      dimension: 'productive_capacity',
      period: 2025,
      value: country === 'ESP' ? 10.2 : country === 'PRT' ? 6.3 : 4.4,
      unit: 'percent',
      source_id: 'IMF',
    },
    {
      country_iso3: country,
      indicator_id: 'housing_cost_overburden_rate',
      name: 'Housing cost overburden rate',
      dimension: 'housing',
      period: 2024,
      value: country === 'ESP' ? 8.2 : country === 'PRT' ? 6.8 : 5.1,
      unit: 'percent',
      source_id: 'EUROSTAT',
    },
    {
      country_iso3: country,
      indicator_id: 'unmet_medical_needs',
      name: 'Unmet medical examination or treatment needs',
      dimension: 'human_systems',
      period: 2025,
      value: country === 'ESP' ? 2.4 : country === 'PRT' ? 3.9 : 4.7,
      unit: 'percent',
      source_id: 'EUROSTAT',
    },
    {
      country_iso3: country,
      indicator_id: 'life_expectancy',
      name: 'Life expectancy at birth',
      dimension: 'human_systems',
      period: 2024,
      value: country === 'ESP' ? 84.0 : country === 'PRT' ? 82.5 : 82.8,
      unit: 'years',
      source_id: 'UN_WPP',
    },
    {
      country_iso3: country,
      indicator_id: 'intentional_homicide_rate',
      name: 'Police-recorded intentional homicides',
      dimension: 'safety',
      period: 2024,
      value: country === 'ESP' ? 0.72 : country === 'PRT' ? 0.68 : 0.69,
      unit: 'per_100k_people',
      source_id: 'EUROSTAT',
    },
    {
      country_iso3: country,
      indicator_id: 'pm25_premature_death_rate',
      name: 'Premature deaths attributable to PM2.5 exposure',
      dimension: 'environment',
      period: 2023,
      value: country === 'ESP' ? 28 : country === 'PRT' ? 21 : 6,
      unit: 'per_100k_people',
      source_id: 'EUROSTAT',
    },
    {
      country_iso3: country,
      indicator_id: 'household_internet_access',
      name: 'Households with internet access',
      dimension: 'infrastructure',
      period: 2025,
      value: country === 'ESP' ? 97.43 : country === 'PRT' ? 91.08 : 95.51,
      unit: 'percent',
      source_id: 'EUROSTAT',
    },
    {
      country_iso3: country,
      indicator_id: 'tertiary_education_25_34',
      name: 'Tertiary education attainment (25–34)',
      dimension: 'human_systems',
      period: 2024,
      value: country === 'ESP' ? 52.0 : country === 'PRT' ? 43.0 : 63.0,
      unit: 'percent',
      source_id: 'EUROSTAT',
    },
    {
      country_iso3: country,
      indicator_id: 'population_65_plus_share',
      name: 'Population aged 65+',
      dimension: 'demography',
      period: 2025,
      value: country === 'ESP' ? 20.4 : country === 'PRT' ? 24.1 : 15.5,
      unit: 'percent',
      source_id: 'UN_WPP',
    },
    {
      country_iso3: country,
      indicator_id: 'energy_import_dependency',
      name: 'Energy import dependency',
      dimension: 'strategic_resilience',
      period: 2024,
      value: country === 'ESP' ? 68.2 : country === 'PRT' ? 66.5 : 67.1,
      unit: 'percent',
      source_id: 'EUROSTAT',
    },
  ]
}

function mockTrendFor(item: ReturnType<typeof overviewMetrics>[number]) {
  const contextual = item.indicator_id === 'population_65_plus_share'
  const improving = item.indicator_id !== 'population_65_plus_share'
  const lowerIsBetter = ['unemployment_rate', 'imf_unemployment_rate', 'housing_cost_overburden_rate', 'unmet_medical_needs', 'intentional_homicide_rate', 'pm25_premature_death_rate', 'energy_import_dependency'].includes(item.indicator_id)
  return {
    direction: contextual ? 'increase' : lowerIsBetter ? 'decrease' : 'increase',
    interpretation: contextual ? 'neutral_or_contextual' : improving ? 'improving' : 'stable',
    confidence: 'high',
    slope_per_year: lowerIsBetter ? -0.2 : 0.3,
    pct_change_1y: contextual ? 1.1 : lowerIsBetter ? -2.0 : 2.1,
    pct_change_3y: contextual ? 3.2 : lowerIsBetter ? -5.0 : 5.2,
    pct_change_5y: contextual ? 5.4 : lowerIsBetter ? -8.0 : 8.5,
    years_used: 6,
    target_status: null,
  }
}


async function mockApi(page: Page) {
  await page.route('https://gisco-services.ec.europa.eu/**', async route => {
    if (route.request().url().includes('URAU_LB_2024_4326_CITIES')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/geo+json',
        body: JSON.stringify({
          type: 'FeatureCollection',
          features: [
            {
              type: 'Feature',
              properties: { URAU_CODE: 'ES001C', URAU_NAME: 'Madrid', NAME_LATN: 'Madrid' },
              geometry: { type: 'Point', coordinates: [-3.7038, 40.4168] },
            },
            {
              type: 'Feature',
              properties: { URAU_CODE: 'PT001C', URAU_NAME: 'Lisboa', NAME_LATN: 'Lisboa' },
              geometry: { type: 'Point', coordinates: [-9.1393, 38.7223] },
            },
            {
              type: 'Feature',
              properties: { URAU_CODE: 'IE001C', URAU_NAME: 'Dublin', NAME_LATN: 'Dublin' },
              geometry: { type: 'Point', coordinates: [-6.2603, 53.3498] },
            },
          ],
        }),
      })
      return
    }

    if (route.request().url().includes('LEVL_0')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/geo+json',
        body: JSON.stringify({
          type: 'FeatureCollection',
          features: [
            {
              type: 'Feature',
              properties: { NUTS_ID: 'ES', NAME_LATN: 'Spain', NUTS_NAME: 'Spain', CNTR_CODE: 'ES', LEVL_CODE: 0 },
              geometry: { type: 'Polygon', coordinates: [[[-9.3, 43.8], [3.4, 43.8], [3.4, 36.0], [-7.1, 36.0], [-7.1, 37.2], [-7.0, 38.7], [-6.9, 41.9], [-8.2, 42.1], [-9.3, 43.8]]] },
            },
            {
              type: 'Feature',
              properties: { NUTS_ID: 'PT', NAME_LATN: 'Portugal', NUTS_NAME: 'Portugal', CNTR_CODE: 'PT', LEVL_CODE: 0 },
              geometry: { type: 'Polygon', coordinates: [[[-9.6, 36.8], [-6.1, 36.8], [-6.1, 42.2], [-9.6, 42.2], [-9.6, 36.8]]] },
            },
            {
              type: 'Feature',
              properties: { NUTS_ID: 'IE', NAME_LATN: 'Ireland', NUTS_NAME: 'Ireland', CNTR_CODE: 'IE', LEVL_CODE: 0 },
              geometry: { type: 'Polygon', coordinates: [[[-10.8, 51.3], [-5.3, 51.3], [-5.3, 55.5], [-10.8, 55.5], [-10.8, 51.3]]] },
            },
          ],
        }),
      })
      return
    }

    if (route.request().url().includes('LEVL_3')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/geo+json',
        body: JSON.stringify({
          type: 'FeatureCollection',
          features: [
            {
              type: 'Feature',
              properties: { NUTS_ID: 'ES120', NAME_LATN: 'Asturias', NUTS_NAME: 'Asturias', CNTR_CODE: 'ES', LEVL_CODE: 3 },
              geometry: { type: 'Polygon', coordinates: [[[-7.0, 42.7], [-4.5, 42.7], [-4.5, 43.7], [-7.0, 43.7], [-7.0, 42.7]]] },
            },
            {
              type: 'Feature',
              properties: { NUTS_ID: 'PT170', NAME_LATN: 'Área Metropolitana de Lisboa', NUTS_NAME: 'Área Metropolitana de Lisboa', CNTR_CODE: 'PT', LEVL_CODE: 3 },
              geometry: { type: 'Polygon', coordinates: [[[-9.6, 38.4], [-8.7, 38.4], [-8.7, 39.1], [-9.6, 39.1], [-9.6, 38.4]]] },
            },
            {
              type: 'Feature',
              properties: { NUTS_ID: 'IE061', NAME_LATN: 'Dublin', NUTS_NAME: 'Dublin', CNTR_CODE: 'IE', LEVL_CODE: 3 },
              geometry: { type: 'Polygon', coordinates: [[[-6.6, 53.1], [-6.0, 53.1], [-6.0, 53.6], [-6.6, 53.6], [-6.6, 53.1]]] },
            },
          ],
        }),
      })
      return
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/geo+json',
      body: JSON.stringify({
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES11', NAME_LATN: 'Galicia', NUTS_NAME: 'Galicia', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-9.3, 41.8], [-6.6, 41.8], [-6.7, 43.8], [-9.3, 43.8], [-9.3, 41.8]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES12', NAME_LATN: 'Principado de Asturias', NUTS_NAME: 'Principado de Asturias', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-7.0, 42.7], [-4.5, 42.7], [-4.5, 43.7], [-7.0, 43.7], [-7.0, 42.7]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES13', NAME_LATN: 'Cantabria', NUTS_NAME: 'Cantabria', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-4.5, 42.7], [-3.1, 42.7], [-3.1, 43.5], [-4.5, 43.5], [-4.5, 42.7]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES21', NAME_LATN: 'País Vasco', NUTS_NAME: 'País Vasco', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-3.1, 42.5], [-1.5, 42.5], [-1.5, 43.5], [-3.1, 43.5], [-3.1, 42.5]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES22', NAME_LATN: 'Navarra', NUTS_NAME: 'Navarra', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-1.8, 41.8], [-0.7, 41.8], [-0.7, 43.0], [-1.8, 43.0], [-1.8, 41.8]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES24', NAME_LATN: 'Aragón', NUTS_NAME: 'Aragón', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-1.6, 40.4], [0.9, 40.4], [0.9, 42.8], [-1.6, 42.8], [-1.6, 40.4]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES30', NAME_LATN: 'Comunidad de Madrid', NUTS_NAME: 'Comunidad de Madrid', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-4.6, 39.8], [-3.0, 39.8], [-3.0, 41.2], [-4.6, 41.2], [-4.6, 39.8]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES41', NAME_LATN: 'Castilla y León', NUTS_NAME: 'Castilla y León', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-7.7, 40.7], [-1.7, 40.7], [-1.7, 42.8], [-7.7, 42.8], [-7.7, 40.7]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES42', NAME_LATN: 'Castilla-La Mancha', NUTS_NAME: 'Castilla-La Mancha', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-5.0, 38.0], [-0.8, 38.0], [-0.8, 40.8], [-5.0, 40.8], [-5.0, 38.0]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES43', NAME_LATN: 'Extremadura', NUTS_NAME: 'Extremadura', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-7.6, 37.0], [-4.8, 37.0], [-4.8, 40.0], [-7.6, 40.0], [-7.6, 37.0]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES51', NAME_LATN: 'Cataluña', NUTS_NAME: 'Cataluña', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[0.2, 40.5], [3.3, 40.5], [3.3, 42.9], [0.2, 42.9], [0.2, 40.5]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES52', NAME_LATN: 'Comunitat Valenciana', NUTS_NAME: 'Comunitat Valenciana', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-1.5, 37.8], [0.8, 37.8], [0.8, 40.8], [-1.5, 40.8], [-1.5, 37.8]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES61', NAME_LATN: 'Andalucía', NUTS_NAME: 'Andalucía', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-7.6, 36.0], [-1.6, 36.0], [-1.6, 38.8], [-7.6, 38.8], [-7.6, 36.0]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'PT11', NAME_LATN: 'Norte', NUTS_NAME: 'Norte', CNTR_CODE: 'PT', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-9.0, 40.8], [-6.2, 40.8], [-6.2, 42.2], [-9.0, 42.2], [-9.0, 40.8]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'IE04', NAME_LATN: 'Northern and Western', NUTS_NAME: 'Northern and Western', CNTR_CODE: 'IE', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-10.7, 52.8], [-7.3, 52.8], [-7.3, 55.4], [-10.7, 55.4], [-10.7, 52.8]]] },
          },
        ],
      }),
    })
  })

  await page.route('http://127.0.0.1:8020/api/**', async route => {
    const url = new URL(route.request().url())
    const path = url.pathname
    const country = path.match(/\/countries\/(ESP|PRT|IRL)\//)?.[1] ?? 'ESP'
    let body: unknown

    if (/^\/api\/cities\/[A-Z0-9]+\/evidence$/.test(path)) {
      const cityCode = path.split('/')[3]
      body = {
        city_code: cityCode,
        geo_level: 'city',
        source: 'AUGUR local store · Eurostat Urban Audit + EEA air quality',
        minimum_population_scope: 50000,
        indicator_count: 9,
        available_count: 9,
        complete: true,
        indicators: [
          { indicator_id: 'city_population', name: 'Population', category: 'demography', status: 'available', period: 2025, value: 3420000, unit: 'persons', dataset_id: 'urb_cpop1', source_id: 'EUROSTAT' },
          { indicator_id: 'city_median_age', name: 'Median population age', category: 'demography', status: 'available', period: 2024, value: 43.7, unit: 'years', dataset_id: 'urb_cpopstr', source_id: 'EUROSTAT' },
          { indicator_id: 'city_public_transport_commute_share', name: 'Journeys to work by public transport', category: 'mobility', status: 'available', period: 2023, value: 38.5, unit: 'percent', dataset_id: 'urb_ctran', source_id: 'EUROSTAT' },
          { indicator_id: 'city_walk_commute_share', name: 'Journeys to work by foot', category: 'mobility', status: 'available', period: 2023, value: 11.4, unit: 'percent', dataset_id: 'urb_ctran', source_id: 'EUROSTAT' },
          { indicator_id: 'city_registered_cars_per_1000', name: 'Registered cars', category: 'mobility', status: 'available', period: 2024, value: 455, unit: 'per_1000_people', dataset_id: 'urb_ctran', source_id: 'EUROSTAT' },
          { indicator_id: 'city_monthly_transit_pass', name: 'Monthly public transport ticket', category: 'mobility', status: 'available', period: 2024, value: 54.6, unit: 'eur_monthly', dataset_id: 'urb_ctran', source_id: 'EUROSTAT' },
          { indicator_id: 'city_tourist_nights_per_resident', name: 'Tourist overnight stays per resident', category: 'tourism', status: 'available', period: 2024, value: 7.8, unit: 'nights_per_person', dataset_id: 'urb_ctour', source_id: 'EUROSTAT' },
          { indicator_id: 'city_tourist_beds_per_1000', name: 'Tourist bed-places', category: 'tourism', status: 'available', period: 2024, value: 28.1, unit: 'per_1000_people', dataset_id: 'urb_ctour', source_id: 'EUROSTAT' },
          { indicator_id: 'city_pm25_annual_mean_observed', name: 'Observed annual mean PM2.5', category: 'environment', status: 'available', period: 2024, value: 9.0111, unit: 'ug_m3', dataset_id: 'EEA_AIR_QUALITY_E1A_CITY_MEASUREMENTS', source_id: 'EEA' },
        ],
        notes: [],
      }
    } else if (/^\/api\/regions\/[A-Z0-9]+\/evidence$/.test(path)) {
      const geoCode = path.split('/')[3]
      if (geoCode === 'AU1') {
        body = {
          geo_code: 'AU1',
          geo_name: 'New South Wales',
          geo_level: 'tl2',
          source: 'AUGUR local store · OECD regional statistics',
          source_ids: ['OECD'],
          indicator_count: 2,
          available_count: 2,
          complete: true,
          indicators: [
            {
              indicator_id: 'regional_population',
              name: 'Population',
              status: 'available',
              period: 2024,
              value: 8534000,
              unit: 'persons',
              dataset_id: 'DSD_REG_DEMO@DF_POP_BROAD',
              source_id: 'OECD',
            },
            {
              indicator_id: 'regional_population_density',
              name: 'Population density',
              status: 'available',
              period: 2024,
              value: 10.58,
              unit: 'people_per_km2',
              dataset_id: 'DSD_REG_DEMO@DF_DENSITY',
              source_id: 'OECD',
            },
          ],
          sector_structure: {
            status: 'unavailable',
            reason: 'sector_context_not_available_for_geography_system',
            dataset_id: null,
            source_id: null,
            sectors: [],
          },
          environmental_health: {
            status: 'unavailable',
            reason: 'environmental_health_not_available_for_geography_system',
            source_id: null,
            dataset_id: null,
            metrics: [],
          },
          notes: [
            'OECD TL2/TL3 levels are not treated as interchangeable with Eurostat NUTS levels.',
          ],
        }
      } else {
      const nuts3 = geoCode.length === 5
      body = nuts3 ? {
        geo_code: geoCode,
        geo_level: 'nuts3',
        source: 'Eurostat regional statistics',
        indicator_count: 2,
        available_count: 2,
        complete: true,
        indicators: [
          { indicator_id: 'regional_intentional_homicide_rate', name: 'Police-recorded intentional homicide', status: 'available', period: 2024, value: 0.69, unit: 'per_100k_people', dataset_id: 'crim_gen_reg', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_robbery_rate', name: 'Police-recorded robbery', status: 'available', period: 2024, value: 34.07, unit: 'per_100k_people', dataset_id: 'crim_gen_reg', source_id: 'EUROSTAT' },
        ],
        notes: [
          'NUTS3 police-recorded crime is descriptive safety context and can be affected by legal, reporting and recording differences.',
        ],
      } : {
        geo_code: geoCode,
        geo_level: 'nuts2',
        source: 'Eurostat regional statistics',
        indicator_count: 11,
        available_count: 11,
        complete: true,
        indicators: [
          { indicator_id: 'regional_population', name: 'Population', status: 'available', period: 2024, value: 2700000, unit: 'persons', dataset_id: 'demo_r_pjangrp3', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_population_density', name: 'Population density', status: 'available', period: 2024, value: 91.4, unit: 'people_per_km2', dataset_id: 'demo_r_d3dens', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_gdp_per_capita', name: 'GDP per capita', status: 'available', period: 2024, value: 28900, unit: 'eur_per_person', dataset_id: 'nama_10r_3gdp', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_employment_rate', name: 'Employment rate, ages 20–64', status: 'available', period: 2024, value: 71.2, unit: 'percent', dataset_id: 'lfst_r_lfe2emprt', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_unemployment_rate', name: 'Unemployment rate, ages 20–64', status: 'available', period: 2024, value: 8.3, unit: 'percent', dataset_id: 'lfst_r_lfu3rt', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_disposable_income_pps_per_capita', name: 'Disposable household income per inhabitant (PPS)', status: 'available', period: 2023, value: 24500, unit: 'pps_per_person', dataset_id: 'nama_10r_2hhinc', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_housing_cost_overburden_rate', name: 'Housing cost overburden rate', status: 'available', period: 2025, value: 6.4, unit: 'percent', dataset_id: 'ilc_lvho07_r', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_unmet_medical_needs', name: 'Unmet medical examination needs', status: 'available', period: 2025, value: 1.2, unit: 'percent', dataset_id: 'hlth_silc_08_r', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_hospital_beds_per_100k', name: 'Available hospital beds', status: 'available', period: 2024, value: 315.6, unit: 'per_100k_people', dataset_id: 'hlth_rs_bdsrg2', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_household_internet_access', name: 'Households with internet access', status: 'available', period: 2025, value: 98.4, unit: 'percent', dataset_id: 'isoc_r_iacc_h', source_id: 'EUROSTAT' },
          { indicator_id: 'regional_air_passengers_thousands', name: 'Air passengers carried', status: 'available', period: 2024, value: 1650, unit: 'thousand_passengers', dataset_id: 'tran_r_avpa_nm', source_id: 'EUROSTAT' },
        ],
        sector_structure: {
          status: 'available',
          dataset_id: 'lfst_r_lfe2en2',
          source_id: 'EUROSTAT',
          period: 2025,
          total_employment_thousands: 1000,
          sector_count: 2,
          top_sectors: [
            { nace_code: 'C', nace_label: 'Manufacturing', period: 2025, employment_thousands: 180, employment_share_pct: 18.0 },
            { nace_code: 'J', nace_label: 'Information and communication', period: 2025, employment_thousands: 70, employment_share_pct: 7.0 },
          ],
          notes: [],
        },
        notes: [],
      }
      }
    } else if (path.endsWith('/ttv/calibration/active')) {
      body = {
        country_iso3: country,
        observation: null,
      }
    } else if (path.endsWith('/career-fit')) {
      body = {
        target_country_iso3: country,
        status: 'profession_missing',
        occupation: {
          status: 'profession_missing',
          occupation_group: null,
          matched_terms: [],
        },
        market_signal: null,
        vacancy_demand_evidence: {
          status: 'available',
          isco_major: 'OC3',
          isco_3digit: 'OC351',
          vacancy_rate_pct: 3.4,
          period: '2024',
          nace_scope: null,
          source_id: 'EUROSTAT',
          dataset_id: 'jvs_a_isco3_r1',
          granularity: 'isco_3digit',
          role: 'context_only',
        },
        live_postings_evidence: {
          status: 'provider_not_configured',
          contract_version: 'live-postings-v1',
          provider_id: null,
          role: 'context_only',
          requested_metrics: [
            'active_posting_count',
            'skill_demand_share',
            'language_requirement_share',
          ],
          required_capabilities: [
            'active_postings',
            'country_filter',
            'occupation_filter',
            'posting_date',
          ],
          optional_capabilities: [
            'skills',
            'languages',
            'salary',
          ],
        },
        skill_match: {
          status: 'not_evaluated',
          matched_skills: [],
          missing_skills: [],
        },
        evidence_complete: false,
        rule_version: 'EURES_COUNTRY_LMI_2024',
        source: {
          label: country === 'ESP'
            ? 'EURES Labour Market Information: Spain'
            : country === 'PRT'
            ? 'EURES Labour Market Information: Portugal'
            : 'EURES Labour Market Information: Ireland',
          url: 'https://eures.europa.eu/',
          evidence_id: 'eures_country_lmi_2024_conditions',
          rule_version: 'EURES_COUNTRY_LMI_2024',
          report_year: 2025,
          conditions_year: 2024,
          report_url: 'https://eures.europa.eu/',
          scope: 'broad_occupation_group',
        },
        notes: [],
      }
    } else if (path.endsWith('/language-fit')) {
      body = {
        target_country_iso3: country,
        status: 'target_language_missing',
        target_languages: [country === 'ESP' ? 'Spanish' : country === 'PRT' ? 'Portuguese' : 'English'],
        matches: [{
          language: country === 'ESP' ? 'Spanish' : country === 'PRT' ? 'Portuguese' : 'English',
          declared_cefr: null,
          meets_work_ready_heuristic: false,
        }],
        work_ready_threshold: 'B2',
        work_ready: false,
        method: 'labour_market_language_heuristic_v1',
        notes: [],
      }
    } else if (path.endsWith('/ttv')) {
      body = {
        target_country_iso3: country,
        method: 'ttv_dependency_graph_v1',
        stage_order: ['legal_fit', 'language_fit', 'career_fit', 'financial_fit'],
        stages: {
          legal_fit: { ready: false, status: 'insufficient_profile', evidence_state: 'implemented' },
          language_fit: { ready: false, status: 'target_language_missing', evidence_state: 'implemented' },
          career_fit: { ready: false, status: 'profession_missing', evidence_state: 'partial' },
          financial_fit: { ready: false, status: 'insufficient_profile', evidence_state: 'partial' },
        },
        blocked_by: ['legal_fit', 'language_fit', 'career_fit', 'financial_fit'],
        blocker_details: [
          { stage_id: 'legal_fit', status: 'insufficient_profile', evidence_state: 'implemented' },
          { stage_id: 'language_fit', status: 'target_language_missing', evidence_state: 'implemented' },
          { stage_id: 'career_fit', status: 'profession_missing', evidence_state: 'partial' },
          { stage_id: 'financial_fit', status: 'insufficient_profile', evidence_state: 'partial' },
        ],
        dependency_ready: false,
        temporal_evidence_state: 'not_implemented',
        temporal_model_version: null,
        temporal_evidence_ready: false,
        temporal_evidence: {
          engine_version: 'ttv-temporal-evidence-v1',
          calendar_ready: false,
          unavailable_stages: ['language', 'skills', 'financial', 'employment'],
          candidate_range: null,
          stages: {
            legal: { status: 'unavailable', weeks_min: null, weeks_max: null, reason: 'legal_timing_not_verified_for_profile' },
            language: {
              status: 'guided_hours_available_calendar_missing',
              weeks_min: null,
              weeks_max: null,
              reason: 'language_study_hours_per_week_missing',
              guided_hours_min: 100,
              guided_hours_max: 250,
              weekly_study_hours: null,
            },
            skills: { status: 'unavailable', weeks_min: null, weeks_max: null, reason: 'career_skill_evidence_incomplete' },
            financial: { status: 'unavailable', weeks_min: null, weeks_max: null, reason: 'financial_transition_duration_not_modelled_for_current_status' },
            employment: { status: 'unavailable', weeks_min: null, weeks_max: null, reason: 'local_job_search_temporal_baseline_not_yet_integrated' },
          },
        },
        candidate_time_range: null,
        estimate_status: 'dependencies_blocked',
        ready_for_time_estimate: false,
        time_estimate: null,
        notes: [],
      }
    } else if (path.endsWith('/legal-fit')) {
      body = {
        target_country_iso3: country,
        status: 'insufficient_profile',
        framework: null,
        work_permit_required: null,
        short_stay: null,
        long_stay: null,
        rule_version: '2026-10-01',
        notes: [],
      }
    } else if (path.endsWith('/financial-fit')) {
      body = {
        target_country_iso3: country,
        status: 'insufficient_profile',
        reason: 'monthly_net_income_missing',
        evidence_state: 'partial',
        evidence_complete: false,
        blockers: ['monthly_net_income'],
        local_income_reference: null,
        national_net_earnings_reference: null,
        portable_income_analysis: null,
        notes: [],
      }
    } else if (path === '/api/profile/readiness') {
      body = {
        profile_id: 'default',
        ready_module_count: 0,
        module_count: 4,
        notes: [],
        modules: {
          legal_fit: { label: 'LegalFit', ready: false, completed_fields: 0, required_fields: 2, missing_fields: ['current_country', 'citizenships'] },
          career_fit: { label: 'CareerFit', ready: false, completed_fields: 0, required_fields: 2, missing_fields: ['profession', 'skills'] },
          language_fit: { label: 'LanguageFit', ready: false, completed_fields: 0, required_fields: 1, missing_fields: ['languages'] },
          financial_fit: { label: 'FinancialFit', ready: false, completed_fields: 0, required_fields: 2, missing_fields: ['current_country', 'monthly_net_income'] },
        },
      }
    } else if (path === '/api/profile') {
      if (route.request().method() === 'PUT') {
        const payload = route.request().postDataJSON()
        body = {
          profile_id: 'default',
          updated_at: '2026-10-01T00:00:00+00:00',
          ...payload,
        }
      } else {
        body = {
          profile_id: 'default',
          age: null,
          current_country: null,
          citizenships: [],
          profession: null,
          skills: [],
          languages: [],
          household_size: 1,
          monthly_net_income: null,
          liquid_savings: null,
          remote_work: false,
          preferences: {},
          updated_at: null,
        }
      }
    } else if (path === '/api/ttv/calibration/status') {
      body = {
        protocol_state: 'definitions_frozen_acceptance_pending',
        protocol_version: null,
        development_case_count: 0,
        holdout_case_count: 0,
        interval_coverage_pct: null,
        mean_interval_width_weeks: null,
        mean_absolute_midpoint_error_weeks: null,
        mean_miss_distance_weeks: null,
        context_summary: {
          context_case_count: 0,
          current_cefr_levels: [],
          target_cefr_levels: [],
          weekly_study_hours: [],
        },
        protocol_readiness: {
          blockers: ['protocol_version', 'acceptance_criteria'],
        },
      }
    } else if (path === '/api/health') {
      body = { status: 'ok', phase: 1, version: 'test', datastores: { sqlite: true, duckdb: true } }
    } else if (path === '/api/operability') {
      body = {
        status: 'partial',
        ready: false,
        analysis_ready: true,
        ttv_temporal_model_ready: false,
        blockers: ['ttv_temporal_model'],
      }
    } else if (path === '/api/countries') {
      body = { countries }
    } else if (path === '/api/geographies') {
      const requestedCountry = url.searchParams.get('country_iso3')
      body = {
        country_iso3: requestedCountry,
        geo_level: null,
        geographies: requestedCountry === 'AUS'
          ? [
              {
                geo_id: 'OECD_TL_2024:AU1',
                country_iso3: 'AUS',
                country_iso2: 'AU',
                name: 'New South Wales',
                geo_level: 'tl2',
                geography_system: 'OECD_TL_2024',
                source_id: 'OECD',
                source_geo_code: 'AU1',
                parent_geo_id: null,
                latitude: null,
                longitude: null,
                indicator_count: 1,
                latest_period: 2024,
              },
              {
                geo_id: 'OECD_TL_2024:AU2',
                country_iso3: 'AUS',
                country_iso2: 'AU',
                name: 'Victoria',
                geo_level: 'tl2',
                geography_system: 'OECD_TL_2024',
                source_id: 'OECD',
                source_geo_code: 'AU2',
                parent_geo_id: null,
                latitude: null,
                longitude: null,
                indicator_count: 1,
                latest_period: 2024,
              },
            ]
          : [],
      }
    } else if (path === '/api/compare/personalized') {
      const requested = (url.searchParams.get('countries') ?? 'IRL,ESP,PRT').split(',')
      body = {
        status: 'weights_missing',
        countries: requested,
        weights: {
          explicit: {},
          scale: [0, 5],
          missing_means: 'not_selected_for_personal_weighting',
        },
        normalization: {
          version: 'augur_selected_set_utility_v1',
          scope: 'selected_country_set',
          utility_range: [0, 1],
          contextual_indicators_excluded: true,
          semantic_construct_version: 'augur_semantic_constructs_v1',
          notes: [],
        },
        indicators: [],
        constructs: [],
        dimensions: [],
      }
    } else if (path === '/api/compare') {
      const requested = (url.searchParams.get('countries') ?? 'IRL,ESP,PRT').split(',')
      body = {
        countries: requested.map((iso3) => {
          const country = countries.find((item) => item.iso3 === iso3)!
          return { iso3: country.iso3, name: country.name }
        }),
        indicator_count: overviewMetrics('ESP').length,
        method: 'aligned_current_observations_v1',
        notes: [],
        indicators: overviewMetrics('ESP').map((espItem) => ({
          indicator_id: espItem.indicator_id,
          name: espItem.name,
          dimension: espItem.dimension,
          unit: espItem.unit,
          countries: Object.fromEntries(
            ['ESP', 'PRT', 'IRL'].map((iso3) => {
              const item = overviewMetrics(iso3).find((candidate) => candidate.indicator_id === espItem.indicator_id)!
              return [iso3, { period: item.period, value: item.value, source_id: item.source_id }]
            }),
          ),
        })),
      }
    } else if (path.endsWith('/snapshot')) {
      body = { country_iso3: country, observation_count: overviewMetrics(country).length, indicators: overviewMetrics(country) }
    } else if (path.endsWith('/overview-series')) {
      body = {
        country_iso3: country,
        series: overviewMetrics(country).map((item) => ({
          indicator_id: item.indicator_id,
          name: item.name,
          dimension: item.dimension,
          unit: item.unit,
          source_id: item.source_id,
          points: Array.from({ length: 8 }, (_, index) => {
            const trend = mockTrendFor(item)
            const step = trend.direction === 'decrease' ? 0.35 : 0.35
            const direction = trend.direction === 'decrease' ? -1 : 1
            const reverseIndex = 7 - index
            return {
              period: item.period - reverseIndex,
              value: item.value - direction * step * reverseIndex,
            }
          }),
        })),
      }
    } else if (path.endsWith('/trends')) {
      body = {
        country_iso3: country,
        indicator_count: overviewMetrics(country).length,
        indicators: overviewMetrics(country).map((item) => ({
          ...item,
          interpretation_policy: ['unemployment_rate', 'housing_cost_overburden_rate', 'energy_import_dependency'].includes(item.indicator_id) ? 'lower' : item.indicator_id === 'population_65_plus_share' ? 'contextual' : 'higher',
          target_min: null,
          target_max: null,
          trend: mockTrendFor(item),
        })),
      }
    } else if (path.endsWith('/assessment')) {
      body = {
        country_iso3: country,
        method: 'test',
        dimensions: Object.fromEntries(
          ['productive_capacity', 'prosperity', 'housing', 'human_systems', 'safety', 'environment', 'infrastructure', 'demography', 'strategic_resilience'].map((dimension) => {
            const items = overviewMetrics(country).filter((item) => item.dimension === dimension)
            const contextual = dimension === 'demography'
            return [dimension, {
              trajectory: contextual ? 'contextual' : 'improving',
              confidence: 'high',
              indicator_count: items.length,
              directional_indicator_count: contextual ? 0 : items.length,
              coverage: contextual ? 0 : 1,
              improving_signals: contextual ? [] : items.map((item) => ({
                indicator_id: item.indicator_id,
                name: item.name,
                direction: mockTrendFor(item).direction,
                confidence: 'high',
                pct_change_5y: mockTrendFor(item).pct_change_5y,
              })),
              deteriorating_signals: [],
              stable_signals: [],
              contextual_signals: contextual ? items.map((item) => ({
                indicator_id: item.indicator_id,
                name: item.name,
                direction: 'increase',
                confidence: 'high',
                pct_change_5y: mockTrendFor(item).pct_change_5y,
              })) : [],
            }]
          }),
        ),
      }
    } else if (path.endsWith('/source-quality')) {
      body = {
        country_iso3: country,
        indicators: overviewMetrics(country).map((item) => ({
          indicator_id: item.indicator_id,
          name: item.name,
          dimension: item.dimension,
          unit: item.unit,
          source_count: item.indicator_id === 'unemployment_rate' ? 2 : 1,
          preferred_source_id: item.source_id,
          preferred_source_name: item.source_id.replaceAll('_', ' '),
          preferred_period: item.period,
          preferred_value: item.value,
          freshest_period: item.period,
          period_spread: 0,
          common_period: item.indicator_id === 'unemployment_rate' ? item.period : null,
          common_period_source_count: item.indicator_id === 'unemployment_rate' ? 2 : null,
          disagreement_pct: item.indicator_id === 'unemployment_rate' ? 0.5 : null,
        })),
      }
    } else if (path.endsWith('/trajectory')) {
      if (country === 'ESP') {
        body = {
          country_iso3: country,
          method: 'official_forecast_horizon_view_v1',
          notes: [],
          horizons: [
            {
              year: 2030,
              indicator_count: 1,
              sources: ['IMF'],
              indicators: [{
                country_iso3: country,
                indicator_id: 'imf_unemployment_rate',
                name: 'Unemployment rate (IMF WEO)',
                dimension: 'productive_capacity',
                period: 2030,
                value: 8.0,
                unit: 'percent',
                source_id: 'IMF',
                source_name: 'IMF',
                dataset_id: 'WEO',
                source_updated_at: '2026-04',
              }],
            },
            {
              year: 2035,
              indicator_count: 1,
              sources: ['IMF'],
              indicators: [{
                country_iso3: country,
                indicator_id: 'imf_unemployment_rate',
                name: 'Unemployment rate (IMF WEO)',
                dimension: 'productive_capacity',
                period: 2035,
                value: 7.5,
                unit: 'percent',
                source_id: 'IMF',
                source_name: 'IMF',
                dataset_id: 'WEO',
                source_updated_at: '2026-04',
              }],
            },
          ],
        }
      } else if (country === 'PRT') {
        body = {
          country_iso3: country,
          method: 'official_forecast_horizon_view_v1',
          notes: [],
          horizons: [{
            year: 2030,
            indicator_count: 1,
            sources: ['UN_WPP'],
            indicators: [{
              country_iso3: country,
              indicator_id: 'fertility_rate',
              name: 'Fertility rate, total',
              dimension: 'demography',
              period: 2030,
              value: 1.26,
              unit: 'births_per_woman',
              source_id: 'UN_WPP',
              source_name: 'UN WPP',
              dataset_id: 'WPP2024',
              source_updated_at: '2024',
            }],
          }],
        }
      } else {
        body = { country_iso3: country, method: 'test', notes: [], horizons: [] }
      }
    } else if (path.endsWith('/scenarios')) {
      if (country === 'ESP') {
        body = {
          country_iso3: country,
          method: 'augur_scenario_envelope_v2',
          horizons: [2030, 2035],
          scenario_names: ['baseline', 'improvement', 'stress'],
          indicators: [
            {
              country_iso3: country,
              indicator_id: 'imf_unemployment_rate',
              name: 'Unemployment rate (IMF WEO)',
              dimension: 'productive_capacity',
              period: 2030,
              value: 8.0,
              unit: 'percent',
              source_id: 'IMF',
              source_name: 'IMF',
              dataset_id: 'WEO',
              official_baseline: 8.0,
              scenarios: { baseline: 8.0, improvement: 7.0, stress: 9.5 },
              assumption: 'AUGUR model assumption for test.',
              uncertainty: { multiplier: 1, level: 'near' },
            },
            {
              country_iso3: country,
              indicator_id: 'imf_unemployment_rate',
              name: 'Unemployment rate (IMF WEO)',
              dimension: 'productive_capacity',
              period: 2035,
              value: 7.5,
              unit: 'percent',
              source_id: 'IMF',
              source_name: 'IMF',
              dataset_id: 'WEO',
              official_baseline: 7.5,
              scenarios: { baseline: 7.5, improvement: 6.0, stress: 10.0 },
              assumption: 'AUGUR model assumption for test.',
              uncertainty: { multiplier: 1.5, level: 'medium' },
            },
          ],
          notes: [],
        }
      } else if (country === 'PRT') {
        body = {
          country_iso3: country,
          method: 'augur_scenario_envelope_v2',
          horizons: [2030],
          scenario_names: ['baseline', 'improvement', 'stress'],
          indicators: [{
            country_iso3: country,
            indicator_id: 'fertility_rate',
            name: 'Fertility rate, total',
            dimension: 'demography',
            period: 2030,
            value: 1.26,
            unit: 'births_per_woman',
            source_id: 'UN_WPP',
            source_name: 'UN WPP',
            dataset_id: 'WPP2024',
            official_baseline: 1.26,
            scenarios: { baseline: 1.26, improvement: 1.26, stress: 1.26 },
            assumption: 'Contextual indicator: no automatic positive/negative adjustment applied.',
            uncertainty: { multiplier: 1, level: 'near' },
          }],
          notes: [],
        }
      } else {
        body = { country_iso3: country, method: 'test', horizons: [], scenario_names: ['baseline', 'improvement', 'stress'], indicators: [], notes: [] }
      }
    } else {
      body = {}
    }

    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
  })
}

test.beforeEach(async ({ page }) => {
  await mockApi(page)
  await page.goto('/')
})

test('topbar distinguishes evidence readiness from full product status', async ({ page }) => {
  await expect(page.getByText('P1 · ok')).toBeVisible()
  await expect(page.getByText('Evidence · ready')).toBeVisible()
  await expect(page.getByText('Evidence · ready')).toHaveAttribute(
    'title',
    'Product: partial · Blockers: ttv_temporal_model',
  )
})


test('refreshes evidence status when the window regains focus', async ({ page }) => {
  await expect(page.getByText('Evidence · ready')).toBeVisible()

  await page.route(
    'http://127.0.0.1:8020/api/operability',
    async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'partial',
          ready: false,
          analysis_ready: false,
          ttv_temporal_model_ready: false,
          blockers: ['data_sync_stale'],
        }),
      })
    },
  )

  await page.evaluate(() => window.dispatchEvent(new Event('focus')))

  await expect(page.getByText('Evidence · partial')).toBeVisible()
  await expect(page.getByText('Evidence · partial')).toHaveAttribute(
    'title',
    'Product: partial · Blockers: data_sync_stale',
  )
})


test('top navigation uses real routes and exposes all six product views', async ({ page }) => {
  await expect(page).toHaveURL(/\/country\/ESP\/overview$/)
  await expect(page.getByTestId('regional-map')).toBeVisible()

  await page.getByRole('button', { name: 'Indicators' }).click()
  await expect(page).toHaveURL(/\/country\/ESP\/indicators$/)
  await expect(page.getByText('2. EVIDENCE EXPLORER / Indicators')).toBeVisible()

  await page.getByRole('button', { name: 'Outlook' }).click()
  await expect(page).toHaveURL(/\/country\/ESP\/outlook$/)
  await expect(page.getByText('3. FUTURE PATHS / Outlook')).toBeVisible()
  await expect(page.getByTestId('regional-map')).toHaveCount(0)

  await page.getByRole('button', { name: 'Compare' }).click()
  await expect(page).toHaveURL(/\/compare\?countries=IRL%2CESP%2CPRT|\/compare\?countries=IRL,ESP,PRT/)
  await expect(page.getByText('4. DECISION MATRIX / Compare')).toBeVisible()

  await page.getByRole('button', { name: 'Profile' }).click()
  await expect(page).toHaveURL(/\/country\/ESP\/profile$/)
  await expect(page.getByRole('region', { name: 'Personal profile' })).toBeVisible()
  await expect(page.getByText('5. MY FIT / Profile')).toBeVisible()

  await page.getByRole('button', { name: 'Skills & Languages' }).click()
  await expect(page).toHaveURL(/\/country\/ESP\/skills$/)
  await expect(page.getByRole('region', { name: 'Skills and languages' })).toBeVisible()
  await expect(page.getByText('6. SKILLS & LANGUAGES')).toBeVisible()
})

test('dynamic non-pilot country opens through the normal overview route', async ({ page }) => {
  await page.goto('/country/DEU/overview')

  await expect(page).toHaveURL(/\/country\/DEU\/overview$/)
  await expect(page.getByText('Germany — country trajectory')).toBeVisible()
  await expect(page.locator('.countryIdentityCard').getByText('DEU', { exact: true })).toBeVisible()

  const map = page.getByTestId('regional-map')
  await expect(map).toHaveAttribute('data-map-status', 'ready')
  await expect(page.getByText('No integrated subnational source for this country yet')).toBeVisible()
})

test('source-native OECD region can be selected without GISCO geometry', async ({ page }) => {
  await page.goto('/country/AUS/overview')

  await expect(page.getByText('Australia — country trajectory')).toBeVisible()

  const regionSelect = page.getByRole('combobox', { name: 'Available source-native region' })
  await expect(regionSelect).toBeVisible()
  await expect(regionSelect).toContainText('New South Wales · TL2')

  await regionSelect.selectOption('AU1')

  const geographicEvidence = page.getByRole('region', { name: 'Selected geographic evidence' })
  await expect(geographicEvidence.getByText('TL2 EVIDENCE')).toBeVisible()
  await expect(geographicEvidence.locator('.radarPanelTopline strong')).toHaveText('New South Wales')
  await expect(geographicEvidence.getByText('Population', { exact: true })).toBeVisible()
  await expect(geographicEvidence.getByText('8,534,000')).toBeVisible()
  await expect(geographicEvidence.getByText('Population density', { exact: true })).toBeVisible()
  await expect(geographicEvidence.getByText('10.6 /km²')).toBeVisible()
})

test('Overview reveals and selects official NUTS 2 regions', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  const map = page.getByTestId('regional-map')
  await expect(map).toBeVisible()
  await expect(map.locator('.leaflet-control-zoom-in')).toBeVisible()
  await expect(page.getByText('Zoom in to reveal available regional detail')).toBeVisible()
  await expect(map).toHaveAttribute('data-map-status', 'ready')

  await page.getByRole('button', { name: 'Focus country' }).click()

  await expect(page.getByText('NUTS 2 regions visible')).toBeVisible()
  await expect.poll(async () => map.locator('.nuts2Boundary').count()).toBeGreaterThan(0)

  const galicia = map.locator('.nuts2Boundary').first()
  await expect.poll(async () => galicia.getAttribute('d')).not.toBe('M0 0')
  await expect(galicia).toBeVisible()
  const galiciaBox = await galicia.boundingBox()
  if (!galiciaBox) throw new Error('Galicia boundary is not rendered')
  await page.mouse.click(
    galiciaBox.x + galiciaBox.width / 2,
    galiciaBox.y + galiciaBox.height / 2,
  )

  await expect(page.getByText('REGION · Galicia · ES11')).toBeVisible()
  const geographicEvidence = page.getByRole('region', { name: 'Selected geographic evidence' })
  await expect(geographicEvidence.getByText('Galicia')).toBeVisible()
  await expect(geographicEvidence.getByText('GDP per capita')).toBeVisible()

  const regionalCards = page.getByRole('region', { name: 'Regional metric cards' })
  await expect(regionalCards).toBeVisible()
  await expect(regionalCards.getByText('Population density')).toBeVisible()
  await expect(regionalCards.getByText('GDP per capita')).toBeVisible()
  await expect(regionalCards.getByText('Disposable household income per inhabitant (PPS)')).toBeVisible()
  await expect(regionalCards.getByText('24,500 PPS/person')).toBeVisible()
  await expect(regionalCards.getByText('Housing cost overburden rate')).toBeVisible()
  await expect(regionalCards.getByText('6.4%')).toBeVisible()
  await expect(regionalCards.getByText('Unmet medical examination needs')).toBeVisible()
  await expect(regionalCards.getByText('1.2%', { exact: true })).toBeVisible()
  await expect(regionalCards.getByText('Available hospital beds')).toBeVisible()
  await expect(regionalCards.getByText('315.6 /100k')).toBeVisible()
  await expect(regionalCards.getByText('Households with internet access')).toBeVisible()
  await expect(regionalCards.getByText('98.4%')).toBeVisible()
  await expect(regionalCards.getByText('Air passengers carried')).toBeVisible()
  await expect(regionalCards.getByText('1,650k passengers')).toBeVisible()
  await expect(page.getByRole('region', { name: 'Country metric cards' })).toHaveCount(0)
  await expect(page.locator('.regionalEvidencePanel')).toHaveCount(0)
  await expect(page.getByText(/Base map: OpenStreetMap · European subnational overlays: Eurostat GISCO NUTS 2024 \+ Urban Audit 2024/)).toBeVisible()
})

test('switches country without a page reload', async ({ page }) => {
  const selector = page.getByLabel('Select country')
  await selector.selectOption('PRT')
  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(selector).toHaveValue('PRT')

  await selector.selectOption('IRL')
  await expect(page.getByLabel('Select country')).toHaveValue('IRL')
  await expect(selector).toHaveValue('IRL')
})



test('Skills and Languages distinguishes learning gaps from demand ranking', async ({ page }) => {
  await page.goto('/country/ESP/skills')

  // Populate the profile/fit fixture already used by the visual audit helper where available.
  const summary = page.getByRole('region', { name: 'Skills decision summary' })
  if (await summary.count()) {
    await expect(summary.getByText('NEXT TO LEARN')).toBeVisible()
    await expect(summary.getByText('PORTABLE ASSETS')).toBeVisible()
    await expect(summary.getByText('LANGUAGE READINESS')).toBeVisible()
    await expect(summary.getByText('MARKET CONTEXT')).toBeVisible()
    await expect(summary.getByText(/not employer-demand frequency/i)).toBeVisible()
    await expect(summary.getByText(/not a skill-demand ranking/i)).toBeVisible()
  }
})

test('Skills and Languages exposes live-postings provider state explicitly', async ({ page }) => {
  await page.goto('/country/ESP/skills')

  await expect(page.getByText('Live job-posting enrichment')).toBeVisible()
  await expect(page.getByText('CONTRACT READY · PROVIDER NOT CONFIGURED')).toBeVisible()
  await expect(page.getByText(/missing access is not zero demand/i)).toBeVisible()
  await expect(page.getByText(/live-postings-v1 contract ready/i)).toBeVisible()
})

test('Decision Matrix keeps personal weighting explicit when no weights are saved', async ({ page }) => {
  await page.goto('/compare?countries=ESP,PRT,IRL')
  await page.getByRole('button', { name: 'My priorities' }).click()

  await expect(page.getByText(/No explicit P2 decision weights are saved yet/i)).toBeVisible()
  await expect(page.getByText(/objective evidence below remains unchanged/i)).toBeVisible()
  await expect(page.getByText(/No overall ranking/i)).toHaveCount(0)
})

test('Decision Matrix shows preference index sensitivity and Pareto candidates', async ({ page }) => {
  await page.route('http://127.0.0.1:8020/api/compare/personalized?*', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'ready',
        countries: ['ESP', 'IRL'],
        weights: {
          explicit: {
            productive_capacity: 4,
            housing: 1,
          },
          scale: [0, 5],
          missing_means: 'not_selected_for_personal_weighting',
        },
        normalization: {
          version: 'augur_selected_set_utility_v1',
          scope: 'selected_country_set',
          utility_range: [0, 1],
          contextual_indicators_excluded: true,
          semantic_construct_version: 'augur_semantic_constructs_v1',
          notes: [],
        },
        indicators: [],
        constructs: [],
        dimensions: [
          {
            dimension: 'productive_capacity',
            explicit_weight: 4,
            utility: { ESP: 0, IRL: 1 },
            construct_count: 2,
            method: 'mean_of_available_semantic_construct_utilities',
          },
          {
            dimension: 'housing',
            explicit_weight: 1,
            utility: { ESP: 1, IRL: 0 },
            construct_count: 1,
            method: 'mean_of_available_semantic_construct_utilities',
          },
        ],
        personalized: {
          status: 'ready',
          score_label: 'selected_set_preference_fit_index',
          score_range: [0, 100],
          scores: { ESP: 20, IRL: 80 },
          positive_weights: { productive_capacity: 4, housing: 1 },
          normalized_weights: { productive_capacity: 0.8, housing: 0.2 },
          included_dimensions: ['housing', 'productive_capacity'],
          coverage: { ESP: 1, IRL: 1 },
          sensitivity: {
            method: 'joint_local_weight_neighborhood_plus_minus_1',
            total_possible_scenarios: 5,
            cartesian_combination_count: 5,
            scenario_limit: 5000,
            truncated: false,
            dimension_count: 2,
            scenario_count: 5,
            weight_bounds: [0, 5],
            score_ranges: {
              ESP: { min: 16.7, max: 25, spread: 8.3 },
              IRL: { min: 75, max: 83.3, spread: 8.3 },
            },
            rank_ranges: {
              ESP: { best_rank: 2, worst_rank: 2, top_scenario_count: 0, scenario_count: 5, status: 'rank_stable' },
              IRL: { best_rank: 1, worst_rank: 1, top_scenario_count: 5, scenario_count: 5, status: 'rank_stable' },
            },
          },
          pareto: {
            method: 'pareto_nondominance_on_positive_weight_dimensions',
            dimensions: ['housing', 'productive_capacity'],
            frontier: ['ESP', 'IRL'],
            dominated_by: { ESP: [], IRL: [] },
          },
          notes: [],
        },
      }),
    })
  })

  await page.goto('/compare?countries=ESP,IRL')
  await page.getByRole('button', { name: 'My priorities' }).click()

  const panel = page.getByRole('region', { name: 'Personalized dimension utilities' })
  await expect(panel).toBeVisible()
  await expect(panel.getByText('20.0', { exact: true })).toBeVisible()
  await expect(panel.getByText('80.0', { exact: true })).toBeVisible()
  await expect(panel.getByText(/sensitivity 16.7–25.0/i)).toBeVisible()
  await expect(panel.getByText(/Pareto candidate set: Spain · Ireland/i)).toBeVisible()
  await expect(panel.getByText(/universal winner/i)).toBeVisible()
  await expect(page.getByText(/best country/i)).toHaveCount(0)
})

test('Outlook labels contextual scenarios without implying statistical uncertainty', async ({ page }) => {
  await page.goto('/country/PRT/outlook')

  await expect(page.getByText('No directional scenario envelope is applied.')).toBeVisible()
  await expect(page.getByText('This indicator is contextual or no model assumptions exist for it.')).toBeVisible()
  await expect(page.getByText('Official forecast / projection')).toBeVisible()
})

test('comparison remains neutral and aligned', async ({ page }) => {
  await page.getByRole('button', { name: 'Compare' }).click()
  await expect(page.getByRole('columnheader', { name: 'Spain' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: 'Portugal' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: 'Ireland' })).toBeVisible()
  await expect(page.getByText('Objective data')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Tested preference robustness' })).toBeVisible()
})


test('Decision Matrix uses relative spreads and neutral selected-set positions', async ({ page }) => {
  await page.goto('/compare?countries=ESP,PRT,IRL')

  await expect(page.getByText('Largest relative spreads')).toBeVisible()
  await expect(page.getByText(/descriptive, not a quality score/i)).toBeVisible()
  const indicatorRows = page.locator('.matrixIndicatorNote')
  const indicatorRowCount = await indicatorRows.count()
  await expect(page.locator('.matrixPositionBadge')).toHaveCount(indicatorRowCount * 3)
  const domainRowCount = await page.locator('.matrixDomainRow').count()
  expect(domainRowCount).toBeGreaterThan(0)
  await expect(page.getByRole('region', { name: 'Domain evidence coverage' }).locator('.decisionCoverageTrack')).toHaveCount(domainRowCount)
  await expect(page.getByText('High', { exact: true }).first()).toBeVisible()
  await expect(page.getByText('Low', { exact: true }).first()).toBeVisible()
  await expect(page.getByText(/descriptive comparison · no winner implied/i).first()).toBeVisible()
})

test('Indicators route exposes drill-down evidence without overstating provenance', async ({ page }) => {
  await page.goto('/country/ESP/indicators')

  await expect(page).toHaveURL(/\/country\/ESP\/indicators$/)
  await expect(page.getByRole('region', { name: 'Indicators' })).toBeVisible()
  await expect(page.getByText('2. EVIDENCE EXPLORER / Indicators')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Unemployment, total (% of total labor force)' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Unemployment, total (% of total labor force)' })).toBeVisible()
  await expect(page.getByLabel('Search indicators')).toBeVisible()
  await expect(page.getByText('Indicator details')).toBeVisible()
  await expect(page.getByText('Corroborated')).toHaveCount(0)
})

test('Indicator provenance exposes methodology and comparability caveats', async ({ page }) => {
  const safety = {
    country_iso3: 'ESP',
    indicator_id: 'intentional_homicide_rate',
    name: 'Police-recorded intentional homicides',
    dimension: 'safety',
    period: 2024,
    value: 0.6,
    unit: 'per_100k_people',
    source_id: 'EUROSTAT',
  }

  await page.route('http://127.0.0.1:8020/api/countries/ESP/snapshot', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ country_iso3: 'ESP', observation_count: 1, indicators: [safety] }),
    })
  })

  await page.route('http://127.0.0.1:8020/api/countries/ESP/trends', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        country_iso3: 'ESP',
        indicator_count: 1,
        indicators: [{
          ...safety,
          interpretation_policy: 'lower',
          target_min: null,
          target_max: null,
          methodology_note: 'Police-recorded intentional homicide rate per 100,000 inhabitants.',
          comparability_note: 'Cross-country comparisons can be affected by differences in criminal law, reporting and police recording practices.',
          trend: {
            direction: 'decrease',
            interpretation: 'improving',
            confidence: 'high',
            slope_per_year: -0.02,
            pct_change_1y: -2.0,
            pct_change_3y: -5.0,
            pct_change_5y: -8.0,
            years_used: 6,
            target_status: null,
          },
        }],
      }),
    })
  })

  await page.route('http://127.0.0.1:8020/api/countries/ESP/source-quality', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        country_iso3: 'ESP',
        indicators: [{
          indicator_id: safety.indicator_id,
          name: safety.name,
          dimension: safety.dimension,
          unit: safety.unit,
          source_count: 1,
          preferred_source_id: 'EUROSTAT',
          preferred_source_name: 'Eurostat',
          preferred_period: 2024,
          preferred_value: 0.6,
          freshest_period: 2024,
          period_spread: 0,
          common_period: null,
          common_period_source_count: null,
          disagreement_pct: null,
        }],
      }),
    })
  })

  await page.route('http://127.0.0.1:8020/api/countries/ESP/overview-series', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        country_iso3: 'ESP',
        series: [{
          indicator_id: safety.indicator_id,
          name: safety.name,
          dimension: safety.dimension,
          unit: safety.unit,
          source_id: 'EUROSTAT',
          points: [
            { period: 2020, value: 0.8 },
            { period: 2021, value: 0.7 },
            { period: 2022, value: 0.7 },
            { period: 2023, value: 0.6 },
            { period: 2024, value: 0.6 },
          ],
        }],
      }),
    })
  })

  await page.goto('/country/ESP/indicators')
  await page.getByRole('button', { name: 'Provenance' }).click()

  const notes = page.getByRole('region', { name: 'Methodology and comparability notes' })
  await expect(notes.getByText('Methodology', { exact: true })).toBeVisible()
  await expect(notes.getByText(/Police-recorded intentional homicide rate/i)).toBeVisible()
  await expect(notes.getByText('Comparability', { exact: true })).toBeVisible()
  await expect(notes.getByText(/recording practices/i)).toBeVisible()
})

test('Indicators keeps raw changes neutral and shows observed history', async ({ page }) => {
  await page.goto('/country/ESP/indicators')

  const row = page.locator('.evidenceExplorerTable tbody tr').filter({ hasText: 'Unemployment, total' }).first()
  await expect(row.locator('.rawChange')).toHaveCount(3)
  await expect(row.locator('.positiveRaw')).toHaveCount(0)
  await expect(row.locator('.negativeRaw')).toHaveCount(0)

  const history = page.getByRole('region', { name: 'Observed indicator history' })
  await expect(history).toBeVisible()
  await expect(history.locator('polyline')).toBeVisible()
  await expect(history.getByText(/8 points · EUROSTAT/i)).toBeVisible()
  await expect(page.getByText('Trend evidence confidence')).toBeVisible()
})

test('Indicators summary distinguishes descriptive changes from directional interpretation', async ({ page }) => {
  await page.goto('/country/ESP/indicators')

  const summary = page.getByRole('region', { name: 'Indicator evidence summary' })
  await expect(summary).toBeVisible()
  await expect(summary.getByText('Indicators shown')).toBeVisible()
  await expect(summary.getByText('Directional signals')).toBeVisible()
  await expect(summary.getByText(/Raw percentage changes are descriptive/i)).toBeVisible()
})

test('Overview dimension cards drill into persistent dimension routes', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  await page.locator('.countryMetricCard').filter({ hasText: 'Labour market' }).click()

  await expect(page).toHaveURL(/\/country\/ESP\/dimension\/productive_capacity$/)
  await expect(page.getByRole('region', { name: 'Dimension detail' })).toBeVisible()
  await expect(page.getByText('Productive capacity · Spain')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Unemployment, total (% of total labor force)' })).toBeVisible()
  await expect(page.getByText('Directional coverage')).toBeVisible()

  await page.reload()
  await expect(page).toHaveURL(/\/country\/ESP\/dimension\/productive_capacity$/)

  await page.getByRole('button', { name: 'All indicators' }).click()
  await expect(page).toHaveURL(/\/country\/ESP\/indicators$/)
})

test('Dimension Detail separates supporting opposing and contextual evidence', async ({ page }) => {
  await page.goto('/country/ESP/dimension/productive_capacity')

  await expect(page.getByText('SYNTHESIS', { exact: true })).toBeVisible()
  await expect(page.getByText('Improving evidence')).toBeVisible()
  await expect(page.getByText('Deteriorating evidence')).toBeVisible()
  await expect(page.getByText('Stable / contextual evidence')).toBeVisible()
  await expect(page.locator('.dimensionSignalLane.supporting')).toBeVisible()
  await expect(page.locator('.dimensionSignalLane.opposing')).toBeVisible()
  await expect(page.locator('.dimensionSignalLane.contextual')).toBeVisible()
})

test('regional map renders clickable country context and geographic controls', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  const map = page.getByTestId('regional-map')
  await expect(map).toBeVisible()
  await expect(map).toHaveAttribute('data-map-status', 'ready')
  await expect.poll(async () => map.locator('.countryBoundary').count()).toBeGreaterThan(0)
  await expect.poll(async () => map.locator('.selectedCountryBoundary').count()).toBeGreaterThan(0)
  await expect(page.getByRole('button', { name: 'Europe' })).toBeEnabled()
  await expect(page.getByRole('button', { name: 'Focus country' })).toBeEnabled()

  const portugal = map.locator('.countryBoundary').nth(1)
  await expect(portugal).toBeVisible()
  const portugalBox = await portugal.boundingBox()
  if (!portugalBox) throw new Error('Portugal boundary is not rendered')
  await page.mouse.click(
    portugalBox.x + portugalBox.width / 2,
    portugalBox.y + portugalBox.height / 2,
  )
  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
})

test('Decision Matrix summarizes numerical position without implying winners', async ({ page }) => {
  await page.goto('/compare?countries=ESP,PRT,IRL')

  const summary = page.getByRole('region', { name: 'Comparison summary' })
  await expect(summary).toBeVisible()
  await expect(summary.getByText('Spain')).toBeVisible()
  await expect(summary.getByText('Portugal')).toBeVisible()
  await expect(summary.getByText('Ireland')).toBeVisible()
  await expect(summary.getByText(/Higher\/lower describes numerical position only/i)).toBeVisible()
  await expect(page.locator('.matrixIndicatorNote').first()).toContainText('no winner implied')
  await expect(page.getByText(/best country/i)).toHaveCount(0)
})

test('Decision Matrix exposes comparable evidence coverage by domain', async ({ page }) => {
  await page.goto('/compare?countries=ESP,PRT,IRL')

  const coverage = page.getByRole('region', { name: 'Domain evidence coverage' })
  await expect(coverage).toBeVisible()
  await expect(coverage.getByText('Comparable data by domain')).toBeVisible()
  const matrixDomainCount = await page.locator('.matrixDomainRow').count()
  await expect(coverage.locator('.decisionCoverageTrack')).toHaveCount(matrixDomainCount)
})

test('personal profile remains separate and can be saved locally', async ({ page }) => {
  await page.goto('/country/ESP/profile')
  const profile = page.getByRole('region', { name: 'Personal profile' })

  await expect(profile.getByText('5. MY FIT / Profile')).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Profile completion' })).toBeVisible()
  await expect(profile.getByText('0 / 4 input sets ready')).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Personal-fit evidence' })).toBeVisible()
  await expect(profile.getByText('Completion measures required inputs only. It is not a country-fit score.')).toBeVisible()

  await profile.getByRole('button', { name: 'Edit' }).click()
  await profile.getByLabel('Profession').fill('Systems engineer')
  await profile.getByLabel('Household size').fill('2')
  await profile.getByRole('button', { name: 'Save profile' }).click()

  await expect(profile.getByText('Saved locally')).toBeVisible()
})

test('My Fit priorities are explicit and evidence cards expose next actions', async ({ page }) => {
  await page.goto('/country/ESP/profile')
  const profile = page.getByRole('region', { name: 'Personal profile' })

  const healthcare = profile.getByRole('button', { name: /Good healthcare/i })
  await expect(healthcare).toHaveAttribute('aria-pressed', 'false')
  await healthcare.click()
  await expect(healthcare).toHaveAttribute('aria-pressed', 'true')
  await expect(profile.getByText('1 selected · used only when explicit')).toBeVisible()

  const evidence = profile.getByRole('region', { name: 'Personal-fit evidence' })
  await expect(evidence.getByText('Next action').first()).toBeVisible()
  await expect(evidence.getByText('Add current_country, citizenships')).toBeVisible()
  await expect(evidence.getByText('Add profession, skills')).toBeVisible()
})

test('Profile separates missing inputs from external evidence constraints', async ({ page }) => {
  await page.goto('/country/ESP/profile')

  const readiness = page.getByRole('region', { name: 'Personal-fit decision readiness' })
  await expect(readiness).toBeVisible()
  await expect(readiness.getByText(/Readiness is not a country score/i)).toBeVisible()
  await expect(readiness.getByText('Work / residence feasibility')).toBeVisible()
  await expect(readiness.getByText('Career viability')).toBeVisible()
  await expect(readiness.getByText('Language viability')).toBeVisible()
  await expect(readiness.getByText('Purchasing-power viability')).toBeVisible()
  await expect(readiness.getByText('profile input', { exact: true })).toHaveCount(4)
})

test('Profile key actions state which decision each missing input unlocks', async ({ page }) => {
  await page.goto('/country/ESP/profile')

  await expect(page.getByText('Unlocks work / residence feasibility')).toBeVisible()
  await expect(page.getByText('Unlocks career viability')).toBeVisible()
  await expect(page.getByText('Unlocks language viability')).toBeVisible()
  await expect(page.getByText('Unlocks purchasing-power viability')).toBeVisible()
})

test('profile marks future financial inputs that do not affect current FinancialFit', async ({ page }) => {
  await page.goto('/country/ESP/profile')
  const profile = page.getByRole('region', { name: 'Personal profile' })
  await profile.getByRole('button', { name: 'Edit' }).click()

  await expect(profile.getByText('Stored for future household-budget modelling; not used in current FinancialFit.')).toBeVisible()
  await expect(profile.getByText('Stored for future transition-cost/runway modelling; not used in current FinancialFit.')).toBeVisible()
})

test('profile architecture keeps completion evidence outputs and TTV distinct', async ({ page }) => {
  await page.goto('/country/ESP/profile')
  const profile = page.getByRole('region', { name: 'Personal profile' })

  await expect(profile.getByText('Your profile', { exact: true })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Profile completion' })).toBeVisible()
  await expect(profile.getByText('Key gaps and actions')).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Personal-fit evidence' })).toBeVisible()
  await expect(profile.getByText('Completion measures required inputs only. It is not a country-fit score.')).toBeVisible()

  await profile.getByText('Detailed fit evidence and TTV').click()
  await expect(profile.getByRole('region', { name: 'TTV readiness' })).toBeVisible()
})

test('latest EURES annex provenance is visible in Skills and Languages', async ({ page }) => {
  await page.route('http://127.0.0.1:8020/api/countries/ESP/career-fit', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        target_country_iso3: 'ESP',
        status: 'evidence_available',
        market_signal: 'not_classified_as_shortage_or_surplus',
        market_signal_scope: 'isco_unit_group',
        market_signal_isco: '3512',
        vacancy_demand_evidence: null,
        occupation_match: {
          status: 'matched',
          selected: { preferred_label: 'ICT user support technician', match_score: 0.91, isco_group: '3512' },
          candidates: [],
          threshold: 0.72,
        },
        skill_match: {
          status: 'matched',
          dataset_mode: 'full',
          dataset_version: '1.2.1',
          matched_skills: [],
          missing_skills: [],
          coverage: 1,
        },
        source: {
          label: 'EURES Report on labour shortages and surpluses 2025 — Annex',
          evidence_id: 'eures_shortages_surpluses_2025_annex',
          rule_version: 'EURES_SHORTAGES_SURPLUSES_2025_ANNEX',
          report_year: 2026,
          conditions_year: 2025,
          scope: 'isco_unit_group',
        },
      }),
    })
  })

  await page.goto('/country/ESP/skills')
  await expect(page.getByText(/not classified as shortage or surplus · ISCO 3512/i)).toBeVisible()
  await expect(page.getByText(/EURES Report on labour shortages and surpluses 2025 — Annex · 2025 conditions · eures_shortages_surpluses_2025_annex/i)).toBeVisible()
})

test('vacancy rate remains contextual in Skills and Languages', async ({ page }) => {
  await page.goto('/country/ESP/skills')
  await expect(page.getByText('Eurostat 2024 · ISCO OC351 vacancy rate 3.4% · context only')).toBeVisible()
})

test('Skills distinguishes vacancy source coverage unavailable from zero demand', async ({ page }) => {
  await page.route('http://127.0.0.1:8020/api/countries/IRL/career-fit', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        target_country_iso3: 'IRL',
        status: 'evidence_available',
        market_signal: 'shortage',
        occupation_match: {
          selected: {
            preferred_label: 'ICT professional',
            match_score: 0.9,
            isco_group: '2522',
            code: '2522',
          },
        },
        vacancy_demand_evidence: {
          status: 'source_coverage_unavailable',
          dataset_id: 'jvs_a_isco3_r1',
          supported_countries: ['ESP', 'PRT'],
          isco_major: 'OC2',
          isco_3digit: 'OC252',
          granularity: 'isco_3digit',
          role: 'context_only',
        },
        skill_match: {
          status: 'matched',
          matched_skills: ['Windows'],
          missing_skills: ['cloud platforms'],
          coverage: 0.5,
          evidence_complete: true,
        },
        evidence_complete: true,
        source: {
          label: 'EURES Labour Market Information: Ireland',
          evidence_id: 'eures_country_lmi_2024_conditions',
          conditions_year: 2024,
          scope: 'broad_occupation_group',
        },
      }),
    })
  })

  await page.goto('/country/IRL/skills')

  await expect(page.getByText(/Eurostat experimental ISCO-3 source does not cover Ireland/i).first()).toBeVisible()
  await expect(page.getByText(/this is not zero demand/i)).toBeVisible()
})

test('versioned EURES market evidence is visible in Skills and Languages', async ({ page }) => {
  await page.goto('/country/ESP/skills')
  await expect(page.getByText(/EURES Labour Market Information: Spain · 2024 conditions · eures_country_lmi_2024_conditions/i)).toBeVisible()
})

test('FinancialFit partial evidence is not shown as complete or empty', async ({ page }) => {
  await page.route('http://127.0.0.1:8020/api/countries/ESP/financial-fit', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        target_country_iso3: 'ESP',
        status: 'local_income_reference_available',
        reason: 'occupation_specific_net_income_not_modelled',
        evidence_state: 'partial',
        evidence_complete: false,
        blockers: ['occupation_specific_net_income', 'household_budget'],
        portable_income_analysis: null,
        local_income_reference: {
          occupation_label: 'ICT support technician',
          occupation_match_score: 0.9,
          isco_group: '3512',
          ses_isco_major_group: 'OC3',
          gross_monthly_mean_eur: 3200,
          period: 2022,
          source_id: 'EUROSTAT',
          dataset_id: 'earn_ses_main',
        },
        national_net_earnings_reference: null,
        notes: [],
      }),
    })
  })

  await page.goto('/country/ESP/profile')
  const evidence = page.getByRole('region', { name: 'Personal-fit evidence' })
  const financialCard = evidence.locator('.evidenceStatusCard').filter({ hasText: 'Financial' })
  await expect(financialCard.getByText('partial', { exact: true })).toBeVisible()

  await page.getByText('Detailed fit evidence and TTV').click()
  await expect(page.getByText(/occupation specific net income · household budget/i)).toBeVisible()
})

test('structured FinancialFit blockers are visible', async ({ page }) => {
  await page.goto('/country/ESP/profile')
  const profile = page.getByRole('region', { name: 'Personal profile' })

  await expect(profile.getByText('FinancialFit incomplete')).toBeVisible()
  await expect(profile.getByText('Add: current_country, monthly_net_income', { exact: true })).toBeVisible()

  await profile.getByText('Detailed fit evidence and TTV').click()
  await expect(profile.getByText('FINANCIAL', { exact: true })).toBeVisible()
})

test('structured TTV blockers are visible', async ({ page }) => {
  await page.goto('/country/ESP/profile')
  const profile = page.getByRole('region', { name: 'Personal profile' })
  await profile.getByText('Detailed fit evidence and TTV').click()

  const ttv = profile.getByRole('region', { name: 'TTV readiness' })
  await expect(ttv.getByText('Blocked by', { exact: true })).toBeVisible()
  await expect(ttv).not.toContainText('Waiting for evidence')
})

test('candidate TTV range shows critical-path composition', async ({ page }) => {
  await page.route('http://127.0.0.1:8020/api/countries/ESP/ttv', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        target_country_iso3: 'ESP',
        method: 'ttv_dependency_graph_v1',
        stages: {},
        blocked_by: [],
        blocker_details: [],
        dependency_ready: true,
        temporal_evidence_state: 'candidate',
        temporal_model_version: null,
        temporal_evidence_ready: true,
        temporal_evidence: {
          calendar_ready: true,
          stages: { language: { status: 'available', guided_hours_min: 100, guided_hours_max: 250, weekly_study_hours: 10 } },
        },
        candidate_time_range: {
          weeks_min: 10,
          weeks_max: 25,
          composition: 'critical_path_v1',
          stage_groups: {},
        },
        estimate_status: 'temporal_model_missing',
        ready_for_time_estimate: false,
        time_estimate: null,
      }),
    })
  })

  await page.goto('/country/ESP/profile')
  await page.getByText('Detailed fit evidence and TTV').click()
  const ttv = page.getByRole('region', { name: 'TTV readiness' })
  await expect(ttv.getByText('Temporal evidence · candidate only')).toBeVisible()
  await expect(ttv.getByText(/10–25 weeks · critical path: preparation parallel → employment → financial · not an AUGUR estimate/)).toBeVisible()
  await expect(ttv.getByText('Estimate available')).toHaveCount(0)
})

test('candidate temporal evidence remains explicitly non-estimate', async ({ page }) => {
  await page.goto('/country/ESP/profile')
  await page.getByText('Detailed fit evidence and TTV').click()

  const ttv = page.getByRole('region', { name: 'TTV readiness' })
  await expect(ttv.getByText('Language planning evidence')).toBeVisible()
  await expect(ttv.getByText('Language: 100–250 guided hours · add study hours/week for calendar conversion')).toBeVisible()
  await expect(ttv.getByText('Estimate available')).toHaveCount(0)
})

test('opt-in TTV calibration observation lifecycle is visible in My Fit', async ({ page }) => {
  let observation: null | Record<string, unknown> = null

  await page.route('http://127.0.0.1:8020/api/countries/ESP/ttv', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        target_country_iso3: 'ESP',
        method: 'ttv_dependency_graph_v1',
        stages: {},
        blocked_by: [],
        blocker_details: [],
        dependency_ready: false,
        temporal_evidence_state: 'not_implemented',
        temporal_model_version: null,
        temporal_evidence_ready: true,
        temporal_evidence: {
          engine_version: 'ttv-temporal-evidence-v1',
          calendar_ready: true,
          estimation_scope: {
            scope_id: 'ttv-estimation-scope-v1',
            in_scope: true,
            blockers: [],
          },
          unavailable_stages: [],
          candidate_range: {
            weeks_min: 10,
            weeks_max: 25,
            composition: 'critical_path_v1',
          },
          stages: {
            language: {
              status: 'available',
              weeks_min: 10,
              weeks_max: 25,
              reason: 'cambridge_guided_hours_with_user_study_intensity',
              current_cefr: 'B1',
              target_cefr: 'B2',
              guided_hours_min: 100,
              guided_hours_max: 250,
              weekly_study_hours: 10,
            },
          },
        },
        candidate_time_range: {
          weeks_min: 10,
          weeks_max: 25,
          composition: 'critical_path_v1',
          stage_groups: {},
        },
        estimate_status: 'dependencies_blocked',
        ready_for_time_estimate: false,
        time_estimate: null,
        notes: [],
      }),
    })
  })

  await page.route('http://127.0.0.1:8020/api/countries/ESP/ttv/calibration/active', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        country_iso3: 'ESP',
        observation,
      }),
    })
  })

  await page.route('http://127.0.0.1:8020/api/countries/ESP/ttv/calibration/start', async route => {
    observation = {
      case_id: 'ttv-dev-esp-testcase',
      country_iso3: 'ESP',
      status: 'active',
      scope_id: 'ttv-estimation-scope-v1',
      engine_version: 'ttv-temporal-evidence-v1',
      composition: 'critical_path_v1',
      candidate_weeks_min: 10,
      candidate_weeks_max: 25,
      started_at: '2026-10-07T05:00:00+00:00',
      completed_at: null,
      baseline: {
        target_country_iso3: 'ESP',
        language: {
          current_cefr: 'B1',
          target_cefr: 'B2',
          weekly_study_hours: 10,
          guided_hours_min: 100,
          guided_hours_max: 250,
        },
      },
      completion: {},
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        country_iso3: 'ESP',
        observation,
      }),
    })
  })

  let completionPayload: unknown = null
  await page.route('http://127.0.0.1:8020/api/ttv/calibration/ttv-dev-esp-testcase/complete', async route => {
    completionPayload = route.request().postDataJSON()
    observation = null
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        observation: { status: 'completed' },
        calibration_case: {
          case_id: 'ttv-dev-esp-testcase',
          sample_role: 'development',
          observed_weeks: 12,
          context: {
            achieved_cefr: 'B2',
            outcome_evidence_type: 'official_exam',
          },
        },
      }),
    })
  })

  await page.goto('/country/ESP/profile')
  await page.getByText('Detailed fit evidence and TTV').click()
  const ttv = page.getByRole('region', { name: 'TTV readiness' })

  await expect(ttv.getByText('Help validate TTV v1')).toBeVisible()
  await expect(ttv.getByText(/Local|Opt in/i)).toBeVisible()
  await ttv.getByRole('button', { name: 'Start calibration observation' }).click()

  await expect(ttv.getByText('TTV v1 calibration observation active')).toBeVisible()
  await expect(ttv.getByText(/candidate 10–25 weeks/i)).toBeVisible()

  const recordButton = ttv.getByRole('button', { name: 'Record documented outcome' })
  await expect(recordButton).toBeDisabled()
  await ttv.getByLabel('Achieved CEFR').selectOption('B2')
  await ttv.getByLabel('Outcome evidence').selectOption('official_exam')
  await expect(recordButton).toBeEnabled()
  await recordButton.click()

  expect(completionPayload).toMatchObject({
    achieved_cefr: 'B2',
    evidence_type: 'official_exam',
    observed_at: null,
  })
  await expect(ttv.getByText('TTV v1 calibration observation active')).toHaveCount(0)
  await expect(ttv.getByRole('button', { name: 'Start calibration observation' })).toBeVisible()
})

test('My Fit exposes TTV calibration diagnostics without implying validation', async ({ page }) => {
  await page.route('http://127.0.0.1:8020/api/ttv/calibration/status', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        protocol_state: 'definitions_frozen_acceptance_pending',
        protocol_version: null,
        development_case_count: 6,
        holdout_case_count: 0,
        interval_coverage_pct: 66.67,
        mean_interval_width_weeks: 14.5,
        mean_absolute_midpoint_error_weeks: 5.2,
        mean_miss_distance_weeks: 3.0,
        context_summary: {
          context_case_count: 6,
          current_cefr_levels: ['A2', 'B1'],
          target_cefr_levels: ['B2'],
          weekly_study_hours: [5, 10],
        },
        protocol_readiness: {
          blockers: ['protocol_version', 'acceptance_criteria'],
        },
      }),
    })
  })

  await page.goto('/country/ESP/profile')
  await page.getByText('Detailed fit evidence and TTV').click()

  const diagnostics = page.getByLabel('TTV calibration diagnostics')
  await expect(diagnostics).toBeVisible()
  await expect(diagnostics.getByText('6', { exact: true })).toBeVisible()
  await expect(diagnostics.getByText('66.7%')).toBeVisible()
  await expect(diagnostics.getByText('14.5 wk')).toBeVisible()
  await expect(diagnostics.getByText('A2 · B1')).toBeVisible()
  await expect(page.getByText('Study-intensity cohorts: 5 · 10 h/week')).toBeVisible()
  await expect(page.getByText(/validated|validation passed/i)).toHaveCount(0)
})

test('TTV development exchange can export and import from My Fit', async ({ page }) => {
  const exchange = {
    exchange_version: 'ttv-development-exchange-v1',
    schema_version: 'ttv-calibration-v1',
    scope_id: 'ttv-estimation-scope-v1',
    privacy: {
      contains_full_profile: false,
      contains_name: false,
      contains_email: false,
      contains_address: false,
      contains_free_text_history: false,
    },
    case_count: 1,
    cases: [{
      case_id: 'exchange-001',
      country_iso3: 'IRL',
      employment_mode: 'remote',
      engine_version: 'ttv-temporal-evidence-v1',
      composition: 'critical_path_v1',
      candidate_weeks_min: 10,
      candidate_weeks_max: 25,
      observed_weeks: 12,
      sample_role: 'development',
      start_event_definition_version: 'ttv-start-active-language-transition-v1',
      viability_outcome_definition_version: 'ttv-outcome-b2-remote-viability-v1',
      stage_timings: {},
    }],
    notes: [],
  }

  await page.route('http://127.0.0.1:8020/api/ttv/calibration/export', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(exchange),
    })
  })

  let importedPayload: unknown = null
  await page.route('http://127.0.0.1:8020/api/ttv/calibration/import', async route => {
    importedPayload = route.request().postDataJSON()
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        exchange_version: 'ttv-development-exchange-v1',
        imported_count: 1,
        case_ids: ['exchange-001'],
      }),
    })
  })

  await page.goto('/country/ESP/profile')
  await page.getByText('Detailed fit evidence and TTV').click()
  const portability = page.getByRole('region', { name: 'TTV readiness' })
    .getByLabel('TTV calibration data portability')

  await expect(portability.getByText('Calibration data portability')).toBeVisible()
  await expect(portability.getByText(/profile and personal history excluded/i)).toBeVisible()

  const downloadPromise = page.waitForEvent('download')
  await portability.getByRole('button', { name: 'Export anonymous development cases' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('AUGUR_TTV_DEVELOPMENT_EXCHANGE.json')
  await expect(portability.getByText('Anonymous development package exported.')).toBeVisible()

  await portability.locator('input[type="file"]').setInputFiles({
    name: 'AUGUR_TTV_DEVELOPMENT_EXCHANGE.json',
    mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify(exchange)),
  })

  await expect(portability.getByText('Development package imported locally.')).toBeVisible()
  expect(importedPayload).toMatchObject({
    exchange_version: 'ttv-development-exchange-v1',
    case_count: 1,
  })
})

test('map starts broad and exposes regional detail when country is focused', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  const map = page.getByTestId('regional-map')
  await expect(map).toBeVisible()
  await expect(map.locator('.nuts2Boundary')).toHaveCount(0)
  await expect(map).toHaveAttribute('data-map-status', 'ready')

  await page.getByRole('button', { name: 'Focus country' }).click()

  await expect.poll(async () => map.locator('.nuts2Boundary').count()).toBeGreaterThan(0)
})



test('map exposes selectable Urban Audit cities only at high zoom', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  const map = page.getByTestId('regional-map')
  await expect(map).toHaveAttribute('data-map-status', 'ready')
  await page.getByRole('button', { name: 'Focus country' }).click()

  await expect(map.locator('.urbanAuditCity')).toHaveCount(0)

  const zoomIn = map.locator('.leaflet-control-zoom-in')
  const cities = map.locator('.urbanAuditCity')
  for (let step = 0; step < 16; step += 1) {
    const before = Number(await map.getAttribute('data-map-zoom'))
    if (before >= 8.5) break
    await zoomIn.click()
    await expect.poll(
      async () => Number(await map.getAttribute('data-map-zoom')),
    ).toBeGreaterThan(before)
  }

  await expect(map).toHaveAttribute('data-map-zoom', /^(8\.5|9\.0|9\.5|10\.0)$/)
  await expect.poll(async () => cities.count()).toBeGreaterThan(0)

  const madrid = cities.first()
  await expect(madrid).toBeVisible()
  await page.evaluate(() => {
    const marker = document.querySelector('.leafletAugurMap .urbanAuditCity')
    marker?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
  })

  await expect(page.getByText('CITY · Madrid · ES001C')).toBeVisible()
  const cityEvidence = page.getByRole('region', { name: 'Selected geographic evidence' })
  await expect(cityEvidence.getByText('Urban Audit + EEA')).toBeVisible()
  await expect(cityEvidence.getByText('3,420,000')).toBeVisible()
  await expect(cityEvidence.getByText('9.0 µg/m³')).toBeVisible()
  await expect(cityEvidence.getByText(/observed air quality from validated EEA/i)).toBeVisible()
})

test('Overview reveals NUTS 3 safety context', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  const map = page.getByTestId('regional-map')
  await expect(map).toBeVisible()

  const zoomIn = map.locator('.leaflet-control-zoom-in')
  for (let i = 0; i < 12; i += 1) {
    const before = Number(await map.getAttribute('data-map-zoom'))
    if (before >= 7) break
    await zoomIn.click()
    await expect.poll(
      async () => Number(await map.getAttribute('data-map-zoom')),
    ).toBeGreaterThan(before)
  }

  await expect.poll(
    async () => map.locator('.nuts3Boundary').count(),
  ).toBeGreaterThan(0)
  const nuts3 = map.locator('.nuts3Boundary').first()
  await expect(nuts3).toHaveCount(1)
  await page.evaluate(() => {
    const region = document.querySelector('.leafletAugurMap .nuts3Boundary')
    region?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
  })

  const evidence = page.getByRole('region', { name: 'Regional metric cards' })
  await expect(evidence.getByText('Police-recorded intentional homicide')).toBeVisible()
  await expect(evidence.getByText('0.7 /100k')).toBeVisible()
  await expect(evidence.getByText('Police-recorded robbery')).toBeVisible()
  await expect(evidence.getByText('34.1 /100k')).toBeVisible()
})

test('unsaved profile edits survive target-country switching', async ({ page }) => {
  await page.goto('/country/ESP/profile')
  const profile = page.getByRole('region', { name: 'Personal profile' })
  await profile.getByRole('button', { name: 'Edit' }).click()
  const profession = profile.getByLabel('Profession')
  const selector = page.getByLabel('Select country')

  await profession.fill('Unsaved draft role')
  await selector.selectOption('PRT')

  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(profession).toHaveValue('Unsaved draft role')
})

test('partial country endpoint failure keeps healthy sections visible', async ({ page }) => {
  await page.route('**/api/countries/PRT/scenarios', async route => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'synthetic scenarios failure' }),
    })
  })

  await page.getByLabel('Select country').selectOption('PRT')

  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(page.getByText('1. COUNTRY RADAR / Overview')).toBeVisible()
  await expect(page.getByText(/Scenarios HTTP 500/)).toBeVisible()
})


test('rapid country switching keeps the latest selection', async ({ page }) => {
  await page.route('**/api/countries/PRT/snapshot', async route => {
    await new Promise(resolve => setTimeout(resolve, 250))
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        country_iso3: 'PRT',
        observation_count: 1,
        indicators: [metric('PRT')],
      }),
    })
  })

  const selector = page.getByLabel('Select country')
  await selector.selectOption('PRT')
  await selector.selectOption('IRL')

  await expect(page.getByLabel('Select country')).toHaveValue('IRL')
  await expect(selector).toHaveValue('IRL')
})


test('unsaved profile draft survives view navigation', async ({ page }) => {
  await page.getByRole('button', { name: 'Profile' }).click()
  const profile = page.getByRole('region', { name: 'Personal profile' })
  await profile.getByRole('button', { name: 'Edit' }).click()
  const profession = profile.getByLabel('Profession')

  await profession.fill('Draft preserved across views')
  await page.getByRole('button', { name: 'Overview' }).click()
  await page.getByRole('button', { name: 'Profile' }).click()
  await page.getByRole('region', { name: 'Personal profile' }).getByRole('button', { name: 'Edit' }).click()
  await expect(page.getByLabel('Profession')).toHaveValue('Draft preserved across views')
})

test('comparison selectors swap countries without duplicates', async ({ page }) => {
  await page.getByRole('button', { name: 'Compare' }).click()

  const first = page.getByLabel('Compare country 1', { exact: true })
  const second = page.getByLabel('Compare country 2', { exact: true })
  const third = page.getByLabel('Compare country 3', { exact: true })

  await expect(first).toHaveValue('IRL')
  await expect(second).toHaveValue('ESP')
  await expect(third).toHaveValue('PRT')

  await first.selectOption('ESP')

  await expect(first).toHaveValue('ESP')
  await expect(second).toHaveValue('IRL')
  await expect(third).toHaveValue('PRT')
})

test('Country Radar domain cards use observed history for sparklines', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  const labourCard = page.locator('.countryMetricCard').filter({ hasText: 'Labour market' })
  await expect(labourCard.locator('.countryMetricSparkline svg')).toBeVisible()
  await expect(labourCard.locator('.countryMetricSparkline polyline')).toHaveAttribute('points', /,/)
  await expect(labourCard.getByText('EUROSTAT · 2025')).toBeVisible()
})

test('Country Radar uses a fixed evidence-first composition', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/country/ESP/overview')

  await expect(page.locator('.countryRadarHero')).toBeVisible()
  await expect(page.locator('.countryIdentityCard')).toBeVisible()
  await expect(page.locator('.countryRadarMap')).toBeVisible()
  await expect(page.locator('.recentChangesPanel')).toBeVisible()
  await expect(page.locator('.countryMetricGrid')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Edit layout' })).toHaveCount(0)
})

test('direct route refresh preserves country and view', async ({ page }) => {
  await page.goto('/country/PRT/outlook')
  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(page.getByText('3. FUTURE PATHS / Outlook')).toBeVisible()
  await expect(page.getByTestId('world-map')).toHaveCount(0)

  await page.reload()

  await expect(page).toHaveURL(/\/country\/PRT\/outlook$/)
  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(page.getByText('3. FUTURE PATHS / Outlook')).toBeVisible()
})

test('compare selection is encoded in URL and survives reload', async ({ page }) => {
  await page.goto('/compare?countries=ESP,PRT,IRL')

  await expect(page.getByLabel('Compare country 1', { exact: true })).toHaveValue('ESP')
  await expect(page.getByLabel('Compare country 2', { exact: true })).toHaveValue('PRT')
  await expect(page.getByLabel('Compare country 3', { exact: true })).toHaveValue('IRL')

  await page.getByLabel('Compare country 1', { exact: true }).selectOption('IRL')
  await expect(page).toHaveURL(/countries=IRL,PRT,ESP|countries=IRL%2CPRT%2CESP/)

  await page.reload()

  await expect(page.getByLabel('Compare country 1', { exact: true })).toHaveValue('IRL')
  await expect(page.getByLabel('Compare country 2', { exact: true })).toHaveValue('PRT')
  await expect(page.getByLabel('Compare country 3', { exact: true })).toHaveValue('ESP')
})


test('Country Radar renders the approved evidence composition', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/country/ESP/overview')

  await expect(page.getByRole('region', { name: 'Country overview' })).toBeVisible()
  await expect(page.getByTestId('regional-map')).toBeVisible()
  await expect(page.getByText('1. COUNTRY RADAR / Overview')).toBeVisible()
  await expect(page.getByText('Largest measured movements')).toBeVisible()
  await expect(page.locator('.countryMetricCard')).toHaveCount(10)

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }))
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth + 2)
})

test('Country Radar stays readable at 1920x900', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 900 })
  await page.goto('/country/ESP/overview')

  await expect(page.locator('.countryRadarHero')).toBeVisible()
  await expect(page.locator('.countryMetricGrid')).toBeVisible()

  const boxes = await page.evaluate(() => {
    const box = (selector: string) => {
      const node = document.querySelector(selector)
      if (!node) return null
      const rect = node.getBoundingClientRect()
      return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom }
    }
    return {
      identity: box('.countryIdentityCard'),
      map: box('.countryRadarMap'),
      changes: box('.recentChangesPanel'),
      metrics: box('.countryMetricGrid'),
    }
  })

  for (const value of Object.values(boxes)) expect(value).not.toBeNull()
  expect(boxes.identity!.right).toBeLessThanOrEqual(boxes.map!.left)
  expect(boxes.map!.right).toBeLessThanOrEqual(boxes.changes!.left)
  expect(boxes.metrics!.top).toBeGreaterThan(boxes.map!.top)
})

test('Country Radar panels do not overlap at 1920x1080', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/country/ESP/overview')

  const boxes = await page.evaluate(() => {
    const box = (selector: string) => {
      const node = document.querySelector(selector)
      if (!node) return null
      const rect = node.getBoundingClientRect()
      return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom }
    }
    return [
      box('.countryIdentityCard'),
      box('.countryRadarMap'),
      box('.recentChangesPanel'),
    ]
  })

  const overlaps = (
    a: { left: number; right: number; top: number; bottom: number },
    b: { left: number; right: number; top: number; bottom: number },
  ) => !(a.right <= b.left || b.right <= a.left || a.bottom <= b.top || b.bottom <= a.top)

  for (const value of boxes) expect(value).not.toBeNull()
  expect(overlaps(boxes[0]!, boxes[1]!)).toBe(false)
  expect(overlaps(boxes[1]!, boxes[2]!)).toBe(false)
})

test('Country Radar keeps country context and evidence cards visible', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  await expect(page.locator('.topbarCountry .flagIcon')).toHaveCount(1)
  await expect(page.getByTestId('regional-map')).toBeVisible()
  await expect(page.locator('.countryIdentityCard')).toBeVisible()
  await expect(page.locator('.countryMetricCard')).toHaveCount(10)
  await expect(page.getByText('No single composite score.')).toBeVisible()
})

test('Future Paths distinguishes official baseline from AUGUR model scenarios', async ({ page }) => {
  await page.goto('/country/ESP/outlook')

  await expect(page.getByText('OFFICIAL FORECAST', { exact: true })).toBeVisible()
  await expect(page.getByText('AUGUR MODEL SCENARIOS', { exact: true })).toBeVisible()
  await expect(page.getByText('not probabilistic', { exact: true })).toBeVisible()
  await expect(page.locator('.officialLine')).toBeVisible()
  await expect(page.locator('.scenarioLine.improvement')).toBeVisible()
  await expect(page.locator('.scenarioLine.stress')).toBeVisible()
})

test('Future Paths marks the forecast boundary and model status', async ({ page }) => {
  await page.goto('/country/ESP/outlook')

  await expect(page.getByText('EXPERIMENTAL')).toBeVisible()
  await expect(page.getByText('not probabilistic')).toBeVisible()
  await expect(page.locator('.forecastBoundary')).toHaveCount(1)
  await expect(page.getByText('forecast →')).toBeVisible()
  await expect(page.locator('.forecastYearLabel')).toHaveCount(5)
})

test('Future Paths avoids fake model envelopes for contextual indicators', async ({ page }) => {
  await page.goto('/country/PRT/outlook')

  await expect(page.getByText('No directional scenario envelope is applied.')).toBeVisible()
  await expect(page.locator('.scenarioLine.improvement')).toHaveCount(0)
  await expect(page.locator('.scenarioLine.stress')).toHaveCount(0)
})

for (const viewport of [
  { width: 1366, height: 768 },
  { width: 1024, height: 768 },
  { width: 390, height: 844 },
]) {
  test(`responsive shell avoids horizontal overflow at ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport)

    for (const path of [
      '/country/ESP/overview',
      '/country/ESP/indicators',
      '/country/ESP/dimension/productive_capacity',
      '/country/ESP/outlook',
      '/country/ESP/profile',
      '/country/ESP/skills',
      '/compare?countries=ESP,PRT,IRL',
    ]) {
      await page.goto(path)
      await expect(page.locator('main.shell')).toBeVisible()

      const overflow = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
      }))

      expect(
        overflow.scrollWidth,
        `horizontal overflow at ${viewport.width}x${viewport.height} on ${path}`,
      ).toBeLessThanOrEqual(overflow.innerWidth + 2)
    }
  })
}



test('Skills and Languages replaces empty tables with evidence-aware onboarding', async ({ page }) => {
  await page.goto('/country/ESP/skills')

  const onboarding = page.getByRole('region', { name: 'Skills profile onboarding' })
  await expect(onboarding).toBeVisible()
  await expect(onboarding.getByText('Add your profession to unlock occupation-level evidence')).toBeVisible()
  await expect(onboarding.getByText('Profession', { exact: true })).toBeVisible()
  await expect(onboarding.getByText('Skills', { exact: true })).toBeVisible()
  await expect(onboarding.getByText('Languages', { exact: true })).toBeVisible()
  await expect(onboarding.getByText(/Cedefop occupation outlook/i)).toBeVisible()
  await expect(page.locator('.skillsDemandTable')).toHaveCount(0)
})

test('captures Skills and Languages populated visual fixture', async ({ page }) => {
  await page.route('http://127.0.0.1:8020/api/profile', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        profile_id: 'visual-skills',
        age: 50,
        current_country: 'ESP',
        citizenships: ['ESP'],
        profession: 'Systems engineer',
        skills: ['Windows', 'Azure', 'Python', 'SQL', 'PowerShell'],
        languages: [
          { language: 'Spanish', cefr: 'C2' },
          { language: 'English', cefr: 'B2' },
        ],
        household_size: 2,
        monthly_net_income: 1650,
        liquid_savings: null,
        remote_work: false,
        preferences: {},
      }),
    })
  })

  await page.route('http://127.0.0.1:8020/api/countries/ESP/career-fit', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        target_country_iso3: 'ESP',
        status: 'evidence_available',
        market_signal: 'not_classified_as_shortage_or_surplus',
        market_signal_scope: 'isco_unit_group',
        market_signal_isco: '3512',
        vacancy_demand_evidence: {
          status: 'available',
          vacancy_rate_pct: 3.4,
          period: '2026-Q2',
          source_id: 'EUROSTAT',
          granularity: 'isco_major',
          isco_major: '3',
        },
        occupation_trend_evidence: {
          status: 'available',
          evidence_type: 'short_term_employment_outlook',
          latest_period: 2027,
          latest_growth_pct: 2.5,
          direction: 'positive_growth',
          role: 'context_only',
        },
        future_shortage_index_evidence: {
          status: 'available',
          source_id: 'CEDEFOP',
          dataset_id: 'CEDEFOP_CLSSI',
          release_version: '2026',
          horizon: 2035,
          isco08: '35',
          granularity: 'isco_2digit',
          occupation_label: 'Information and communications technicians',
          main_occupation_group: 'High-skilled non-manual occupations',
          shortage_index: 3.3333333,
          component_code: '4-3-3',
          components: {
            employment_growth: 4,
            replacement_demand: 3,
            skills_imbalance: 3,
          },
          scale: {
            minimum: 1,
            maximum: 4,
            direction: 'higher_means_more_intense_shortage',
          },
          role: 'context_only',
        },
        skill_demand_trend_evidence: {
          status: 'source_access_gated',
          source_id: 'CEDEFOP',
          dataset_id: 'CEDEFOP_SKILLS_OVATE',
          access_path: 'Eurostat Microdata access portal',
          reproducible_public_ingestion: false,
          role: 'withheld_until_reproducible_access',
        },
        language_oja_requirements_evidence: {
          status: 'source_access_gated',
          source_id: 'CEDEFOP',
          dataset_id: 'CEDEFOP_SKILLS_OVATE',
          access_path: 'Eurostat Microdata access portal',
          reproducible_public_ingestion: false,
          role: 'withheld_until_reproducible_access',
        },
        occupation_match: {
          status: 'matched',
          selected: {
            preferred_label: 'ICT user support technician',
            match_score: 0.91,
            isco_group: '3512',
            code: '3512',
          },
        },
        skill_match: {
          dataset_mode: 'full',
          dataset_version: 'ESCO 1.2.1',
          occupation_label: 'ICT user support technician',
          matched_skills: ['Windows', 'Azure', 'SQL', 'PowerShell'],
          missing_skills: ['network troubleshooting', 'ICT security policies'],
          coverage: 0.67,
          evidence_complete: true,
        },
        source: {
          label: 'EURES Report on labour shortages and surpluses 2025 — Annex',
          evidence_id: 'eures_shortages_surpluses_2025_annex',
          conditions_year: 2025,
          scope: 'isco_unit_group',
        },
      }),
    })
  })

  await page.route('http://127.0.0.1:8020/api/countries/ESP/language-fit', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        target_country_iso3: 'ESP',
        status: 'evidence_available',
        target_languages: ['Spanish', 'English'],
        matches: [
          { language: 'Spanish', declared_cefr: 'C2', meets_work_ready_heuristic: true },
          { language: 'English', declared_cefr: 'B2', meets_work_ready_heuristic: true },
        ],
        work_ready_threshold: 'B2',
        work_ready: true,
        occupation_language_evidence: {
          status: 'available',
          occupation_label: 'ICT user support technician',
          essential_skill_count: 1,
          optional_skill_count: 1,
        },
      }),
    })
  })

  await page.setViewportSize({ width: 1920, height: 900 })
  await page.goto('/country/ESP/skills')
  await expect(page.locator('.skillsDemandTable')).toBeVisible()
  await expect(page.getByText('ICT user support technician', { exact: true })).toBeVisible()

  const coverage = page.getByRole('region', { name: 'Demand evidence coverage' })
  await expect(coverage).toBeVisible()
  await expect(coverage.getByText('Future shortage pressure')).toBeVisible()
  await expect(coverage.getByText(/ACTIVE · 2035/i)).toBeVisible()
  await expect(coverage.getByText(/Cedefop CLSSI · index 3\.33\/4 · ISCO-2 35 · growth 4 · replacement 3 · imbalance 3/i)).toBeVisible()
  await expect(coverage.getByText(/Cedefop STAS/i)).toBeVisible()
  await expect(coverage.getByText(/SOURCE ACCESS GATED/i).first()).toBeVisible()
  await expect(coverage.getByText(/Skills-OVATE detailed OJA evidence/i).first()).toBeVisible()

  await page.getByRole('button', { name: 'Rising skills' }).click()
  await expect(page.getByText(/Occupation outlook: positive growth/i)).toBeVisible()
  await expect(page.getByText(/source access gated via Eurostat microdata/i)).toBeVisible()

  await page.getByRole('button', { name: 'Job-ad language demand' }).click()
  await expect(page.getByText(/Job-ad language demand is source-access gated/i)).toBeVisible()

  await page.screenshot({
    path: 'test-results/ui-audit-skills-languages-populated-1920x900.png',
    fullPage: false,
  })
})

test('secondary views keep their desktop composition at 1920x900', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 900 })

  await page.goto('/country/ESP/profile')
  await expect(page.locator('.myFitTopGrid')).toBeVisible()

  await page.goto('/country/ESP/indicators')
  await expect(page.locator('.evidenceExplorerLayout')).toBeVisible()
  await expect(page.locator('.evidenceExplorerTable')).toBeVisible()

  await page.goto('/country/ESP/outlook')
  await expect(page.locator('.futurePathsGrid')).toBeVisible()
  await expect(page.locator('.forecastPanel')).toBeVisible()
  await expect(page.locator('.scenarioPanel')).toBeVisible()

  await page.goto('/compare?countries=ESP,PRT,IRL')
  await expect(page.locator('.decisionMatrixLayout')).toBeVisible()
  await expect(page.locator('.decisionMatrixTable')).toBeVisible()

  await page.goto('/country/ESP/skills')
  await expect(page.locator('.skillsLanguagesGrid')).toBeVisible()

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }))
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth + 2)
})

test('captures Overview desktop visual artifact', async ({ page }) => {
  const dimension = (
    trajectory: 'improving' | 'mixed' | 'contextual',
    signalName: string,
  ) => ({
    trajectory,
    confidence: 'high',
    indicator_count: 3,
    directional_indicator_count: trajectory === 'contextual' ? 0 : 2,
    coverage: 1,
    improving_signals: trajectory === 'improving'
      ? [{ indicator_id: signalName, name: signalName, direction: 'increase', confidence: 'high', pct_change_5y: 5 }]
      : [],
    deteriorating_signals: [],
    stable_signals: trajectory === 'mixed'
      ? [{ indicator_id: signalName, name: signalName, direction: 'stable', confidence: 'medium', pct_change_5y: 0 }]
      : [],
    contextual_signals: trajectory === 'contextual'
      ? [{ indicator_id: signalName, name: signalName, direction: 'contextual', confidence: 'high', pct_change_5y: null }]
      : [],
  })

  await page.route(
    'http://127.0.0.1:8020/api/countries/ESP/assessment',
    async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          country_iso3: 'ESP',
          method: 'visual-fixture',
          dimensions: {
            prosperity: dimension('improving', 'Real GDP growth'),
            productive_capacity: dimension('improving', 'Employment rate'),
            housing: dimension('mixed', 'Housing cost burden'),
            demography: dimension('contextual', 'Population structure'),
            human_systems: dimension('improving', 'Tertiary attainment'),
            fiscal: dimension('contextual', 'Fiscal balance'),
            strategic_resilience: dimension('contextual', 'Energy resilience'),
          },
        }),
      })
    },
  )

  await page.route(
    'http://127.0.0.1:8020/api/countries/ESP/scenarios',
    async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          country_iso3: 'ESP',
          method: 'visual-fixture',
          horizons: [2030, 2035, 2045],
          scenario_names: ['baseline', 'improvement', 'stress'],
          indicators: [{
            name: 'Fertility rate, total',
            unit: 'ratio',
            scenarios: {
              baseline: 1.26,
              improvement: 1.42,
              stress: 1.08,
            },
          }],
          notes: [],
        }),
      })
    },
  )

  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/country/ESP/overview')
  await page.screenshot({
    path: 'test-results/overview-desktop-1080.png',
    fullPage: false,
  })

  await page.setViewportSize({ width: 1920, height: 900 })
  await page.screenshot({
    path: 'test-results/overview-desktop-900.png',
    fullPage: false,
  })
})




test('captures full AUGUR UI audit set', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 900 })

  const views = [
    ['overview', '/country/ESP/overview'],
    ['indicators', '/country/ESP/indicators'],
    ['dimension-productive-capacity', '/country/ESP/dimension/productive_capacity'],
    ['outlook', '/country/ESP/outlook'],
    ['compare', '/compare?countries=ESP,PRT,IRL'],
    ['profile', '/country/ESP/profile'],
    ['skills-languages', '/country/ESP/skills'],
  ] as const

  for (const [name, path] of views) {
    await page.goto(path)
    await expect(page.locator('main.shell')).toBeVisible()

    await page.screenshot({
      path: `test-results/ui-audit-${name}-1920x900.png`,
      fullPage: false,
    })

    if (name !== 'overview') {
      await page.screenshot({
        path: `test-results/ui-audit-${name}-full.png`,
        fullPage: true,
      })
    }
  }
})

test('Country Radar hero never overlaps metric cards', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/country/ESP/overview')

  const hero = await page.locator('.countryRadarHero').boundingBox()
  const metrics = await page.locator('.countryMetricGrid').boundingBox()
  expect(hero).not.toBeNull()
  expect(metrics).not.toBeNull()
  expect((hero?.y ?? 0) + (hero?.height ?? 0)).toBeLessThanOrEqual((metrics?.y ?? 0) - 2)
})

test('Country Radar keeps core content within desktop width', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/country/ESP/overview')

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }))
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth + 2)
})

test('responsive Country Radar preserves core panels', async ({ page }) => {
  for (const viewport of [
    { width: 1366, height: 768 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport)
    await page.goto('/country/ESP/overview')

    await expect(page.getByTestId('regional-map')).toBeVisible()
    await expect(page.locator('.countryIdentityCard')).toBeVisible()
    await expect(page.locator('.recentChangesPanel')).toBeVisible()
    await expect(page.locator('.countryMetricGrid')).toBeVisible()
  }
})

test('mobile My Fit keeps summary, completion, actions and evidence reachable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/country/ESP/profile')

  const profile = page.getByRole('region', { name: 'Personal profile' })
  await expect(profile.getByText('Your profile', { exact: true })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Profile completion' })).toBeVisible()
  await expect(profile.getByText('Key gaps and actions')).toBeVisible()
  await expect(profile.getByText('Your priorities')).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Personal-fit evidence' })).toBeVisible()
})



test('city evidence is grouped into demography mobility tourism and environment', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  const selector = page.getByLabel('Select country')
  await expect(selector.locator('option')).toHaveCount(countries.length)

  const map = page.getByTestId('regional-map')
  await expect(map).toHaveAttribute('data-map-status', 'ready')

  await page.getByRole('button', { name: 'Focus country' }).click()
  await expect.poll(async () => Number(await map.getAttribute('data-map-zoom'))).toBeGreaterThanOrEqual(4)

  const zoomIn = page.locator('.leaflet-control-zoom-in')
  await expect.poll(async () => Number(await map.getAttribute('data-map-zoom'))).toBeGreaterThanOrEqual(3)

  while (Number(await map.getAttribute('data-map-zoom')) < 8.5) {
    await zoomIn.click()
    await page.waitForTimeout(25)
  }

  await expect.poll(async () => map.locator('.urbanAuditCity').count()).toBeGreaterThan(0)
  const cityMarker = map.locator('.urbanAuditCity').first()
  await expect(cityMarker).toBeVisible()
  await cityMarker.click({ force: true })

  const geographicEvidence = page.getByRole('region', { name: 'Selected geographic evidence' })
  await expect(geographicEvidence.getByText('Demography', { exact: true })).toBeVisible()
  await expect(geographicEvidence.getByText('Mobility', { exact: true })).toBeVisible()
  await expect(geographicEvidence.getByText('Tourism', { exact: true })).toBeVisible()
  await expect(geographicEvidence.getByText('Environment', { exact: true })).toBeVisible()
  await expect(geographicEvidence.getByText('Median population age')).toBeVisible()
  await expect(geographicEvidence.getByText('Monthly public transport ticket')).toBeVisible()
  await expect(geographicEvidence.getByText('Tourist overnight stays per resident')).toBeVisible()
  await expect(geographicEvidence.getByText('Observed annual mean PM2.5')).toBeVisible()
  await expect(geographicEvidence.getByText('43.7 years')).toBeVisible()
  await expect(geographicEvidence.getByText('€54.60 /month')).toBeVisible()
})

test('regional sector context appears for selected NUTS2 region', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  await page.getByRole('button', { name: 'Focus country' }).click()
  const map = page.getByTestId('regional-map')
  await expect(map).toBeVisible()

  await page.evaluate(() => {
    const paths = Array.from(document.querySelectorAll('.leafletAugurMap .nuts2Boundary'))
    const target = paths[0] as SVGPathElement | undefined
    target?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
  })

  await expect(page.getByText('Regional employment structure')).toBeVisible()
  await expect(page.getByText('J · Information and communication')).toBeVisible()
  await expect(page.getByText('7.0%')).toBeVisible()
})
