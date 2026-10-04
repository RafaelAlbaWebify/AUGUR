import { useEffect, useMemo, useState } from 'react'

type SkillsLanguagesPageProps = {
  apiBase: string
  targetCountry: string
  countryName: string
}

type Profile = {
  profession?: string | null
  skills?: string[]
  languages?: Array<{ language?: string; name?: string; cefr?: string; level?: string }>
}

type CareerFit = {
  status?: string
  market_signal?: string | null
  market_signal_scope?: string
  market_signal_isco?: string | null
  occupation_match?: {
    selected?: {
      preferred_label?: string
      match_score?: number
      isco_group?: string
      code?: string
    } | null
  }
  vacancy_demand_evidence?: {
    status?: string
    vacancy_rate_pct?: number
    period?: string
    source_id?: string
    granularity?: string
    isco_major?: string
  } | null
  skill_match?: {
    dataset_mode?: string | null
    dataset_version?: string | null
    occupation_label?: string | null
    matched_skills?: Array<string | { label?: string; skill?: string; name?: string }>
    missing_skills?: Array<string | { label?: string; skill?: string; name?: string }>
    coverage?: number | null
    evidence_complete?: boolean
  }
  source?: {
    label?: string
    evidence_id?: string
    rule_version?: string
    report_year?: number
    conditions_year?: number
    scope?: string
  } | null
}

type LanguageFit = {
  status?: string
  target_languages?: string[]
  matches?: Array<{
    language: string
    declared_cefr?: string | null
    meets_work_ready_heuristic?: boolean
  }>
  work_ready_threshold?: string
  work_ready?: boolean
  occupation_language_evidence?: {
    status?: string
    occupation_label?: string
    essential_skill_count?: number
    optional_skill_count?: number
  } | null
}

function skillLabel(value: string | { label?: string; skill?: string; name?: string }) {
  if (typeof value === 'string') return value
  return value.label ?? value.skill ?? value.name ?? 'Unnamed skill'
}

function languageLevel(profile: Profile | null, language: string) {
  const match = (profile?.languages ?? []).find((item) => {
    const name = item.language ?? item.name
    return name?.toLowerCase() === language.toLowerCase()
  })
  return match?.cefr ?? match?.level ?? 'Not set'
}

export default function SkillsLanguagesPage({
  apiBase,
  targetCountry,
  countryName,
}: SkillsLanguagesPageProps) {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [career, setCareer] = useState<CareerFit | null>(null)
  const [language, setLanguage] = useState<LanguageFit | null>(null)
  const [tab, setTab] = useState<'demand' | 'rising' | 'gaps' | 'portable' | 'languages'>('demand')

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal

    Promise.all([
      fetch(`${apiBase}/api/profile`, { signal }).then((r) => r.ok ? r.json() : null),
      fetch(`${apiBase}/api/countries/${targetCountry}/career-fit`, { signal }).then((r) => r.ok ? r.json() : null),
      fetch(`${apiBase}/api/countries/${targetCountry}/language-fit`, { signal }).then((r) => r.ok ? r.json() : null),
    ]).then(([profileData, careerData, languageData]) => {
      if (signal.aborted) return
      setProfile(profileData)
      setCareer(careerData)
      setLanguage(languageData)
    }).catch(() => undefined)

    return () => controller.abort()
  }, [apiBase, targetCountry])

  const matched = useMemo(
    () => (career?.skill_match?.matched_skills ?? []).map(skillLabel),
    [career],
  )
  const missing = useMemo(
    () => (career?.skill_match?.missing_skills ?? []).map(skillLabel),
    [career],
  )

  const visibleSkills = tab === 'gaps'
    ? missing
    : tab === 'portable'
    ? [...new Set([...(profile?.skills ?? []), ...matched])].slice(0, 20)
    : tab === 'demand'
    ? [...new Set([...(profile?.skills ?? []), ...matched, ...missing])].slice(0, 20)
    : []

  const demandEvidenceAvailable = career?.vacancy_demand_evidence?.status === 'available'
  const liveSkillDemandAvailable = false
  const profileReadyForSkills = Boolean(
    (profile?.profession && profile.profession.trim()) ||
    career?.occupation_match?.selected?.preferred_label,
  )
  const hasDeclaredSkills = Boolean(profile?.skills?.length)
  const hasLanguages = Boolean(profile?.languages?.length)
  const profileGaps = [
    !profileReadyForSkills ? 'profession' : null,
    !hasDeclaredSkills ? 'skills' : null,
    !hasLanguages ? 'languages' : null,
  ].filter((item): item is string => Boolean(item))

  return (
    <section className="skillsLanguagesPage" aria-label="Skills and languages">
      <div className="productPageHeader">
        <div>
          <span>6. SKILLS & LANGUAGES</span>
          <h2>Demand, trends and your match</h2>
        </div>
        <p>What to learn, what transfers, and what the evidence can currently support.</p>
      </div>

      <section className="skillsControlBar">
        <label>
          <span>Target occupation</span>
          <strong>{career?.occupation_match?.selected?.preferred_label ?? profile?.profession ?? 'Add profession in Profile'}</strong>
        </label>
        <label>
          <span>Country / region</span>
          <strong>{countryName} · national</strong>
        </label>
        <label>
          <span>Time horizon</span>
          <strong>Current evidence</strong>
        </label>
        <div className="evidenceModeBadge">OFFICIAL / VERIFIED EVIDENCE ONLY</div>
      </section>

      <div className="skillsLanguagesGrid">
        <section className="skillsDemandPanel">
          {!profileReadyForSkills ? (
            <section className="skillsOnboardingState" aria-label="Skills profile onboarding">
              <div className="skillsOnboardingHero">
                <span>PROFILE INPUT REQUIRED</span>
                <h3>Add your profession to unlock occupation-level evidence</h3>
                <p>
                  AUGUR needs a target occupation before it can match ESCO skills, interpret shortage/surplus evidence,
                  or connect future occupational demand. No skill-demand percentages are inferred from an empty profile.
                </p>
              </div>

              <div className="skillsUnlockGrid">
                <article>
                  <span>1</span>
                  <div><strong>Profession</strong><small>Resolves an ESCO / ISCO occupation.</small></div>
                  <b>{profileReadyForSkills ? 'ready' : 'required'}</b>
                </article>
                <article>
                  <span>2</span>
                  <div><strong>Skills</strong><small>Separates matched skills from gaps.</small></div>
                  <b>{hasDeclaredSkills ? 'ready' : 'recommended'}</b>
                </article>
                <article>
                  <span>3</span>
                  <div><strong>Languages</strong><small>Enables CEFR and occupation-language checks.</small></div>
                  <b>{hasLanguages ? 'ready' : 'recommended'}</b>
                </article>
              </div>

              <div className="skillsUnlockEvidence">
                <div>
                  <span>AVAILABLE NOW</span>
                  <strong>Country vacancy context</strong>
                  <small>{demandEvidenceAvailable ? `${career?.vacancy_demand_evidence?.vacancy_rate_pct?.toFixed(1)}% · ${career?.vacancy_demand_evidence?.period}` : 'No verified vacancy context loaded'}</small>
                </div>
                <div>
                  <span>UNLOCKS NEXT</span>
                  <strong>ESCO occupation + skill matching</strong>
                  <small>Official taxonomy evidence, not employer-demand frequency.</small>
                </div>
                <div>
                  <span>FUTURE DATA LAYER</span>
                  <strong>Cedefop occupation demand</strong>
                  <small>Public OJA shortage + short-term forecast datasets are the next ingestion target.</small>
                </div>
              </div>

              <p className="skillsOnboardingFooter">
                Missing profile fields: {profileGaps.join(', ') || 'none'} · Edit them in My Fit / Profile.
              </p>
            </section>
          ) : (
            <>
              <div className="segmentedTabs" role="tablist" aria-label="Skills views">
                {[
                  ['demand', 'Skills in demand'],
                  ['rising', 'Rising skills'],
                  ['gaps', 'My gaps'],
                  ['portable', 'Portable skills'],
                  ['languages', 'Job-ad language demand'],
                ].map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    className={tab === id ? 'active' : ''}
                    onClick={() => setTab(id as typeof tab)}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {tab === 'rising' ? (
                <div className="evidenceUnavailable">
                  <strong>Rising-skill trends are not available yet.</strong>
                  <span>AUGUR needs time-series job-posting evidence such as Cedefop Skills-OVATE before it can calculate demand growth honestly.</span>
                </div>
              ) : tab === 'languages' ? (
                <div className="evidenceUnavailable">
                  <strong>Job-posting language demand is not available yet.</strong>
                  <span>Current LanguageFit uses declared CEFR, target-country labour-market language and ESCO occupation-language evidence; it does not yet count language requirements in live postings.</span>
                </div>
              ) : (
                <div className="skillsTableWrap">
                  <table className="skillsDemandTable">
                    <thead><tr><th>Skill</th><th>Demand</th><th>Trend</th><th>Evidence</th><th>Your profile</th><th>Match</th></tr></thead>
                    <tbody>
                      {visibleSkills.map((skill) => {
                        const declared = (profile?.skills ?? []).some((item) => item.toLowerCase() === skill.toLowerCase())
                        const essentialMatch = matched.some((item) => item.toLowerCase() === skill.toLowerCase())
                        const gap = missing.some((item) => item.toLowerCase() === skill.toLowerCase())
                        return (
                          <tr key={skill}>
                            <td><strong>{skill}</strong></td>
                            <td>{liveSkillDemandAvailable ? 'Available' : 'Not yet measured'}</td>
                            <td>—</td>
                            <td>{essentialMatch || gap ? 'ESCO occupation evidence' : 'Declared profile skill'}</td>
                            <td>{declared ? 'Declared' : 'Not declared'}</td>
                            <td><span className={essentialMatch ? 'evidenceChip good' : gap ? 'evidenceChip warn' : 'evidenceChip neutral'}>{essentialMatch ? 'Matched' : gap ? 'Gap' : 'Context'}</span></td>
                          </tr>
                        )
                      })}
                      {visibleSkills.length === 0 && <tr><td colSpan={6}>No skill evidence available for this view.</td></tr>}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="skillsEvidenceFooter">
                <div><span>Occupation market signal</span><strong>{career?.market_signal?.replaceAll('_', ' ') ?? 'Unavailable'}</strong></div>
                <div><span>Vacancy context</span><strong>{demandEvidenceAvailable ? `${career?.vacancy_demand_evidence?.vacancy_rate_pct?.toFixed(1)}% · ${career?.vacancy_demand_evidence?.period}` : 'Unavailable'}</strong></div>
                <div><span>Skill coverage</span><strong>{career?.skill_match?.coverage == null ? 'Unavailable' : `${Math.round(career.skill_match.coverage * 100)}% essential skills`}</strong></div>
              </div>

              <section className="demandEvidenceCoverage" aria-label="Demand evidence coverage">
                <div className="panelHeading">
                  <div>
                    <span>DEMAND EVIDENCE COVERAGE</span>
                    <h3>What is measured vs. still pending</h3>
                  </div>
                </div>
                <div className="demandCoverageGrid">
                  <article className="active">
                    <span>ACTIVE</span>
                    <strong>Current shortage / surplus</strong>
                    <small>EURES / ELA occupation evidence</small>
                  </article>
                  <article className="active">
                    <span>ACTIVE</span>
                    <strong>Vacancy context</strong>
                    <small>Eurostat experimental JVR by occupation group</small>
                  </article>
                  <article className="active">
                    <span>ACTIVE</span>
                    <strong>Occupation-skill relationships</strong>
                    <small>ESCO taxonomy · not demand frequency</small>
                  </article>
                  <article className="planned">
                    <span>PLANNED</span>
                    <strong>Future shortage pressure</strong>
                    <small>Cedefop CLSSI 2026 · country / occupation to 2035</small>
                  </article>
                  <article className="planned">
                    <span>PLANNED</span>
                    <strong>Short-term occupation outlook</strong>
                    <small>Cedefop STAS · twice-yearly employment projection</small>
                  </article>
                  <article className="restricted">
                    <span>ACCESS NEEDED</span>
                    <strong>Skill demand shares / trends</strong>
                    <small>Cedefop Skills-OVATE detailed OJA evidence</small>
                  </article>
                </div>
              </section>
            </>
          )}
        </section>
        <aside className="languageDemandPanel">
          <section>
            <div className="panelHeading">
              <div>
                <span>LANGUAGE FIT</span>
                <h3>Declared + target evidence</h3>
              </div>
            </div>

            <div className="languageEvidenceTable">
              {(language?.matches ?? []).map((item) => (
                <div key={item.language}>
                  <strong>{item.language}</strong>
                  <span>{item.meets_work_ready_heuristic ? 'Meets AUGUR work-ready heuristic' : 'Gap / evidence incomplete'}</span>
                  <small>Your level: {item.declared_cefr ?? languageLevel(profile, item.language)}</small>
                </div>
              ))}
              {(language?.matches ?? []).length === 0 && (
                <div><span>No target-language evidence available.</span></div>
              )}
            </div>
          </section>

          <section className="learningEffortPanel">
            <div className="panelHeading">
              <div>
                <span>LEARNING EFFORT</span>
                <h3>Estimate status</h3>
              </div>
            </div>
            <p>
              CEFR learning-time estimates live in TTV and require a declared current level plus weekly study hours.
              This page does not invent hours when those inputs are missing.
            </p>
          </section>

          <section className="skillsInsightPanel">
            <div className="panelHeading">
              <div>
                <span>INSIGHTS</span>
                <h3>What AUGUR can say now</h3>
              </div>
            </div>
            <ul>
              <li>Occupation: {career?.occupation_match?.selected?.preferred_label ?? 'not confidently resolved'}.</li>
              <li>Market signal: {career?.market_signal?.replaceAll('_', ' ') ?? 'not available'}{career?.market_signal_isco ? ` · ISCO ${career.market_signal_isco}` : ''}.</li>
              <li>Market evidence: {career?.source?.label ?? 'not available'}{career?.source?.conditions_year ? ` · ${career.source.conditions_year} conditions` : ''}{career?.source?.evidence_id ? ` · ${career.source.evidence_id}` : ''}.</li>
              <li>Vacancy context: {career?.vacancy_demand_evidence?.status === 'available' ? `Eurostat ${career.vacancy_demand_evidence.period} · ISCO ${career.vacancy_demand_evidence.isco_major ?? career.vacancy_demand_evidence.granularity ?? 'group'} vacancy rate ${career.vacancy_demand_evidence.vacancy_rate_pct?.toFixed(1)}% · context only` : 'not available'}.</li>
              <li>Skill evidence: {career?.skill_match?.dataset_version ?? career?.skill_match?.dataset_mode ?? 'not available'}.</li>
              <li>Live skill demand, employer counts and rising-skill trends are intentionally withheld until a job-posting evidence source is integrated.</li>
            </ul>
          </section>
        </aside>
      </div>
    </section>
  )
}
