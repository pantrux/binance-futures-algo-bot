import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Binance Futures Algo Bot",
  description: "Trading Workstation Terminal",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="shell-body">
        <aside className="shell-sidebar">
          <div className="shell-logo">Terminal.sys</div>
          <nav className="shell-nav">
            <Link href="/">[ Home ]</Link>
            <Link href="/overview">[ Overview ]</Link>
            <Link href="/positions">[ Positions ]</Link>
            <Link href="/orders">[ Orders ]</Link>
            <Link href="/risk">[ Risk ]</Link>
            <Link href="/shadow-run">[ Shadow Run ]</Link>
            <Link href="/operations">[ Operations ]</Link>
            <Link href="/alerts">[ Alerts ]</Link>
          </nav>
          <div className="shell-status">
            <span>SYS: ONLINE</span>
            <span className="text-accent">NET: CONNECTED</span>
          </div>
        </aside>
        
        <div className="shell-main">
          <header className="shell-topbar">
            <div className="topbar-left">
              <span>Binance Futures Algo Bot</span>
            </div>
            <div className="topbar-right">
              <span>Clock: UTC</span>
              <span className="status-badge testnet">TESTNET</span>
            </div>
          </header>
          
          <main className="shell-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
