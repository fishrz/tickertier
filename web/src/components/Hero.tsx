// Hero block — magazine-style giant headline + side stats
interface HeroProps {
  title: React.ReactNode
  emphasis?: string  // legacy: italic gold-dim word inside string title
  subtitle?: string
  bigStat?: string | number
  bigStatLabel?: string
  bottomLine?: React.ReactNode
}

export function Hero({ title, emphasis, subtitle, bigStat, bigStatLabel, bottomLine }: HeroProps) {
  // If title is a string AND emphasis given, split it; else render as-is (ReactNode)
  const renderTitle = () => {
    if (typeof title !== 'string' || !emphasis || !title.includes(emphasis)) {
      return title
    }
    const [before, after] = title.split(emphasis)
    return (
      <>
        {before}
        <em className="not-italic font-bold text-gold-dim italic">{emphasis}</em>
        {after}
      </>
    )
  }

  return (
    <section className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-12 items-end py-16 border-b border-ink">
      <h1 className="font-serif font-black tracking-[-0.04em] leading-[0.92] text-[clamp(64px,9vw,128px)]">
        {renderTitle()}
      </h1>
      {(bigStat !== undefined || bottomLine) && (
        <div className="text-right md:text-right text-mute font-mono text-[12px] uppercase tracking-[0.1em] leading-relaxed">
          {bigStat !== undefined && (
            <>
              <div className="font-serif text-[56px] text-ink font-black leading-none mb-2 tracking-[-0.02em]">
                {bigStat}
              </div>
              {bigStatLabel && <div>{bigStatLabel}</div>}
            </>
          )}
          {subtitle && <div className="mt-2">{subtitle}</div>}
          {bottomLine && <div className="mt-3">{bottomLine}</div>}
        </div>
      )}
    </section>
  )
}
