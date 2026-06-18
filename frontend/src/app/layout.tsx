import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

import { Toaster } from "sonner";
import { AuthProvider } from "@/contexts/AuthContext";
import SidebarLayout from "@/components/ui/SidebarLayout";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Audit Command Center",
  description: "Document traceability and bottleneck detection in B2B supply networks via graphs",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" data-scroll-behavior="smooth">
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans bg-[var(--bg-base)] text-[var(--on-surface)] antialiased`}>
        <AuthProvider>
          <SidebarLayout>
            {children}
          </SidebarLayout>
        </AuthProvider>
        <Toaster
          position="top-right"
          style={{ top: "24px", right: "24px" }}
          toastOptions={{
            className: "bg-white border-gray-200 text-gray-900 shadow-lg",
          }}
        />
      </body>
    </html>
  );
}
