"use client";

import React, { useState, useEffect } from "react";
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";
import { toast } from "sonner";

export default function SpainMap() {
  const [locations, setLocations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Creamos un controlador para poder cancelar la petición
    const controller = new AbortController();
    const signal = controller.signal;

    // 2. Le pasamos la señal al fetch
    fetch("http://localhost:8000/api/network/locations", { signal })
      .then((res) => {
        if (!res.ok) throw new Error("Fallo en la respuesta del servidor");
        return res.json();
      })
      .then((data) => {
        setLocations(data);
        setLoading(false);
      })
      .catch((error) => {
        // 3. Si el error es porque React canceló la petición (por el Strict Mode), lo ignoramos
        if (error.name === "AbortError") {
          console.log("Petición cancelada por limpieza de React");
          return; 
        }

        console.error("Error al sincronizar nodos con FastAPI:", error);
        setLoading(false);

        toast.error(
          <div className="flex flex-col gap-1">
            <span className="font-bold">Error al cargar el mapa</span>
            <span className="text-slate-400 text-xs">No se han podido obtener las ubicaciones. Comprueba tu conexión con el servidor.</span>
          </div>,
          // Opcional: Le damos un ID al toast para que, si por algún motivo saltan dos, Sonner no los duplique en pantalla
          { id: "map-error-toast" } 
        );
      });

    // 4. Función de limpieza (Cleanup): React llama a esto cuando desmonta el componente
    return () => {
      controller.abort();
    };
  }, []);

  return (
    <div className="h-[500px] w-full flex justify-center items-center relative z-0">
      
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-10 backdrop-blur-sm bg-[#0E1117]/30">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mb-2"></div>
          <span className="text-cyan-400 text-sm font-mono animate-pulse">Sincronizando nodos...</span>
        </div>
      )}

      <ComposableMap
        projection="geoMercator"
        projectionConfig={{
          center: [-4, 40], 
          scale: 2200 
        }}
        style={{ width: "100%", height: "100%" }}
      >
        <Geographies geography="/spain.json">
          {({ geographies }: { geographies: any[] }) =>
            geographies.map((geo: any) => (
              <Geography
                key={geo.rsmKey || geo.properties.cartodb_id}
                geography={geo}
                fill="#272A35" 
                stroke="#374151" 
                strokeWidth={0.5}
                style={{
                  default: { outline: "none" },
                  hover: { fill: "#3b4252", outline: "none", transition: "all 250ms" },
                  pressed: { outline: "none" }
                }}
              />
            ))
          }
        </Geographies>

        {locations.map((loc, index) => (
          <Marker key={index} coordinates={loc.coordinates as [number, number]}>
            {/* Animación de pulso (opcional, si hay demasiados puntos puedes quitarla para mejorar rendimiento) */}
            <circle 
              r={loc.weight ? Math.max(Math.log(loc.weight) * 2, 4) : 4} 
              fill="#22d3ee" 
              className="opacity-20 animate-ping" 
            />
            {/* Punto sólido */}
            <circle 
              r={loc.weight ? Math.max(Math.log(loc.weight) * 1, 2) : 2} 
              fill="#22d3ee" 
              stroke="#0E1117" 
              strokeWidth={0.5} 
            />
          </Marker>
        ))}
      </ComposableMap>
    </div>
  );
}