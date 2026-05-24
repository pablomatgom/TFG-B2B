export interface RiskData {
  total_supplies_edges: number;
  top_n: number;
  concentration_pct: number;
  top_suppliers: { name: string; degree: number; share_pct: number }[];
}

export interface DiscrepancyRow {
  supplier: string;
  total: number;
  flagged: number;
  discrepancy_rate_pct: number;
}

export interface LeadTimeRow {
  category: string;
  avg_delay_days: number;
  sample: number;
  late_count: number;
  late_pct: number;
}

export interface PaymentRow {
  supplier: string;
  total_exposure_eur: number;
  avg_payment_days: number;
  invoice_count: number;
}

export interface LineageRow {
  factura_id: string;
  riesgo_economico: number;
  pedido_original: string;
  proveedor: string;
  afectado: string;
  id_productos_implicados: string[];
  saltos_topologicos: number;
}

export interface GdsData {
  bottlenecks: {
    company_id: string;
    legal_name: string;
    role: string;
    betweenness_score: number;
  }[];
  communities: {
    communityId: number;
    total_empresas: number;
    ejemplos_empresas: string[];
  }[];
}