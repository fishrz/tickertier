export interface PersonaPillProps {
  persona?: string | null
}

export function PersonaPill({ persona }: PersonaPillProps) {
  if (!persona) return null
  return (
    <span className="inline-block rounded-full bg-surface-2 text-muted text-[12px] px-2.5 py-1 zh">
      {persona}
    </span>
  )
}
