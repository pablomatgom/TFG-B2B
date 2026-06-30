# Arquitectura del Subsistema Analítico

La capa analítica se organiza como un **patrón de composición por mixins**: `B2BGraphAnalyzer`
hereda de cuatro mixins especializados, cada uno en su propio fichero. Todos comparten el
helper `_fetch_data()` definido en `analyzer.py`.

```
B2BGraphAnalyzer          (analyzer.py)
├── MacroMixin             (macro_stats.py)   — estructura global, rankings, series temporales
├── LineageMixin           (traceability.py)  — trazabilidad backward / exact-path / forward
├── GDSMixin               (gds.py)           — betweenness, PageRank, Louvain, WCC
└── RiskMixin              (risk.py)
    ├── DiscrepancyMixin   (risk_discrepancy.py) — tasa de discrepancias e impacto comercial
    ├── OperationalMixin   (risk_supply.py)      — lead time, pagos, concentración, geografía
    ├── ScoringMixin       (risk_scoring.py)     — scoring compuesto, fragilidad, contratos
    └── SynthesisMixin     (risk_cross.py)       — análisis cruzado multidimensional
```

---

## Tabla de métodos públicos

| Módulo | Mixin | Método | Salida |
|---|---|---|---|
| `macro_stats.py` | `MacroMixin` | `get_macro_statistics()` | `GraphMacroStats` |
| `macro_stats.py` | `MacroMixin` | `get_temporal_distribution()` | `DataFrame` |
| `traceability.py` | `LineageMixin` | `get_backward_traceability()` | `DataFrame` |
| `traceability.py` | `LineageMixin` | `extract_lineage_paths()` | `DataFrame` |
| `traceability.py` | `LineageMixin` | `get_forward_traceability()` | `DataFrame` |
| `gds.py` | `GDSMixin` | `compute_betweenness_centrality()` | `DataFrame` |
| `gds.py` | `GDSMixin` | `compute_pagerank()` | `DataFrame` |
| `gds.py` | `GDSMixin` | `detect_communities_louvain()` | `DataFrame` |
| `gds.py` | `GDSMixin` | `detect_weakly_connected_components()` | `dict` |
| `risk_discrepancy.py` | `DiscrepancyMixin` | `get_discrepancy_rate_by_supplier()` | `DataFrame` |
| `risk_discrepancy.py` | `DiscrepancyMixin` | `compute_commercial_impact(tolerance_pct)` | `DataFrame` |
| `risk_supply.py` | `OperationalMixin` | `get_lead_time_compliance()` | `DataFrame` |
| `risk_supply.py` | `OperationalMixin` | `get_payment_terms_exposure()` | `DataFrame` |
| `risk_supply.py` | `OperationalMixin` | `get_overdue_exposure()` | `DataFrame` |
| `risk_supply.py` | `OperationalMixin` | `get_supplier_risk_concentration()` | `dict` |
| `risk_supply.py` | `OperationalMixin` | `get_geographic_risk()` | `DataFrame` |
| `risk_scoring.py` | `ScoringMixin` | `get_contract_detail()` | `DataFrame` |
| `risk_scoring.py` | `ScoringMixin` | `compute_supplier_risk_score()` | `DataFrame` |
| `risk_scoring.py` | `ScoringMixin` | `get_buyer_fragility()` | `DataFrame` |
| `risk_scoring.py` | `ScoringMixin` | `get_contract_profile()` | `dict` |
| `risk_cross.py` | `SynthesisMixin` | `get_cross_dimensional_suppliers()` | `DataFrame` |

---

## Mapa de consumo API → Backend

| Endpoint | Métodos backend |
|---|---|
| `GET /api/dashboard/macro` | `get_macro_statistics()`, `get_temporal_distribution()` |
| `GET /api/analytics/gds` | `compute_betweenness_centrality()`, `compute_pagerank()`, `detect_communities_louvain()`, `detect_weakly_connected_components()` |
| `GET /api/analytics/lineage/backward` | `get_backward_traceability()` |
| `GET /api/analytics/lineage/exact-paths` | `extract_lineage_paths()` |
| `GET /api/analytics/lineage/forward` | `get_forward_traceability()` |
| `GET /api/analytics/risk` | `get_supplier_risk_concentration()` |
| `GET /api/analytics/risk/supplier-score` | `compute_supplier_risk_score()` |
| `GET /api/analytics/risk/buyer-fragility` | `get_buyer_fragility()` |
| `GET /api/analytics/risk/contracts` | `get_contract_profile()` |
| `GET /api/analytics/risk/contracts-detail` | `get_contract_detail()` |
| `GET /api/analytics/risk/geographic` | `get_geographic_risk()` |
| `GET /api/analytics/risk/overdue` | `get_overdue_exposure()` |
| `GET /api/analytics/risk/synthesis/suppliers` | `get_cross_dimensional_suppliers()` |
| `GET /api/analytics/discrepancy-suppliers` | `get_discrepancy_rate_by_supplier()` |
| `GET /api/analytics/risk/commercial-impact` | `compute_commercial_impact()` |
| `GET /api/analytics/lead-time` | `get_lead_time_compliance()` |
| `GET /api/analytics/payment` | `get_payment_terms_exposure()` |