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
            geometry: { type: 'Polygon', coordinates: [[[-9.3, 41.8], [-6.7, 41.8], [-6.7, 43.8], [-9.3, 43.8], [-9.3, 41.8]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'ES12', NAME_LATN: 'Principado de Asturias', NUTS_NAME: 'Principado de Asturias', CNTR_CODE: 'ES', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-7.2, 42.8], [-4.5, 42.8], [-4.5, 43.7], [-7.2, 43.7], [-7.2, 42.8]]] },
          },
          {
            type: 'Feature',
            properties: { NUTS_ID: 'PT11', NAME_LATN: 'Norte', NUTS_NAME: 'Norte', CNTR_CODE: 'PT', LEVL_CODE: 2 },
            geometry: { type: 'Polygon', coordinates: [[[-9, 40.8], [-6.2, 40.8], [-6.2, 42.2], [-9, 42.2], [-9, 40.8]]] },
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
        indicator_count: 1,
        method: 'aligned_current_observations_v1',
        notes: [],
        indicators: [{
          indicator_id: 'unemployment_rate',
          name: 'Unemployment',
          dimension: 'productive_capacity',
          unit: 'percent',
          countries: {
            ESP: { period: 2025, value: 10.4, source_id: 'EUROSTAT' },
            PRT: { period: 2025, value: 6.4, source_id: 'EUROSTAT' },
            IRL: { period: 2025, value: 4.5, source_id: 'EUROSTAT' },
          },
        }],
      }
    } else if (path.endsWith('/snapshot')) {
      body = { country_iso3: country, observation_count: 1, indicators: [metric(country)] }
    } else if (path.endsWith('/overview-series')) {
      body = {
        country_iso3: country,
        series: [{
          indicator_id: 'unemployment_rate',
          name: 'Unemployment, total (% of total labor force)',
          dimension: 'productive_capacity',
          unit: 'percent',
          source_id: 'EUROSTAT',
          points: [
            { period: 2018, value: country === 'ESP' ? 15.3 : country === 'PRT' ? 7.0 : 5.8 },
            { period: 2019, value: country === 'ESP' ? 14.1 : country === 'PRT' ? 6.6 : 5.0 },
            { period: 2020, value: country === 'ESP' ? 15.5 : country === 'PRT' ? 7.0 : 5.8 },
            { period: 2021, value: country === 'ESP' ? 14.8 : country === 'PRT' ? 6.6 : 6.2 },
            { period: 2022, value: country === 'ESP' ? 12.9 : country === 'PRT' ? 6.1 : 4.5 },
            { period: 2023, value: country === 'ESP' ? 12.2 : country === 'PRT' ? 6.5 : 4.3 },
            { period: 2024, value: country === 'ESP' ? 11.3 : country === 'PRT' ? 6.4 : 4.4 },
            { period: 2025, value: metric(country).value },
          ],
        }],
      }
    } else if (path.endsWith('/trends')) {
      body = { country_iso3: country, indicator_count: 1, indicators: [{ ...metric(country), interpretation_policy: 'lower', target_min: null, target_max: null, trend: { direction: 'decrease', interpretation: 'improving', confidence: 'high', slope_per_year: -0.2, pct_change_1y: -2, pct_change_3y: -5, pct_change_5y: -8, years_used: 6, target_status: null } }] }
    } else if (path.endsWith('/assessment')) {
      body = { country_iso3: country, method: 'test', dimensions: { productive_capacity: { trajectory: 'improving', confidence: 'high', indicator_count: 1, directional_indicator_count: 1, coverage: 1, improving_signals: [{ indicator_id: 'unemployment_rate', name: 'Unemployment', direction: 'decrease', confidence: 'high', pct_change_5y: -8 }], deteriorating_signals: [], stable_signals: [], contextual_signals: [] } } }
    } else if (path.endsWith('/source-quality')) {
      body = { country_iso3: country, indicators: [{ indicator_id: 'unemployment_rate', name: 'Unemployment', dimension: 'productive_capacity', unit: 'percent', source_count: 2, preferred_source_id: 'EUROSTAT', preferred_source_name: 'Eurostat', preferred_period: 2025, preferred_value: metric(country).value, freshest_period: 2025, period_spread: 0, common_period: 2025, common_period_source_count: 2, disagreement_pct: 0.5 }] }
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
  await expect(page.getByTestId('world-map')).toBeVisible()

  await page.getByRole('button', { name: 'Indicators' }).click()
  await expect(page).toHaveURL(/\/country\/ESP\/indicators$/)
  await expect(page.getByText('2. EVIDENCE EXPLORER / Indicators')).toBeVisible()

  await page.getByRole('button', { name: 'Outlook' }).click()
  await expect(page).toHaveURL(/\/country\/ESP\/outlook$/)
  await expect(page.getByText('3. FUTURE PATHS / Outlook')).toBeVisible()
  await expect(page.getByTestId('world-map')).toHaveCount(0)

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
  await expect(page.getByRole('button', { name: 'Galicia' })).toBeVisible()
  await page.getByRole('button', { name: 'Galicia' }).click()

  await expect(page.getByText('Galicia · ES11')).toBeVisible()
  await expect(page.getByText('Geography: Eurostat GISCO · NUTS 2024 · level 2 · EPSG:4326')).toBeVisible()

  await page.getByRole('button', { name: 'Map', exact: true }).click()
  await expect(page.getByTestId('world-map')).toBeVisible()

  await page.getByRole('button', { name: 'Regions' }).click()
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

test('world view renders country geometry and drives selection', async ({ page }) => {
  await expect(page.getByText('WORLD VIEW')).toBeVisible()

  const map = page.getByTestId('world-map')
  await expect(map).toBeVisible()

  const portugalShape = map.locator('[data-country="PRT"]')
  await expect(portugalShape).toHaveCount(1)
  await expect(portugalShape).toBeVisible()

  await portugalShape.click()

  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(page).toHaveURL(/\/country\/PRT\/overview$/)
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

test('map zoom controls change and reset the view', async ({ page }) => {
  const map = page.getByTestId('world-map')
  await expect(map).toBeVisible()

  const initialViewBox = await map.getAttribute('viewBox')

  await page.getByRole('button', { name: 'Zoom in' }).click()
  await expect.poll(async () => map.getAttribute('viewBox')).not.toBe(initialViewBox)

  await page.getByRole('button', { name: 'Reset map' }).click()
  await expect(map).toHaveAttribute('viewBox', initialViewBox ?? '0 0 1000 500')
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
  await expect(page.getByTestId('world-map')).toBeVisible()
  await expect(page.getByText('1. COUNTRY RADAR / Overview')).toBeVisible()
  await expect(page.getByText('Latest one-year movements')).toBeVisible()
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

  await expect(page.locator('.worldMapLegend .flagIcon')).toHaveCount(3)
  await expect(page.locator('.topbarCountry .flagIcon')).toHaveCount(1)
  await expect(page.locator('.countryIdentityCard')).toBeVisible()
  await expect(page.locator('.countryMetricCard')).toHaveCount(10)
  await expect(page.getByText('No single composite score.')).toBeVisible()
})

test('Future Paths distinguishes official baseline from AUGUR model scenarios', async ({ page }) => {
  await page.goto('/country/ESP/outlook')

  await expect(page.getByText('OFFICIAL FORECAST', { exact: true })).toBeVisible()
  await expect(page.getByText('AUGUR MODEL SCENARIOS', { exact: true })).toBeVisible()
  await expect(page.getByText('not official forecasts', { exact: true })).toBeVisible()
  await expect(page.locator('.officialLine')).toBeVisible()
  await expect(page.locator('.scenarioLine.improvement')).toBeVisible()
  await expect(page.locator('.scenarioLine.stress')).toBeVisible()
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

    await expect(page.getByTestId('world-map')).toBeVisible()
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

