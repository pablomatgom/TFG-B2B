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
  avg_agreed_days: number;
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

export interface ChainNode {
  id: string;
  tipo: string;
  importe: number | null;
  discrepancy: boolean;
  estado: string | null;
  fecha: string | null;
}

export interface ExactPathRow {
  factura_id: string;
  pedido_original: string;
  proveedor: string;
  afectado: string;
  cadena_completa: ChainNode[];
  saltos_topologicos: number;
  importe_factura: number;
  importe_pedido: number;
}

export type ForwardDoc = Omit<ChainNode, "fecha">;

export interface ForwardRow {
  pedido_id: string;
  importe_pedido_eur: number;
  estado_pedido: string | null;
  proveedor: string;
  comprador: string;
  total_docs_cumplimiento: number;
  docs_con_discrepancia: number;
  documentos_cumplimiento: ForwardDoc[];
}

export interface CommercialImpactRow {
  pedido_id: string;
  proveedor: string;
  comprador: string;
  importe_pedido_eur: number;
  total_facturado_eur: number;
  delta_eur: number;
  delta_pct: number | null;
  num_facturas: number;
  facturas_con_discrepancia: number;
  importe_en_discrepancia_eur: number;
  estado_comercial: "SOBREFACTURADO" | "SUBFACTURADO" | "CONFORME";
}

export interface SupplierScoreRow {
  supplier: string;
  avg_reliability: number;
  discrepancy_pct: number;
  late_pct: number;
  supply_degree: number;
  risk_score: number;
  overdue_count: number;
  overdue_eur: number;
}

export interface BuyerFragilityRow {
  buyer: string;
  node_role: string;
  region: string;
  supplier_count: number;
  top_supplier_pct: number;
  total_volume_eur: number;
  overdue_received: number;
  overdue_eur: number;
}

export interface OverdueRow {
  supplier: string;
  buyer: string;
  overdue_invoices: number;
  total_overdue_eur: number;
  avg_payment_days: number;
  avg_agreed_days: number;
}

export interface ContractProfileData {
  contract_type_distribution: Record<string, number>;
  exclusivity_pct: number;
  avg_reliability_score: number;
  avg_payment_terms_days: number;
  avg_contract_age_days: number;
}

export interface ContractDetailRow {
  supplier: string;
  region: string;
  total_contracts: number;
  contract_types: string[];
  exclusive_contracts: number;
  exclusive_pct: number;
  avg_reliability: number;
  avg_payment_terms_days: number;
}

export interface SupplierInvoiceRow {
  document_id: string;
  buyer: string;
  gross_amount: number;
  status: string;
  payment_terms_days: number;
  due_date: string | null;
  issue_date: string | null;
  discrepancy_flag: boolean;
}

export interface BuyerSupplierRecommendationRow {
  supplier: string;
  region: string | null;
  size_band: string | null;
  industry_code: string | null;
  supply_degree: number;
  avg_reliability: number;
  cat_overlap: number;
  proximity_count: number;
}

export interface SupplierContractRow {
  buyer: string;
  buyer_region: string | null;
  contract_type: string;
  is_exclusive: boolean;
  reliability_score: number;
  payment_terms_days: number;
  agreed_volume_eur: number;
  since_date: string | null;
}

export interface GeographicRiskRow {
  region: string;
  supplier_count: number;
  avg_reliability: number;
  total_invoices: number;
  discrepancy_pct: number;
}

export interface CrossSupplierRow {
  supplier: string;
  region: string;
  supply_degree: number;
  total_invoices: number;
  discrepancy_pct: number;
  late_pct: number;
  risk_score: number;
  avg_reliability: number;
  overdue_count: number;
  overdue_eur: number;
}

export interface CrossBuyerRow {
  buyer: string;
  region: string;
  supplier_count: number;
  top_supplier_pct: number;
  overdue_received: number;
  overdue_eur: number;
}

export interface WccData {
  total_components: number;
  main_component_size: number;
  main_component_pct: number;
  isolated_nodes: number;
  components: { component_id: number; size: number }[];
}

export interface GdsData {
  bottlenecks: {
    company_id: string;
    legal_name: string;
    role: string;
    betweenness_score: number;
    normalized_pct: number;
  }[];
  communities: {
    communityId: number;
    total_empresas: number;
    ejemplos_empresas: { name: string; role: string; region: string; band: string; sector: string }[];
  }[];
  pagerank: {
    company_id: string;
    legal_name: string;
    role: string;
    pagerank_score: number;
  }[];
  wcc: WccData;
}