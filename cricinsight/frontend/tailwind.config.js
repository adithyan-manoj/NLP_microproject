/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cricket: {
          pitch: "#166534",
          grass: "#22c55e",
          crease: "#f8fafc",
          leather: "#dc2626",
          dark: "#0f172a",
          card: "#1e293b",
          border: "#334155",
          accent: "#38bdf8"
        }
      }
    },
  },
  plugins: [],
}
