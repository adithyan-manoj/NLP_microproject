/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Manrope', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        card: {
          DEFAULT: 'var(--card)',
          foreground: 'var(--foreground)',
        },
        popover: {
          DEFAULT: 'var(--popover)',
          foreground: 'var(--foreground)',
        },
        primary: {
          DEFAULT: 'var(--primary)',
          foreground: 'var(--primary-foreground)',
        },
        secondary: {
          DEFAULT: 'var(--secondary)',
          foreground: 'var(--foreground)',
        },
        muted: {
          DEFAULT: 'var(--secondary)',
          foreground: 'var(--muted-foreground)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          foreground: 'var(--foreground)',
        },
        destructive: {
          DEFAULT: 'var(--destructive)',
          foreground: '#ffffff',
        },
        border: 'var(--border)',
        ring: 'var(--primary)',
        sidebar: 'var(--sidebar)',
        lime: '#B9F36B',
        cyan: '#55C9E8',
        warn: '#E5B54A',
        cricket: {
          pitch: "#166534",
          grass: "#22c55e",
          crease: "#f8fafc",
          leather: "#dc2626",
          dark: "#0a0f1d",
          surface: "#0f172a",
          card: "#131d31",
          border: "#1e293b",
          accent: "#38bdf8"
        },
        cricops: {
          canvas: "#070b14",
          surface: "#0c1322",
          card: "#0f172a",
          cardElevated: "#131e35",
          border: "#1e293b",
          borderLight: "#334155",
          cyan: "#06b6d4",
          cyanLight: "#22d3ee",
          emerald: "#10b981",
          amber: "#f59e0b",
          purple: "#8b5cf6",
          crimson: "#ef4444"
        }
      },
      boxShadow: {
        'glow-cyan': '0 0 25px -5px rgba(6, 182, 212, 0.25)',
        'glow-emerald': '0 0 25px -5px rgba(16, 185, 129, 0.25)',
        'card-elevated': '0 10px 30px -10px rgba(2, 6, 23, 0.7)',
      }
    },
  },
  plugins: [],
}
