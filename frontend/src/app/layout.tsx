import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Swarm Forecaster",
  description: "Multi-agent adversarial forecasting engine",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">
        <nav className="border-b border-[var(--border)] px-6 py-3 flex items-center gap-6">
          <a href="/" className="text-lg font-semibold tracking-tight">
            Swarm Forecaster
          </a>
          <div className="flex gap-4 text-sm text-[var(--text-muted)]">
            <a href="/" className="hover:text-[var(--text)] transition-colors">
              Dashboard
            </a>
            <a
              href="/runs"
              className="hover:text-[var(--text)] transition-colors"
            >
              Runs
            </a>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-6">{children}</main>
      </body>
    </html>
  );
}
