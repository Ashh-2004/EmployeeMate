/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-green': '#25d366',
        'link-blue': '#0373e9',
        'charcoal': '#1c1e21',
        'ink-black': '#111b21',
        'cream-canvas': '#fcf5eb',
        'pure-white': '#ffffff',
        'warm-gray': '#5e5e5e',
        'pale-blue': '#f0f4f9',
        'chat-user': '#d9fdd3',
      },
      borderRadius: {
        'pill': '50px',
        'card': '16px',
        'image': '25px',
      }
    },
  },
  plugins: [],
}

