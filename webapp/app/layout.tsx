import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/nav";
import { TopBar } from "@/components/top-bar";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

export const metadata: Metadata = {
  title: "PaySentinel — Agentic Red-Team Lab",
  description: "Identify, generate, and defend against GenAI-powered payment fraud.",
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
        </div>
      </body>
    </html>
  );
}
