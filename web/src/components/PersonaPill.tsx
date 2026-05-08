interface Props {
  persona?: string | null
  className?: string
}

// Persona = "人物画像"分类（如：稳健白马 / 妖股 / 财报敏感型...）
export function PersonaPill({ persona, className = '' }: Props) {
  if (!persona) return null
  return (
    <span
      className={`inline-flex items-center font-mono text-[11px] uppercase tracking-[0.15em] py-[3px] px-2.5 border border-gold-dim text-gold-dim bg-paper ${className}`}
    >
      <span className="mr-1.5 text-[8px]">●</span>
      {persona}
    </span>
  )
}
