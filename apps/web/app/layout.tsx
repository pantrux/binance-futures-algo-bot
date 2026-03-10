import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Binance Futures Algo Bot",
  description: "Panel de control del bot de trading algorítmico",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
