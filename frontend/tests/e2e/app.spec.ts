import { expect, test, type Page } from '@playwright/test'

const countries = [
  { iso2: 'ES', iso3: 'ESP', name: 'Spain', region: 'Europe', subregion: 'Southern Europe', currency: 'EUR', eu_member: true, eurozone_member: true, oecd_member: true },
  { iso2: 'PT', iso3: 'PRT', name: 'Portugal', region: 'Europe', subregion: 'Southern Europe', currency: 'EUR', eu_member: true, eurozone_member: true, oecd_member: true },
  { iso2: 'IE', iso3: 'IRL', name: 'Ireland', region: 'Europe', subregion: 'Northern Europe', currency: 'EUR', eu_member: true, eurozone_member: true, oecd_member: true },
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
  const lowerIsBetter = ['unemployment_rate', 'imf_unemployment_rate', 'housing_cost_overburden_rate', 'energy_import_dependency'].includes(item.indicator_id)
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

    if (path.endsWith('/career-fit')) {
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
          vacancy_rate_pct: 3.4,
          period: '2026-Q2',
          nace_scope: 'B-T',
          source_id: 'EUROSTAT',
          dataset_id: 'jvs_q_isco_r21',
          granularity: 'isco_major_group',
          role: 'context_only',
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
          ['productive_capacity', 'prosperity', 'housing', 'human_systems', 'demography', 'strategic_resilience'].map((dimension) => {
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

test('Overview exposes selectable official NUTS 2 regions', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  await expect(page.getByTestId('regional-map')).toBeVisible()
  await page.getByRole('button', { name: 'Regions' }).click()
  await expect(page.getByTestId('regional-map').getByRole('button', { name: 'Galicia' })).toBeVisible()
  await page.getByTestId('regional-map').getByRole('button', { name: 'Galicia' }).click()

  await expect(page.getByText('Galicia · ES11')).toBeVisible()
  await expect(page.getByText('Geography: Eurostat GISCO · NUTS 2024 · level 2 · EPSG:4326')).toBeVisible()

  await page.getByRole('button', { name: 'Map', exact: true }).click()
  await expect(page.getByTestId('regional-map')).toBeVisible()
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
  await expect(page.getByText('How sensitive is the comparison?')).toBeVisible()
})


test('Decision Matrix uses relative spreads and neutral selected-set positions', async ({ page }) => {
  await page.goto('/compare?countries=ESP,PRT,IRL')

  await expect(page.getByText('Largest relative spreads')).toBeVisible()
  await expect(page.getByText(/descriptive, not a quality score/i)).toBeVisible()
  await expect(page.locator('.matrixPositionBadge')).toHaveCount(24)
  await expect(page.locator('.matrixDomainRow')).toHaveCount(6)
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

test('regional map renders selected-country geometry and city anchors', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  const map = page.getByTestId('regional-map')
  await expect(map).toBeVisible()
  await expect(map.getByRole('button', { name: 'Galicia' })).toBeVisible()
  await expect(map.locator('.regionalCityMarker')).toHaveCount(4)
})

test('Decision Matrix summarizes numerical position without implying winners', async ({ page }) => {
  await page.goto('/compare?countries=ESP,PRT,IRL')

  const summary = page.getByRole('region', { name: 'Comparison summary' })
  await expect(summary).toBeVisible()
  await expect(summary.getByText('Spain')).toBeVisible()
  await expect(summary.getByText('Portugal')).toBeVisible()
  await expect(summary.getByText('Ireland')).toBeVisible()
  await expect(summary.getByText(/Higher\/lower describes numerical position only/i)).toBeVisible()
  await expect(page.getByText(/winner implied/i)).toHaveCount(0)
})

test('Decision Matrix exposes comparable evidence coverage by domain', async ({ page }) => {
  await page.goto('/compare?countries=ESP,PRT,IRL')

  const coverage = page.getByRole('region', { name: 'Domain evidence coverage' })
  await expect(coverage).toBeVisible()
  await expect(coverage.getByText('Comparable data by domain')).toBeVisible()
  await expect(coverage.locator('.decisionCoverageTrack')).toHaveCount(6)
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
  await expect(page.getByText('Eurostat 2026-Q2 · ISCO OC3 vacancy rate 3.4% · context only')).toBeVisible()
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

test('regional directory toggles without replacing the map', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  await expect(page.getByTestId('regional-map')).toBeVisible()
  await expect(page.locator('.regionalRegionList')).toHaveCount(0)

  await page.getByRole('button', { name: 'Regions' }).click()
  await expect(page.getByTestId('regional-map')).toBeVisible()
  await expect(page.locator('.regionalRegionList')).toBeVisible()

  await page.getByRole('button', { name: 'Map', exact: true }).click()
  await expect(page.locator('.regionalRegionList')).toHaveCount(0)
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

  await expect(page.getByText('MODELLED')).toBeVisible()
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

test('responsive shell avoids horizontal overflow across core views', async ({ page }) => {
  const cases = [
    { width: 1366, height: 768 },
    { width: 1024, height: 768 },
    { width: 390, height: 844 },
  ]

  for (const viewport of cases) {
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
  }
})



test('Skills and Languages replaces empty tables with evidence-aware onboarding', async ({ page }) => {
  await page.goto('/country/ESP/skills')

  const onboarding = page.getByRole('region', { name: 'Skills profile onboarding' })
  await expect(onboarding).toBeVisible()
  await expect(onboarding.getByText('Add your profession to unlock occupation-level evidence')).toBeVisible()
  await expect(onboarding.getByText('Profession', { exact: true })).toBeVisible()
  await expect(onboarding.getByText('Skills', { exact: true })).toBeVisible()
  await expect(onboarding.getByText('Languages', { exact: true })).toBeVisible()
  await expect(onboarding.getByText(/Cedefop occupation demand/i)).toBeVisible()
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
  await expect(coverage.getByText(/Cedefop CLSSI 2026/i)).toBeVisible()
  await expect(coverage.getByText(/Cedefop STAS/i)).toBeVisible()
  await expect(coverage.getByText(/Skills-OVATE detailed OJA evidence/i)).toBeVisible()

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

