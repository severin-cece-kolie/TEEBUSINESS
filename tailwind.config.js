/**
 * Legacy/CDN compatibility mirror.
 *
 * Tailwind v4's canonical theme and source paths live in
 * frontend/tailwind.css. The current templates still load Tailwind's CDN and
 * define smaller inline configs, so keep this file aligned until the visual
 * parity phase is complete.
 *
 * @type {import('tailwindcss').Config}
 */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./**/static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'luxury-black': '#0a0a0a',
        'luxury-grey': '#f6f5f2',
        'luxury-mid': '#77736c',
        'luxury-line': '#e8e4dc',
        'auth-red': '#a23b32',
        'auth-red-dark': '#8a3029',
      },
      fontFamily: {
        'barlow': ['Barlow', 'sans-serif'],
        'inter': ['Inter', 'sans-serif'],
        'poppins': ['Poppins', 'sans-serif'],
      },
      borderRadius: {
        'luxury': '8px',
      }
    },
  },
  plugins: [],
}
