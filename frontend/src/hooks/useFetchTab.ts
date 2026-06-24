"use client";

import { useEffect, useRef, type Dispatch } from "react";
import { API_BASE } from "@/lib/api";
import type {
  RiskData, SupplierScoreRow, BuyerFragilityRow,
  DiscrepancyRow, CommercialImpactRow,
  LeadTimeRow,
  PaymentRow, OverdueRow,
  LineageRow, ExactPathRow, ForwardRow,
  GdsData,
  ContractProfileData, ContractDetailRow,
  GeographicRiskRow,
} from "@/types/analytics";

/* ── State shape ────────────────────────────────────────────── */

export type AnalyticsState = {
  risk:           RiskData | null;
  scores:         SupplierScoreRow[];
  fragility:      BuyerFragilityRow[];
  discrepancy:    DiscrepancyRow[];
  commercial:     CommercialImpactRow[];
  leadTime:       LeadTimeRow[];
  payment:        PaymentRow[];
  overdueRows:    OverdueRow[];
  lineage:        LineageRow[];
  exactPaths:     ExactPathRow[];
  forward:        ForwardRow[];
  gds:            GdsData;
  contracts:      ContractProfileData | null;
  contractDetail: ContractDetailRow[];
  geographic: GeographicRiskRow[];
};

/* ── Action union — one per tab ─────────────────────────────── */

export type AnalyticsAction =
  | { type: "SET_RISK";         data: Pick<AnalyticsState, "risk" | "scores" | "fragility" | "geographic"> }
  | { type: "SET_DISCREPANCY";  data: Pick<AnalyticsState, "discrepancy" | "commercial"> }
  | { type: "SET_LEAD_TIME";    data: Pick<AnalyticsState, "leadTime"> }
  | { type: "SET_EXPOSURE";     data: Pick<AnalyticsState, "payment" | "overdueRows"> }
  | { type: "SET_TRACEABILITY"; data: Pick<AnalyticsState, "lineage" | "exactPaths" | "forward"> }
  | { type: "SET_GDS";          data: Pick<AnalyticsState, "gds"> }
  | { type: "SET_CONTRACTS";    data: Pick<AnalyticsState, "contracts" | "contractDetail"> };

/* ── Reducer + initial state ────────────────────────────────── */

export const INITIAL_ANALYTICS_STATE: AnalyticsState = {
  risk:           null,
  scores:         [],
  fragility:      [],
  discrepancy:    [],
  commercial:     [],
  leadTime:       [],
  payment:        [],
  overdueRows:    [],
  lineage:        [],
  exactPaths:     [],
  forward:        [],
  gds:            { bottlenecks: [], communities: [], pagerank: [], wcc: {} as GdsData["wcc"] },
  contracts:      null,
  contractDetail: [],
  geographic: [],
};

export function analyticsReducer(
  state: AnalyticsState,
  action: AnalyticsAction,
): AnalyticsState {
  return { ...state, ...action.data };
}

/* ── Fetch helpers ──────────────────────────────────────────── */

const j = <T>(url: string): Promise<T> =>
  fetch(url).then((r) => { if (!r.ok) throw new Error(`${r.status} ${r.statusText}`); return r.json() as Promise<T>; });
const arr = <T>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : []);

async function fetchTabData(tab: number): Promise<AnalyticsAction> {
  switch (tab) {
    case 0: {
      const [contractsD, detailD] = await Promise.all([
        j<ContractProfileData>(`${API_BASE}/api/analytics/risk/contracts`),
        j<unknown>(`${API_BASE}/api/analytics/risk/contracts-detail`),
      ]);
      return { type: "SET_CONTRACTS", data: {
        contracts:      (contractsD as ContractProfileData)?.contract_type_distribution ? contractsD as ContractProfileData : null,
        contractDetail: arr<ContractDetailRow>(detailD),
      }};
    }
    case 1: {
      const [riskD, scoresD, fragD, geoD] = await Promise.all([
        j<RiskData>(`${API_BASE}/api/analytics/risk`),
        j<unknown>(`${API_BASE}/api/analytics/risk/supplier-score`),
        j<unknown>(`${API_BASE}/api/analytics/risk/buyer-fragility`),
        j<unknown>(`${API_BASE}/api/analytics/risk/geographic`),
      ]);
      return { type: "SET_RISK", data: {
        risk:      (riskD as RiskData)?.total_supplies_edges ? riskD as RiskData : null,
        scores:    arr<SupplierScoreRow>(scoresD),
        fragility: arr<BuyerFragilityRow>(fragD),
        geographic: arr<GeographicRiskRow>(geoD),
      }};
    }
    case 2: {
      const [discD, comD] = await Promise.all([
        j<unknown>(`${API_BASE}/api/analytics/discrepancy-suppliers`),
        j<unknown>(`${API_BASE}/api/analytics/risk/commercial-impact`),
      ]);
      return { type: "SET_DISCREPANCY", data: {
        discrepancy: arr<DiscrepancyRow>(discD),
        commercial:  arr<CommercialImpactRow>(comD),
      }};
    }
    case 3: {
      const ltD = await j<unknown>(`${API_BASE}/api/analytics/lead-time`);
      return { type: "SET_LEAD_TIME", data: { leadTime: arr<LeadTimeRow>(ltD) } };
    }
    case 4: {
      const [payD, overdueD] = await Promise.all([
        j<unknown>(`${API_BASE}/api/analytics/payment`),
        j<unknown>(`${API_BASE}/api/analytics/risk/overdue`),
      ]);
      return { type: "SET_EXPOSURE", data: {
        payment:     arr<PaymentRow>(payD),
        overdueRows: arr<OverdueRow>(overdueD),
      }};
    }
    case 5: {
      const [linD, pathD, fwdD] = await Promise.all([
        j<unknown>(`${API_BASE}/api/analytics/lineage/backward`),
        j<unknown>(`${API_BASE}/api/analytics/lineage/exact-paths`),
        j<unknown>(`${API_BASE}/api/analytics/lineage/forward`),
      ]);
      return { type: "SET_TRACEABILITY", data: {
        lineage:    arr<LineageRow>(linD),
        exactPaths: arr<ExactPathRow>(pathD),
        forward:    arr<ForwardRow>(fwdD),
      }};
    }
    case 6: {
      const gdsD = await j<GdsData | null>(`${API_BASE}/api/analytics/gds`);
      return { type: "SET_GDS", data: {
        gds: gdsD ?? { bottlenecks: [], communities: [], pagerank: [], wcc: {} as GdsData["wcc"] },
      }};
    }
    default:
      throw new Error(`Unknown tab: ${tab}`);
  }
}

/* ── Hook ───────────────────────────────────────────────────── */

export function useFetchTab(
  activeTab:     number,
  dispatch:      Dispatch<AnalyticsAction>,
  setLoadingTab: (tab: number | null) => void,
) {
  const fetchedRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    if (fetchedRef.current.has(activeTab)) return;
    fetchedRef.current.add(activeTab);
    setLoadingTab(activeTab);
    fetchTabData(activeTab)
      .then((action) => dispatch(action))
      .catch((err)   => console.error(`Tab ${activeTab} fetch failed:`, err))
      .finally(()    => setLoadingTab(null));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);
}
