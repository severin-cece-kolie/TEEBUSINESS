/** @type {import('tailwindcss').Config} */
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
        'luxury-grey': '#f7f7f7',
        'luxury-mid': '#8a8a8a',
      },
      fontFamily: {
        'barlow': ['Barlow', 'sans-serif'],
        'inter': ['Inter', 'sans-serif'],
      },
      borderRadius: {
        'luxury': '12px',
      }
    },
  },
  plugins: [],
}
