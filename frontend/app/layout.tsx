import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { LayoutDashboard, FileBarChart, Lightbulb, Settings, Gauge } from "lucide-react";
import KillServiceWorker from "@/components/KillServiceWorker";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Hospital Agentic AI",
  description: "Hospital Resource Optimization Simulation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <KillServiceWorker />
        <div className="min-h-screen bg-slate-50 dark:bg-black">
          <aside className="hidden md:flex fixed inset-y-0 left-0 w-64 bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 flex-col">
            <div className="px-6 py-5 text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-50">
              Agentic Hospital
            </div>
            <nav className="flex-1 px-2 py-2 space-y-1">
              <Link href="/" className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
              <Link href="/reports" className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
                <FileBarChart className="w-4 h-4" />
                <span>Reports</span>
              </Link>
              <Link href="/insights" className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
                <Lightbulb className="w-4 h-4" />
                <span>Insights</span>
              </Link>
              <Link href="/settings" className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </Link>
              <Link href="/resource-optimization" className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
                <Gauge className="w-4 h-4" />
                <span>Resource Optimization</span>
              </Link>
            </nav>
            <div className="px-6 py-4 text-xs text-slate-500 dark:text-slate-400">
              v1.2-Direct
            </div>
          </aside>
          <div className="md:pl-64">
            <div className="md:hidden sticky top-0 z-30 bg-white/80 dark:bg-slate-950/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-between px-4 py-3">
                <span className="text-base font-semibold text-slate-900 dark:text-slate-50">Agentic Hospital</span>
                <nav className="flex items-center gap-3 text-sm">
                  <Link href="/" className="px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800">Dashboard</Link>
                  <Link href="/reports" className="px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800">Reports</Link>
                  <Link href="/insights" className="px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800">Insights</Link>
                  <Link href="/settings" className="px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800">Settings</Link>
                  <Link href="/resource-optimization" className="px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800">Resource Optimization</Link>
                </nav>
              </div>
            </div>
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
