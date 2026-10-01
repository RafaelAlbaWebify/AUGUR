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

type ProfilePanelProps = {
  apiBase: string
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

export default function ProfilePanel({ apiBase }: ProfilePanelProps) {
  const [profile, setProfile] = useState<PersonalProfile>(EMPTY_PROFILE)
  const [citizenshipsText, setCitizenshipsText] = useState('')
  const [skillsText, setSkillsText] = useState('')
  const [languagesText, setLanguagesText] = useState('')
  const [status, setStatus] = useState<'loading' | 'ready' | 'saving' | 'saved' | 'error'>('loading')

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
      })
      .catch(() => setStatus('error'))
  }, [apiBase])

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
