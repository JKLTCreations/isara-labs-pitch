import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Isara Labs",
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
        <div className="flex h-screen">
          {/* ── Sidebar ── */}
          <aside className="w-[240px] shrink-0 flex flex-col bg-[var(--bg-secondary)] border-r border-[var(--border)] shadow-[var(--shadow-md)]">
            {/* Logo */}
            <div className="px-6 py-6 flex items-center gap-3">
              <div className="relative">
                <img
                  src="/isara.png"
                  alt="Isara Labs"
                  className="w-9 h-9 rounded-full"
                />
                <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[var(--green)] ring-2 ring-[var(--bg-secondary)] pulse-online" />
              </div>
              <div>
                <span className="text-[15px] font-semibold tracking-[-0.01em] text-[var(--cream)]">
                  Isara Labs
                </span>
                <p className="text-[10px] font-medium text-[var(--text-tertiary)] tracking-wide uppercase mt-0.5">
                  Forecasting
                </p>
              </div>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-3 mt-2 space-y-1">
              <NavItem href="/" label="Forecasts" icon={
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M2 14l5-6 3 3.5 6-8" />
                </svg>
              } />
              <NavItem href="/runs" label="Runs" icon={
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="3" width="14" height="12" rx="0" />
                  <path d="M2 7h14" />
                </svg>
              } />
            </nav>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-[var(--border)]">
              <div className="flex items-center gap-2.5">
                <div className="w-[6px] h-[6px] rounded-full bg-[var(--green)] pulse-online" />
                <span className="text-[11px] font-medium text-[var(--text-tertiary)]">
                  All systems operational
                </span>
              </div>
            </div>
          </aside>

          {/* ── Main ── */}
          <main className="flex-1 overflow-auto">
            <div className="max-w-[1100px] mx-auto px-10 py-10">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}

function NavItem({ href, label, icon }: { href: string; label: string; icon: React.ReactNode }) {
  return (
    <a
      href={href}
      className="group flex items-center gap-3 px-4 py-2.5 text-[13px] font-medium text-[var(--text-secondary)] hover:text-[var(--cream)] hover:bg-[var(--accent)]/10 transition-all duration-300 ease-out"
    >
      <span className="text-[var(--text-tertiary)] group-hover:text-[var(--accent-light)] transition-colors duration-300">
        {icon}
      </span>
      {label}
    </a>
  );
}
