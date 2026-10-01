import { useEffect, useState } from 'react'

type LanguageSkill = {
  language: string
  cefr: string | null
}

type PersonalProfile = {
  profile_id?: string
  age: number | null
  current_country: string | null
  citizenships: string[]
  profession: string | null
  skills: string[]
  languages: LanguageSkill[]
  household_size: number
  monthly_net_income: number | null
  liquid_savings: number | null
  remote_work: boolean
  preferences: Record<string, string | number | boolean>
  updated_at?: string | null
}

type ReadinessModule = {
  label: string
  ready: boolean
  completed_fields: number
  required_fields: number
  missing_fields: string[]
}

type ReadinessResponse = {
  profile_id: string
  modules: Record<string, ReadinessModule>
  ready_module_count: number
  module_count: number
  notes: string[]
}

type LegalFitResponse = {
  target_country_iso3: string
  status: string
  framework: string | null
  work_permit_required: boolean | null
  basis_citizenships?: string[]
  short_stay: null | {
    up_to_months: number
    residence_registration_generally_required: boolean
    presence_reporting_may_apply: boolean
  }
  long_stay: null | {
    registration_may_be_required: boolean
    conditions_depend_on_status: boolean
    statuses: string[]
  }
  rule_version: string
  notes: string[]
}

type FinancialFitResponse = {
  target_country_iso3: string
  status: string
  reason: string | null
  portable_income_analysis: null | {
    origin_country_iso3: string
    monthly_net_income: number
    origin_price_level_index: number
    origin_period: number
    target_price_level_index: number
    target_period: number
    relative_cost_factor: number
    origin_equivalent_purchasing_power: number
    purchasing_power_change_pct: number
    source_id: string
  }
  notes: string[]
}

type ProfilePanelProps = {
  apiBase: string
  targetCountry: string
}

const EMPTY_PROFILE: PersonalProfile = {
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
}

function parseList(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function parseLanguages(value: string): LanguageSkill[] {
  return parseList(value).map((item) => {
    const [language, cefr] = item.split(':').map((part) => part.trim())
    return {
      language,
      cefr: cefr || null,
    }
  })
}

function formatLanguages(languages: LanguageSkill[]) {
  return languages
    .map((item) => item.cefr ? `${item.language}:${item.cefr}` : item.language)
    .join(', ')
}

export default function ProfilePanel({ apiBase, targetCountry }: ProfilePanelProps) {
  const [profile, setProfile] = useState<PersonalProfile>(EMPTY_PROFILE)
  const [citizenshipsText, setCitizenshipsText] = useState('')
  const [skillsText, setSkillsText] = useState('')
  const [languagesText, setLanguagesText] = useState('')
  const [status, setStatus] = useState<'loading' | 'ready' | 'saving' | 'saved' | 'error'>('loading')
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null)
  const [financialFit, setFinancialFit] = useState<FinancialFitResponse | null>(null)
  const [legalFit, setLegalFit] = useState<LegalFitResponse | null>(null)

  async function refreshLegalFit() {
    try {
      const response = await fetch(`${apiBase}/api/countries/${targetCountry}/legal-fit`)
      if (!response.ok) return
      setLegalFit(await response.json())
    } catch {
      // Profile editing remains usable if LegalFit cannot be loaded.
    }
  }

  async function refreshFinancialFit() {
    try {
      const response = await fetch(`${apiBase}/api/countries/${targetCountry}/financial-fit`)
      if (!response.ok) return
      setFinancialFit(await response.json())
    } catch {
      // Profile editing remains usable if FinancialFit cannot be loaded.
    }
  }

  async function refreshReadiness() {
    try {
      const response = await fetch(`${apiBase}/api/profile/readiness`)
      if (!response.ok) return
      setReadiness(await response.json())
    } catch {
      // Profile editing remains usable if readiness cannot be loaded.
    }
  }

  useEffect(() => {
    fetch(`${apiBase}/api/profile`)
      .then(async (response) => {
        if (!response.ok) throw new Error(`Profile HTTP ${response.status}`)
        return response.json()
      })
      .then((data: PersonalProfile) => {
        setProfile(data)
        setCitizenshipsText(data.citizenships.join(', '))
        setSkillsText(data.skills.join(', '))
        setLanguagesText(formatLanguages(data.languages))
        setStatus('ready')
        void refreshReadiness()
        void refreshLegalFit()
        void refreshFinancialFit()
      })
      .catch(() => setStatus('error'))
  }, [apiBase, targetCountry])

  async function save() {
    setStatus('saving')

    const payload = {
      ...profile,
      current_country: profile.current_country?.trim().toUpperCase() || null,
      citizenships: parseList(citizenshipsText).map((item) => item.toUpperCase()),
      skills: parseList(skillsText),
      languages: parseLanguages(languagesText),
    }

    delete payload.profile_id
    delete payload.updated_at

    try {
      const response = await fetch(`${apiBase}/api/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) throw new Error(`Profile HTTP ${response.status}`)

      const saved = await response.json() as PersonalProfile
      setProfile(saved)
      setStatus('saved')
      await refreshReadiness()
      await refreshLegalFit()
      await refreshFinancialFit()
    } catch {
      setStatus('error')
    }
  }

  return (
    <section className="profileSection" aria-label="Personal profile">
      <div className="dimensionHeader">
        <div>
          <div className="label">PERSONAL PROFILE</div>
          <h3>Inputs for future personal-fit analysis</h3>
        </div>
        <span>stored locally · never changes country facts</span>
      </div>

      <div className="profileCard">
        <div className="profileGrid">
          <label>
            <span>Age</span>
            <input
              type="number"
              min={16}
              max={100}
              value={profile.age ?? ''}
              onChange={(event) => setProfile({
                ...profile,
                age: event.target.value ? Number(event.target.value) : null,
              })}
            />
          </label>

          <label>
            <span>Current country (ISO3)</span>
            <input
              maxLength={3}
              value={profile.current_country ?? ''}
              placeholder="ESP"
              onChange={(event) => setProfile({
                ...profile,
                current_country: event.target.value,
              })}
            />
          </label>

          <label>
            <span>Citizenships</span>
            <input
              value={citizenshipsText}
              placeholder="ESP, IRL"
              onChange={(event) => setCitizenshipsText(event.target.value)}
            />
          </label>

          <label>
            <span>Profession</span>
            <input
              value={profile.profession ?? ''}
              placeholder="Systems engineer"
              onChange={(event) => setProfile({
                ...profile,
                profession: event.target.value || null,
              })}
            />
          </label>

          <label className="profileWide">
            <span>Skills</span>
            <input
              value={skillsText}
              placeholder="Windows, Azure, Python, SQL"
              onChange={(event) => setSkillsText(event.target.value)}
            />
          </label>

          <label className="profileWide">
            <span>Languages · optional CEFR</span>
            <input
              value={languagesText}
              placeholder="Spanish:C2, English:B2"
              onChange={(event) => setLanguagesText(event.target.value)}
            />
          </label>

          <label>
            <span>Household size</span>
            <input
              type="number"
              min={1}
              max={20}
              value={profile.household_size}
              onChange={(event) => setProfile({
                ...profile,
                household_size: Number(event.target.value) || 1,
              })}
            />
          </label>

          <label>
            <span>Monthly net income</span>
            <input
              type="number"
              min={0}
              value={profile.monthly_net_income ?? ''}
              onChange={(event) => setProfile({
                ...profile,
                monthly_net_income: event.target.value ? Number(event.target.value) : null,
              })}
            />
          </label>

          <label>
            <span>Liquid savings</span>
            <input
              type="number"
              min={0}
              value={profile.liquid_savings ?? ''}
              onChange={(event) => setProfile({
                ...profile,
                liquid_savings: event.target.value ? Number(event.target.value) : null,
              })}
            />
          </label>

          <label className="profileCheckbox">
            <input
              type="checkbox"
              checked={profile.remote_work}
              onChange={(event) => setProfile({
                ...profile,
                remote_work: event.target.checked,
              })}
            />
            <span>Remote work is viable</span>
          </label>
        </div>

        <div className="profileReadiness">
          <div className="profileReadinessHeader">
            <strong>Personal-fit readiness</strong>
            <span>
              {readiness
                ? `${readiness.ready_module_count}/${readiness.module_count} input sets ready`
                : 'checking inputs…'}
            </span>
          </div>

          <div className="profileReadinessGrid">
            {Object.entries(readiness?.modules ?? {}).map(([moduleId, item]) => (
              <div className={item.ready ? 'ready' : ''} key={moduleId}>
                <strong>{item.label}</strong>
                <span>
                  {item.ready
                    ? 'Profile inputs present'
                    : `Missing: ${item.missing_fields.join(', ')}`}
                </span>
              </div>
            ))}
          </div>

          <p>
            Readiness only confirms that profile inputs exist. Country-fit evidence
            will be calculated separately.
          </p>
        </div>

        <div className="financialFitCard">
          <div className="profileReadinessHeader">
            <strong>LegalFit · {targetCountry}</strong>
            <span>{legalFit?.status?.replaceAll('_', ' ') ?? 'loading…'}</span>
          </div>

          {legalFit?.status === 'eu_free_movement_framework' ? (
            <div className="financialFitMetrics">
              <div>
                <span>Work permit</span>
                <strong>Not required</strong>
              </div>
              <div>
                <span>Short stay</span>
                <strong>Up to {legalFit.short_stay?.up_to_months ?? 3} months</strong>
              </div>
              <div>
                <span>Long stay</span>
                <strong>Registration may apply</strong>
              </div>
            </div>
          ) : (
            <p className="financialFitMessage">
              {legalFit?.status === 'domestic'
                ? 'Domestic case: cross-border EU free-movement logic is not needed.'
                : legalFit?.status === 'country_specific_rules_required'
                ? 'Country-specific immigration rules still need verified implementation for this citizenship.'
                : 'Complete current country and citizenships to evaluate the legal framework.'}
            </p>
          )}

          <p>
            Legal framework only. Long-stay conditions and national registration formalities still apply.
          </p>
        </div>

        <div className="financialFitCard">
          <div className="profileReadinessHeader">
            <strong>FinancialFit · {targetCountry}</strong>
            <span>{financialFit?.status?.replaceAll('_', ' ') ?? 'loading…'}</span>
          </div>

          {financialFit?.portable_income_analysis ? (
            <div className="financialFitMetrics">
              <div>
                <span>Relative cost factor</span>
                <strong>×{financialFit.portable_income_analysis.relative_cost_factor.toFixed(2)}</strong>
              </div>
              <div>
                <span>Purchasing-power change</span>
                <strong>
                  {financialFit.portable_income_analysis.purchasing_power_change_pct > 0 ? '+' : ''}
                  {financialFit.portable_income_analysis.purchasing_power_change_pct.toFixed(1)}%
                </strong>
              </div>
              <div>
                <span>Origin-equivalent income</span>
                <strong>
                  {new Intl.NumberFormat('en-US', {
                    maximumFractionDigits: 0,
                  }).format(financialFit.portable_income_analysis.origin_equivalent_purchasing_power)}
                </strong>
              </div>
            </div>
          ) : (
            <p className="financialFitMessage">
              {financialFit?.status === 'local_income_unknown'
                ? 'Current income is not assumed portable. Local salary evidence is required.'
                : financialFit?.status === 'insufficient_country_evidence'
                ? 'Country price-level evidence is not loaded yet.'
                : 'Complete the required financial profile inputs to compare purchasing power.'}
            </p>
          )}

          <p>
            Relative purchasing power only. This is not a household budget or country score.
          </p>
        </div>

        <div className="profileActions">
          <span>
            {status === 'loading' && 'Loading local profile…'}
            {status === 'saving' && 'Saving…'}
            {status === 'saved' && 'Saved locally'}
            {status === 'error' && 'Profile could not be loaded or saved'}
            {status === 'ready' && (profile.updated_at ? 'Local profile loaded' : 'No profile saved yet')}
          </span>
          <button type="button" onClick={save} disabled={status === 'loading' || status === 'saving'}>
            Save profile
          </button>
        </div>
      </div>
    </section>
  )
}
