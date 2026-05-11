import { useState } from 'react'

interface ShareButtonProps {
  title: string
  text: string
  url: string
  /** Optional: smaller variant for inline placement */
  size?: 'sm' | 'md'
  className?: string
}

/**
 * One-click share with Web Share API (mobile) + clipboard fallback (desktop).
 * Shows a transient toast after action.
 */
export function ShareButton({ title, text, url, size = 'md', className = '' }: ShareButtonProps) {
  const [toast, setToast] = useState<string | null>(null)

  const flash = (msg: string) => {
    setToast(msg)
    window.setTimeout(() => setToast(null), 1800)
  }

  const onClick = async () => {
    const fullText = `${text}\n${url}`
    try {
      // Prefer Web Share API when available (mobile + Safari/Chrome supports it)
      const nav = navigator as Navigator & { share?: (d: ShareData) => Promise<void> }
      if (nav.share) {
        await nav.share({ title, text, url })
        return
      }
      // Fallback: clipboard
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(fullText)
        flash('已复制到剪贴板')
        return
      }
      // Last-resort fallback
      const ta = document.createElement('textarea')
      ta.value = fullText
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      flash('已复制到剪贴板')
    } catch (err) {
      // User cancelled or denied — suppress noise
      const e = err as Error
      if (e?.name !== 'AbortError') {
        flash('分享失败')
      }
    }
  }

  const base =
    size === 'sm'
      ? 'px-2.5 py-1 text-[11px]'
      : 'px-4 py-2 text-[13px]'

  return (
    <div className={`relative inline-flex ${className}`}>
      <button
        type="button"
        onClick={onClick}
        className={`${base} font-mono font-bold uppercase tracking-[0.1em] border border-ink bg-paper hover:bg-ink hover:text-paper transition-colors`}
        title="分享 / 复制链接"
      >
        ↗ 分享
      </button>
      {toast && (
        <span
          className="absolute left-full top-1/2 -translate-y-1/2 ml-3 whitespace-nowrap font-mono text-[11px] text-pos pointer-events-none"
          role="status"
        >
          {toast}
        </span>
      )}
    </div>
  )
}
