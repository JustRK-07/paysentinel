"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ShieldAlert, ArrowLeft } from "lucide-react";
import { Button } from "@tremor/react";

export default function NotFound() {
  return (
    <div className="min-h-[calc(100vh-12rem)] flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="text-center max-w-md"
      >
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-accent/10 mb-6">
          <ShieldAlert className="w-10 h-10 text-accent" />
        </div>
        <h1 className="text-6xl font-bold gradient-text mb-3">404</h1>
        <h2 className="text-xl font-semibold mb-2">Signal lost</h2>
        <p className="text-fg-muted mb-8">
          The page you're looking for has been flagged. Try one of the four pillars instead.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-2 mb-6">
          <Link href="/"><Button icon={ArrowLeft}>Dashboard</Button></Link>
          <Link href="/identify"><Button variant="secondary">Identify</Button></Link>
          <Link href="/generate"><Button variant="secondary">Generate</Button></Link>
          <Link href="/defend"><Button variant="secondary">Defend</Button></Link>
          <Link href="/loop"><Button variant="secondary">Closed Loop</Button></Link>
        </div>
        <p className="text-xs font-mono text-fg-muted">
          PSF-404 · no fraud signal here · report to defend/identify
        </p>
      </motion.div>
    </div>
  );
}
