import type { Metadata } from "next";
import type { ReactNode } from "react";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ecommerce",
  description: "Catálogo y compras en línea",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className="min-h-screen bg-stone-50 text-stone-950 antialiased dark:bg-stone-950 dark:text-stone-50">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
