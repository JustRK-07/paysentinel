import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/nav";
import { TopBar } from "@/components/top-bar";
import { ToastHost } from "@/components/toast";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

export const metadata: Metadata = {
  title: "PaySentinel — Agentic Red-Team Lab for GenAI Payment Fraud",
  description:
    "Identify novel GenAI payment fraud vectors, generate realistic simulations, and defend with a 5-model ensemble — all in one closed feedback loop. 30 attacks · 7 surfaces · 11/14 MITRE ATLAS tactics covered.",
  keywords: [
    "fraud detection",
    "GenAI",
    "payment security",
    "red team",
    "blue team",
    "closed loop",
    "MITRE ATLAS",
    "deepfake",
    "voice cloning",
  ],
  authors: [{ name: "PaySentinel" }],
  openGraph: {
    title: "PaySentinel — Agentic Red-Team Lab",
    description:
      "Identify, generate, and defend against GenAI-powered payment fraud. Closed-loop red-team/blue-team with 5-model stacking ensemble.",
    type: "website",
  },
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${mono.variable} font-sans`}>
        <div className="relative min-h-screen">
          <TopBar />
          <div className="flex">
            <Nav />
            <main className="flex-1 ml-56 pt-16 px-8 py-8 relative z-10">{children}</main>
          </div>
          <ToastHost />
        </div>
      </body>
    </html>
  );
}
