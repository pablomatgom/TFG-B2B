import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

import { Toaster } from "sonner";

// Importamos la Navbar
import Navbar from "@/components/ui/Navbar";

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
        <Navbar />
        
        {/* Añadimos un padding superior (pt-16) para que el contenido no quede oculto detrás de la Navbar fija */}
        <div className="pt-16 min-h-screen">
          {children}
        </div>

        {/* 2. Añadimos el componente global de notificaciones */}
        <Toaster 
          position="top-right" 
          style={{ top: '80px', right: '24px' }}
          toastOptions={{
            // Clases de Tailwind para que coincida con tu diseño oscuro y cyberpunk
            className: 'bg-[#161B22]/95 border-slate-800 text-slate-200 backdrop-blur-md shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)]',
          }}
        />
      </body>
    </html>
  );
}