/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3b82f6',
          dark: '#2563eb',
          light: '#172554',
        },
        accent: {
          DEFAULT: '#22c55e',
          dark: '#16a34a',
          light: '#052e16',
        },
        danger: {
          DEFAULT: '#ef4444',
          dark: '#dc2626',
          light: '#450a0a',
        },
        neutral: {
          border: '#334155',
          bg: '#0f172a',
          bgAlt: '#1e293b',
          text: '#f1f5f9',
          textMuted: '#94a3b8',
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
