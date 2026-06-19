/**
 * Legacy configuration reference.
 *
 * Tailwind v4's canonical theme and source paths live in
 * frontend/tailwind.css, and the templates load the compiled local stylesheet.
 * The v4 CLI does not consume this file; keep it only until the remaining
 * historical frontend files are audited in a dedicated cleanup.
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
