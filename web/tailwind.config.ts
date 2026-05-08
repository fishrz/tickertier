import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: 'var(--ink)',
        paper: 'var(--paper)',
        'paper-2': 'var(--paper-2)',
        rule: 'var(--rule)',
        mute: 'var(--mute)',
        gold: 'var(--gold)',
        'gold-dim': 'var(--gold-dim)',
        pos: 'var(--pos)',
        neg: 'var(--neg)',
        'tier-fire': 'var(--tier-fire)',
        'tier-crown': 'var(--tier-crown)',
        'tier-jade': 'var(--tier-jade)',
        'tier-npc': 'var(--tier-npc)',
        'tier-poop': 'var(--tier-poop)',
        'tier-skull': 'var(--tier-skull)',
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', 'Songti SC', 'serif'],
        sans: ['"Noto Sans SC"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      maxWidth: {
        page: '1280px',
      },
      borderRadius: {
        none: '0',
        DEFAULT: '0',
      },
    },
  },
  plugins: [],
} satisfies Config
