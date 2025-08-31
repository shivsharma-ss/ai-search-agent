import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef6ff',
          100: '#d9ecff',
          200: '#bfe0ff',
          300: '#93c9ff',
          400: '#5ca9ff',
          500: '#2b8bff',
          600: '#166fe0',
          700: '#145bb3',
          800: '#154e8f',
          900: '#173f6d',
        },
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
} satisfies Config
