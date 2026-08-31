import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Cyber-noir palette — electric cyan + hot magenta + emerald on near-black
        background: "#0A0A0F",
        surface: "#11131A",
        elevated: "#161922",
        border: "#1F2230",
        primary: {
          DEFAULT: "#00E5FF", // electric cyan
          fg: "#001016",
        },
        accent: {
          DEFAULT: "#FF006E", // hot magenta / danger
          fg: "#160014",
        },
        success: "#10B981", // emerald
        warning: "#F59E0B", // amber
        info: "#A78BFA", // electric purple (AI indicator)
        muted: "#9CA3AF",
        fg: "#F0F0F5",
        "fg-muted": "#9CA3AF",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        lg: "0.625rem",
        md: "0.5rem",
        sm: "0.375rem",
      },
      keyframes: {
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(0, 229, 255, 0.4)" },
          "50%": { boxShadow: "0 0 0 8px rgba(0, 229, 255, 0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "pulse-glow": "pulse-glow 2s infinite",
        shimmer: "shimmer 2s linear infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
