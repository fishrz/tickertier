import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        'surface-2': 'var(--surface-2)',
        border: 'var(--border)',
        text: 'var(--text)',
        muted: 'var(--muted)',
        gold: 'var(--gold)',
        'gold-soft': 'var(--gold-soft)',
        'tier-fire': 'var(--tier-fire)',
        'tier-crown': 'var(--tier-crown)',
        'tier-jade': 'var(--tier-jade)',
        'tier-npc': 'var(--tier-npc)',
        'tier-poop': 'var(--tier-poop)',
        'tier-skull': 'var(--tier-skull)',
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans SC', 'system-ui', 'sans-serif'],
        zh: ['"Noto Sans SC"', 'Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      maxWidth: {
        page: '1280px',
      },
    },
  },
  plugins: [],
} satisfies Config
