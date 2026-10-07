import FlagIcon from './FlagIcon'

type Country = {
  iso2?: string
  iso3: string
  name: string
}

type CountrySelectProps = {
  countries: Country[]
  value: string
  onChange: (iso3: string) => void
  ariaLabel: string
  compact?: boolean
}

export default function CountrySelect({
  countries,
  value,
  onChange,
  ariaLabel,
  compact = false,
}: CountrySelectProps) {
  const selected = countries.find((country) => country.iso3 === value)

  return (
    <label className={compact ? 'countryPicker compact' : 'countryPicker'}>
      <FlagIcon iso3={value} iso2={selected?.iso2} />
      <select
        value={value}
        aria-label={ariaLabel}
        onChange={(event) => onChange(event.target.value)}
      >
        {countries.map((country) => (
          <option value={country.iso3} key={country.iso3}>
            {country.name}
          </option>
        ))}
      </select>
      <span className="countryPickerChevron">⌄</span>
    </label>
  )
}
