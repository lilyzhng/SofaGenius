import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Playfair Display"', "serif"],
        sans: ['"Inter"', "sans-serif"],
      },
      colors: {
        "nobel-gold": "#C5A059",
        "nobel-cream": "#F9F8F4",
        "nobel-cream-dark": "#F5F4F0",
      },
    },
  },
  plugins: [],
} satisfies Config;
