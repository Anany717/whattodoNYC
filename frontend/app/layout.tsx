import type { Metadata } from "next";

import Navbar from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "WhatToDo NYC",
  description: "Context-aware NYC discovery and decision platform"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  );
}
