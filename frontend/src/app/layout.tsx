import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

import { Toaster } from "sonner";

import Navbar from "@/components/ui/Navbar";
import { AuthProvider } from "@/contexts/AuthContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "B2B Graph Intelligence",
  description: "Análisis de Redes Logísticas con Neo4j",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className={`${inter.className} bg-[#0E1117] text-slate-50 antialiased`}>
        {/* La Navbar se quedará fija arriba en todas las páginas */}
        <AuthProvider>
          <Navbar />
          <div className="pt-16 min-h-screen">
            {children}
          </div>
        </AuthProvider>
        {/* Notificaciones a los usuarios izquierda arriba*/}
        <Toaster 
          position="top-right" 
          style={{ top: '80px', right: '24px' }}
          toastOptions={{
            className: 'bg-[#161B22]/95 border-slate-800 text-slate-200 backdrop-blur-md shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)]',
          }}
        />
      </body>
    </html>
  );
}