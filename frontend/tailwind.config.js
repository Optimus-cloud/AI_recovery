/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fintech: {
          dark: '#0B0F19',
          card: '#151D30',
          border: '#1F293D',
          primary: '#10B981', // green-500
          danger: '#EF4444', // red-500
          warning: '#F59E0B', // amber-500
          accent: '#3B82F6', // blue-500
          muted: '#9CA3AF' // gray-400
        }
      }
    },
  },
  plugins: [],
}
