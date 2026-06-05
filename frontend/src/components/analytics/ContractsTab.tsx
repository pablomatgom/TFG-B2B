"use client";

import {
  Card, Title, Text, Grid,
  DonutChart,
} from "@tremor/react";
import type { ContractProfileData } from "@/types/analytics";
import { EMPTY } from "./shared";

interface Props {
  contracts: ContractProfileData | null;
}

export function ContractsTab({ contracts }: Props) {
  if (!contracts) return EMPTY;

  const contractDonut = Object.entries(contracts.contract_type_distribution).map(
    ([name, value]) => ({ name, value })
  );

  return (
    <div className="space-y-10">

      {/* ── PERFIL DE CONTRATOS DE RED ───────────────────────────── */}
      <section>
        <h2 className="text-lg font-semibold text-white mb-1">Perfil de Contratos de Red</h2>
        <p className="text-slate-400 text-sm mb-4">
          Caracterización estructural de los acuerdos SUPPLIES de toda la red.
        </p>
        <Grid numItemsSm={1} numItemsLg={3} className="gap-6">
          <Card className="bg-[#1E212B] border-slate-800 flex flex-col items-center justify-center">
            <Title className="text-white mb-3">Tipos de Contrato</Title>
            {contractDonut.length > 0 ? (
              <DonutChart
                data={contractDonut}
                category="value"
                index="name"
                colors={["blue", "violet", "amber"]}
                className="h-36"
              />
            ) : (
              <Text className="text-slate-500 text-sm">Sin datos</Text>
            )}
          </Card>

          <Card className="bg-[#1E212B] border-slate-800 lg:col-span-2">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 h-full items-center">
              <div className="text-center">
                <Text className="text-slate-400 text-xs uppercase tracking-widest mb-1">Exclusividad</Text>
                <p className="text-3xl font-bold text-white tabular-nums">
                  {contracts.exclusivity_pct.toFixed(1)}%
                </p>
                <Text className="text-slate-500 text-xs mt-1">relaciones exclusivas</Text>
              </div>
              <div className="text-center">
                <Text className="text-slate-400 text-xs uppercase tracking-widest mb-1">Fiabilidad Red</Text>
                <p className="text-3xl font-bold tabular-nums" style={{ color: "var(--primary)" }}>
                  {(contracts.avg_reliability_score * 100).toFixed(1)}%
                </p>
                <Text className="text-slate-500 text-xs mt-1">media global</Text>
              </div>
              <div className="text-center">
                <Text className="text-slate-400 text-xs uppercase tracking-widest mb-1">Plazo Pago</Text>
                <p className="text-3xl font-bold text-white tabular-nums">
                  {contracts.avg_payment_terms_days.toFixed(0)} d
                </p>
                <Text className="text-slate-500 text-xs mt-1">media acordada</Text>
              </div>
              <div className="text-center">
                <Text className="text-slate-400 text-xs uppercase tracking-widest mb-1">Antigüedad</Text>
                <p className="text-3xl font-bold text-slate-300 tabular-nums">
                  {contracts.avg_contract_age_days} d
                </p>
                <Text className="text-slate-500 text-xs mt-1">media contratos</Text>
              </div>
            </div>
          </Card>
        </Grid>
      </section>

    </div>
  );
}