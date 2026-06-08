"use client";

import { useAuth } from "@/contexts/AuthContext";

export default function WelcomeHeader() {
  const { user } = useAuth();

  const firstName = user?.full_name?.split(" ")[0] ?? "";
  const dateStr = new Date().toLocaleDateString("es-ES", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="flex items-end justify-between animate-fade-up">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {firstName ? `Bienvenido, ${firstName}` : "Bienvenido"}
        </h1>
        <p className="text-sm text-gray-500 mt-0.5 capitalize">{dateStr}</p>
      </div>
    </div>
  );
}