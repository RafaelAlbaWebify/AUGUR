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

    if (path === '/api/health') {
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


test('world view drives country selection without reload', async ({ page }) => {
  await expect(page.getByText('WORLD VIEW')).toBeVisible()
  await expect(page.getByTestId('world-map')).toBeVisible()

  const worldView = page.getByRole('region', { name: 'World country map' })
  await worldView.getByRole('button', { name: 'Portugal' }).click()

  await expect(page.getByRole('heading', { name: 'Portugal', exact: true })).toBeVisible()
  await expect(page.locator('.metricValue').filter({ hasText: /^6\.4%$/ })).toBeVisible()
})
