import type { Metadata } from "next";
import { DM_Sans, Manrope } from 'next/font/google';

import "./globals.css";
import Providers from "@/components/Providers";
import Sidebar from "@/components/Sidebar";
import TopNav from "@/components/TopNav";
import ErrorSuppressor from "@/components/ErrorSuppressor";

import BottomNav from "@/components/BottomNav";

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-dm-sans',
  weight: ['300', '400', '500', '600', '700'],
});

const manrope = Manrope({
  subsets: ['latin'],
  variable: '--font-manrope',
});

export const metadata: Metadata = {
  title: "VoltMetric Pro | Dashboard",
  description: "EV Infrastructure Management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${dmSans.variable} ${manrope.variable} antialiased light`}
      suppressHydrationWarning
    >
      <head>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
      </head>
      <body className="flex min-h-screen bg-background text-on-surface" suppressHydrationWarning>
        <Providers>
          <ErrorSuppressor />
          <Sidebar />
          <div className="flex-1 flex flex-col md:ml-64 min-h-screen pb-[72px] md:pb-0 relative">
            <TopNav />
            <main className="flex-1 bg-background font-headline">
              {children}
            </main>
          </div>
          <BottomNav />
        </Providers>
      </body>
    </html>
  );
}
