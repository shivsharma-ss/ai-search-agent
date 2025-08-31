/** @type {import('tailwindcss').Config} */
module.exports = {
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
        neon: {
          500: '#00f5ff',
          600: '#00d1ff',
          700: '#00a8ff'
        }
      },
      keyframes: {
        glow: {
          '0%, 100%': { boxShadow: '0 0 10px rgba(0,245,255,0.4), 0 0 30px rgba(0,168,255,0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(0,245,255,0.6), 0 0 40px rgba(0,168,255,0.5)' }
        },
        gridMove: {
          '0%': { backgroundPosition: '0 0, 0 0' },
          '100%': { backgroundPosition: '100px 50px, 100px 50px' }
        },
        pulseBorder: {
          '0%, 100%': { opacity: 0.4 },
          '50%': { opacity: 1 }
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' }
        }
      },
      animation: {
        glow: 'glow 2.5s ease-in-out infinite',
        grid: 'gridMove 12s linear infinite',
        pulseBorder: 'pulseBorder 3s ease-in-out infinite',
        scanline: 'scanline 6s linear infinite'
      }
    }
  },
  plugins: [require('@tailwindcss/forms')]
}

