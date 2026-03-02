import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "WhatToDo NYC",
  description: "Context-aware NYC discovery and decision platform"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-6">
          <Link href="/" className="font-display text-2xl font-bold text-brand-700">
            WhatToDo NYC
          </Link>
          <nav className="flex gap-3 text-sm font-semibold text-slate-700">
            <Link href="/results">Results</Link>
            <Link href="/map">Map</Link>
            <Link href="/login">Login</Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
