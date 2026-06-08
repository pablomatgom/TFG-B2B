"use client";

import { useState } from "react";
import { BuildingOffice2Icon, DocumentDuplicateIcon } from "@heroicons/react/24/outline";
import SectionHeader from "@/components/dashboard/SectionHeader";
import SimpleBarList from "@/components/dashboard/SimpleBarList";
import DocTypeDonut  from "@/components/dashboard/DocTypeDonut";
import RankingModal  from "@/components/dashboard/RankingModal";
import type { ModalData } from "@/components/dashboard/RankingModal";

interface RankingsGridProps {
  docTypes:  { name: string; value: number }[];
  suppliers: { name: string; value: number }[];
  buyers:    { name: string; value: number }[];
}

export default function RankingsGrid({ docTypes, suppliers, buyers }: RankingsGridProps) {
  const [modal, setModal] = useState<ModalData | null>(null);

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Doc types donut */}
        <div className="animate-fade-up stagger-2 bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <SectionHeader
            icon={DocumentDuplicateIcon}
            title="Tipos de Documento"
            subtitle="Distribución por categoría EDI."
            iconColor="text-gray-500"
            iconBg="bg-gray-100"
          />
          {docTypes.length > 0 ? (
            <DocTypeDonut data={docTypes} />
          ) : (
            <p className="text-gray-400 text-sm py-10 text-center">
              Sin datos — ejecuta el pipeline primero.
            </p>
          )}
        </div>

        {/* Top suppliers */}
        <div className="animate-fade-up stagger-3 bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <SectionHeader
            icon={BuildingOffice2Icon}
            title="Top Proveedores"
            subtitle="Por número de clientes abastecidos."
            iconColor="text-gray-500"
            iconBg="bg-gray-100"
          />
          {suppliers.length > 0 ? (
            <>
              <SimpleBarList data={suppliers.slice(0, 5)} suffix="clientes" color="primary" />
              {suppliers.length > 5 && (
                <button
                  onClick={() => setModal({
                    title:    "Top Proveedores",
                    subtitle: "Por número de clientes abastecidos.",
                    data:     suppliers,
                    suffix:   "clientes",
                    color:    "primary",
                  })}
                  className="mt-4 w-full py-2 text-[11px] font-semibold rounded-lg border border-gray-200 text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-all duration-150"
                >
                  Ver todos ({suppliers.length}) →
                </button>
              )}
            </>
          ) : (
            <p className="text-gray-400 text-sm py-10 text-center">Sin datos.</p>
          )}
        </div>

        {/* Top buyers */}
        <div className="animate-fade-up stagger-4 bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <SectionHeader
            icon={BuildingOffice2Icon}
            title="Top Compradores"
            subtitle="Por número de proveedores recibidos."
            iconColor="text-gray-500"
            iconBg="bg-gray-100"
          />
          {buyers.length > 0 ? (
            <>
              <SimpleBarList data={buyers.slice(0, 5)} suffix="proveedores" color="violet" />
              {buyers.length > 5 && (
                <button
                  onClick={() => setModal({
                    title:    "Top Compradores",
                    subtitle: "Por número de proveedores recibidos.",
                    data:     buyers,
                    suffix:   "proveedores",
                    color:    "violet",
                  })}
                  className="mt-4 w-full py-2 text-[11px] font-semibold rounded-lg border border-gray-200 text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-all duration-150"
                >
                  Ver todos ({buyers.length}) →
                </button>
              )}
            </>
          ) : (
            <p className="text-gray-400 text-sm py-10 text-center">Sin datos.</p>
          )}
        </div>

      </div>

      <RankingModal modal={modal} onClose={() => setModal(null)} />
    </>
  );
}