import type { Config } from "tailwindcss"

const config: Config = {
  content: [
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eefbf0",
          100: "#d5f5d9",
          200: "#adebb6",
          300: "#78da8a",
          400: "#41c45d",
          500: "#22a840",
          600: "#168833",
          700: "#136c2b",
          800: "#145625",
          900: "#124720",
          950: "#05270f",
        },
      },
    },
  },
  plugins: [],
}

export default config
