/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        void: "#07070a",
        crypt: "#0c0c10",
        slab: "#111116",
        bone: "#e9e3d7",
        ash: "#a29c90",
        dust: "#7e7970",
        ember: "#cf6440",
        candle: "#e9b578",
        blood: "#7a2f26",
        moss: "#7c8a6d",
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', "Georgia", "serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      letterSpacing: {
        widest2: "0.28em",
      },
      keyframes: {
        flicker: {
          "0%, 100%": { opacity: "0.85", transform: "scale(1)" },
          "25%": { opacity: "0.55", transform: "scale(0.94)" },
          "50%": { opacity: "1", transform: "scale(1.03)" },
          "75%": { opacity: "0.7", transform: "scale(0.97)" },
        },
        fog: {
          "0%, 100%": { transform: "translate3d(-2%, 0, 0) scale(1)" },
          "50%": { transform: "translate3d(2%, -1%, 0) scale(1.06)" },
        },
        rise: {
          from: { opacity: "0", transform: "translateY(14px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        breathe: {
          "0%, 100%": { opacity: "0.35" },
          "50%": { opacity: "0.75" },
        },
      },
      animation: {
        flicker: "flicker 3.2s ease-in-out infinite",
        fog: "fog 26s ease-in-out infinite",
        rise: "rise 0.7s cubic-bezier(0.18, 0.7, 0.2, 1) both",
        shimmer: "shimmer 2.2s ease-in-out infinite",
        breathe: "breathe 4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
