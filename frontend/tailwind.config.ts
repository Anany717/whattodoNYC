import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef9f8",
          100: "#d6f0ee",
          500: "#0f766e",
          700: "#0b5e58"
        },
        accent: {
          500: "#d97706",
          700: "#b45309"
        }
      },
      boxShadow: {
        lift: "0 10px 30px rgba(11, 94, 88, 0.18)"
      },
      fontFamily: {
        display: ["\"Space Grotesk\"", "sans-serif"],
        body: ["\"IBM Plex Sans\"", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
