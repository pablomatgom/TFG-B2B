export interface ScaleFreeMetrics {
  node_count:       number;
  mean_degree:      number;
  median_degree:    number;
  std_degree:       number;
  max_degree:       number;
  min_degree:       number;
  gini_coefficient: number;
  hub_count:        number;
  hub_threshold:    number;
  max_mean_ratio:   number;
}

export interface MacroStats {
  node_counts:         Record<string, number>;
  relationship_counts: Record<string, number>;

  top_suppliers: {
    company_id:          string;
    legal_name:          string;
    supplies_out:        number;
    avg_agreed_volume:   number;
  }[];

  top_buyers: {
    company_id:          string;
    legal_name:          string;
    supplies_in:         number;
    avg_agreed_volume:   number;
  }[];

  doc_type_counts: Record<string, number>;

  economic_volume: {
    invoice_count:   number;
    total_gross_eur: number;
    total_tax_eur:   number;
    total_net_eur:   number;
  };

  document_health: {
    total_documents:              number;
    flagged_documents:            number;
    overall_discrepancy_rate_pct: number;
  };

  /** Empty object `{}` when the graph has no SUPPLIES edges yet. */
  scale_free_metrics: Partial<ScaleFreeMetrics>;
}

export interface TemporalSeriesRow {
  year:              number;
  month:             number;
  documents:         number;
  flagged:           number;
  total_gross_eur:   number;
  active_companies:   number;
  active_products:    number;
  active_connections: number;
  /** Computed by the frontend: `"YYYY-MM"`. */
  date?:             string;
}

export interface DashboardResponse {
  macro_stats:     MacroStats;
  temporal_series: TemporalSeriesRow[];
}