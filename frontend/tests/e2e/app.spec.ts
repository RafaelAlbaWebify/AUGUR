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
  await page.route('http://127.0.0.1:8020/api/**', async route => {
    const url = new URL(route.request().url())
    const path = url.pathname
    const country = path.match(/\/countries\/(ESP|PRT|IRL)\//)?.[1] ?? 'ESP'
    let body: unknown

    if (path.endsWith('/ttv')) {
      body = {
        target_country_iso3: country,
        method: 'ttv_dependency_graph_v1',
        stage_order: ['legal_fit', 'language_fit', 'career_fit', 'financial_fit'],
        stages: {
          legal_fit: { ready: false, status: 'insufficient_profile', evidence_state: 'implemented' },
          language_fit: { ready: false, status: 'profile_inputs_missing', evidence_state: 'country_evidence_pending' },
          career_fit: { ready: false, status: 'profile_inputs_missing', evidence_state: 'country_evidence_pending' },
          financial_fit: { ready: false, status: 'insufficient_profile', evidence_state: 'partial' },
        },
        blocked_by: ['legal_fit', 'language_fit', 'career_fit', 'financial_fit'],
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
        status: 'local_income_unknown',
        reason: 'portable_income_not_confirmed',
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
          financial_fit: { label: 'FinancialFit', ready: false, completed_fields: 1, required_fields: 3, missing_fields: ['monthly_net_income', 'liquid_savings'] },
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
    } else if (path === '/api/countries') {
      body = { countries }
    } else if (path === '/api/compare') {
      body = {
        countries: countries.map(({ iso3, name }) => ({ iso3, name })),
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
    } else if (path.endsWith('/trends')) {
      body = { country_iso3: country, indicator_count: 1, indicators: [{ ...metric(country), interpretation_policy: 'lower', target_min: null, target_max: null, trend: { direction: 'decrease', interpretation: 'improving', confidence: 'high', slope_per_year: -0.2, pct_change_1y: -2, pct_change_3y: -5, pct_change_5y: -8, years_used: 6, target_status: null } }] }
    } else if (path.endsWith('/assessment')) {
      body = { country_iso3: country, method: 'test', dimensions: { productive_capacity: { trajectory: 'improving', confidence: 'high', indicator_count: 1, directional_indicator_count: 1, coverage: 1, improving_signals: [{ indicator_id: 'unemployment_rate', name: 'Unemployment', direction: 'decrease', confidence: 'high', pct_change_5y: -8 }], deteriorating_signals: [], stable_signals: [], contextual_signals: [] } } }
    } else if (path.endsWith('/source-quality')) {
      body = { country_iso3: country, indicators: [{ indicator_id: 'unemployment_rate', name: 'Unemployment', dimension: 'productive_capacity', unit: 'percent', source_count: 2, preferred_source_id: 'EUROSTAT', preferred_source_name: 'Eurostat', preferred_period: 2025, preferred_value: metric(country).value, freshest_period: 2025, period_spread: 0, common_period: 2025, common_period_source_count: 2, disagreement_pct: 0.5 }] }
    } else if (path.endsWith('/trajectory')) {
      body = { country_iso3: country, method: 'test', notes: [], horizons: [2030, 2035, 2045].map(year => ({ year, indicator_count: 0, sources: [], indicators: [] })) }
    } else if (path.endsWith('/scenarios')) {
      body = { country_iso3: country, method: 'test', horizons: [2030, 2035, 2045], scenario_names: ['baseline', 'improvement', 'stress'], indicators: [], notes: [] }
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

test('loads core analytical sections', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'AUGUR' })).toBeVisible()
  await expect(page.getByText('COUNTRY SIGNAL SUMMARY')).toBeVisible()
  await expect(page.getByText('OFFICIAL OUTLOOK')).toBeVisible()
  await expect(page.getByText('AUGUR SCENARIOS')).toBeVisible()
  await expect(page.getByText('COUNTRY COMPARISON')).toBeVisible()
})

test('switches country without a page reload', async ({ page }) => {
  const selector = page.getByLabel('Select country')
  await selector.selectOption('PRT')
  await expect(page.getByRole('heading', { name: 'Portugal', exact: true })).toBeVisible()
  await expect(page.locator('.metricValue').filter({ hasText: /^6\.4%$/ })).toBeVisible()

  await selector.selectOption('IRL')
  await expect(page.getByRole('heading', { name: 'Ireland', exact: true })).toBeVisible()
  await expect(page.locator('.metricValue').filter({ hasText: /^4\.5%$/ })).toBeVisible()
})

test('comparison remains neutral and aligned', async ({ page }) => {
  await expect(page.getByRole('columnheader', { name: 'Spain' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: 'Portugal' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: 'Ireland' })).toBeVisible()
  await expect(page.getByText('aligned indicators · no ranking')).toBeVisible()
})


test('world view renders country geometry and drives selection', async ({ page }) => {
  await expect(page.getByText('WORLD VIEW')).toBeVisible()

  const map = page.getByTestId('world-map')
  await expect(map).toBeVisible()

  const portugalShape = map.locator('[data-country="PRT"]')
  await expect(portugalShape).toHaveCount(1)
  await expect(portugalShape).toBeVisible()

  await portugalShape.click()

  await expect(page.getByRole('heading', { name: 'Portugal', exact: true })).toBeVisible()
  await expect(page.locator('.metricValue').filter({ hasText: /^6\.4%$/ })).toBeVisible()
})


test('personal profile remains separate and can be saved locally', async ({ page }) => {
  const profile = page.getByRole('region', { name: 'Personal profile' })
  await expect(profile.getByText('stored locally · never changes country facts')).toBeVisible()
  await expect(profile.getByText('Personal-fit readiness')).toBeVisible()
  await expect(profile.getByText('0/4 input sets ready')).toBeVisible()
  await expect(profile.getByText('LegalFit · ESP')).toBeVisible()
  await expect(profile.getByText('FinancialFit · ESP')).toBeVisible()
  await expect(profile.getByText('TTV dependency path · ESP')).toBeVisible()
  await expect(profile.getByText('time estimate intentionally blocked')).toBeVisible()

  await profile.getByLabel('Profession').fill('Systems engineer')
  await profile.getByLabel('Household size').fill('2')
  await profile.getByRole('button', { name: 'Save profile' }).click()

  await expect(profile.getByText('Saved locally')).toBeVisible()
})
