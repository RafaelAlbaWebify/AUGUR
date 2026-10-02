type FlagIconProps = {
  iso3: string
  className?: string
}

export default function FlagIcon({ iso3, className = '' }: FlagIconProps) {
  const common = {
    className: `flagIcon ${className}`.trim(),
    viewBox: '0 0 24 16',
    role: 'img' as const,
    'aria-label': `${iso3} flag`,
  }

  if (iso3 === 'ESP') {
    return (
      <svg {...common}>
        <rect width="24" height="16" rx="2" fill="#AA151B" />
        <rect y="4" width="24" height="8" fill="#F1BF00" />
      </svg>
    )
  }

  if (iso3 === 'PRT') {
    return (
      <svg {...common}>
        <rect width="9.5" height="16" rx="2" fill="#046A38" />
        <rect x="9.5" width="14.5" height="16" rx="2" fill="#DA291C" />
        <circle cx="9.5" cy="8" r="2.3" fill="#F5C242" />
      </svg>
    )
  }

  if (iso3 === 'IRL') {
    return (
      <svg {...common}>
        <rect width="8" height="16" rx="2" fill="#169B62" />
        <rect x="8" width="8" height="16" fill="#FFFFFF" />
        <rect x="16" width="8" height="16" rx="2" fill="#FF883E" />
      </svg>
    )
  }

  return (
    <svg {...common}>
      <rect width="24" height="16" rx="2" fill="#355064" />
    </svg>
  )
}
