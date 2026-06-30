# Routers de la API

Los routers agrupan los endpoints REST por dominio funcional y se montan
sobre la aplicación FastAPI principal.  Todos los endpoints protegidos
requieren un JWT válido en la cabecera `Authorization: Bearer <token>`.

---

## Salud (`health.py`)

::: backend.api.routers.health.root
    options:
      show_root_full_path: false

::: backend.api.routers.health.api_health_check
    options:
      show_root_full_path: false

---

## Autenticación (`auth.py`)

Prefijo: `/auth`

::: backend.api.routers.auth.login
    options:
      show_root_full_path: false

::: backend.api.routers.auth.get_me
    options:
      show_root_full_path: false

::: backend.api.routers.auth.register
    options:
      show_root_full_path: false

### Helper interno

::: backend.api.routers.auth._make_token
    options:
      show_root_full_path: false

---

## Dashboard (`dashboard.py`)

Prefijo: `/api/dashboard`

::: backend.api.routers.dashboard.get_macro_dashboard
    options:
      show_root_full_path: false

---

## Empresa y Documentos (`company.py`)

Endpoints que operan sobre el nodo `Company` del usuario autenticado y sus
documentos EDI asociados en Neo4j.

::: backend.api.routers.company.get_my_company
    options:
      show_root_full_path: false

::: backend.api.routers.company.update_my_company
    options:
      show_root_full_path: false

::: backend.api.routers.company.get_my_documents
    options:
      show_root_full_path: false

::: backend.api.routers.company.update_document_status
    options:
      show_root_full_path: false

---

## Pipeline ETL (`pipeline.py`)

Modelo de ejecución: un único pipeline activo a la vez, gestionado con un
lock en memoria. El estado persiste en `_state` mientras el proceso esté
vivo y se reinicia a `idle` al reiniciar el servidor.

::: backend.api.routers.pipeline.trigger_pipeline
    options:
      show_root_full_path: false

::: backend.api.routers.pipeline.get_pipeline_status
    options:
      show_root_full_path: false

### Funciones internas

::: backend.api.routers.pipeline._run_pipeline_task
    options:
      show_root_full_path: false

::: backend.api.routers.pipeline._set_state
    options:
      show_root_full_path: false

---

## Analítica - Linaje (`analytics/lineage.py`)

Prefijo: `/api/analytics/lineage`

::: backend.api.routers.analytics.lineage.get_backward_lineage
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.lineage.get_lineage_exact_paths
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.lineage.get_forward_traceability
    options:
      show_root_full_path: false

---

## Analítica - Discrepancias (`analytics/discrepancy.py`)

Prefijo: `/api/analytics/discrepancy-suppliers`

::: backend.api.routers.analytics.discrepancy.get_discrepancy_by_supplier
    options:
      show_root_full_path: false

---

## Analítica - Plazos de entrega (`analytics/lead_time.py`)

Prefijo: `/api/analytics/lead-time`

::: backend.api.routers.analytics.lead_time.get_lead_time_compliance
    options:
      show_root_full_path: false

---

## Analítica - Exposición de pagos (`analytics/payment.py`)

Prefijo: `/api/analytics/payment`

::: backend.api.routers.analytics.payment.get_payment_exposure
    options:
      show_root_full_path: false

---

## Analítica - GDS (`analytics/gds.py`)

Prefijo: `/api/analytics/gds`

::: backend.api.routers.analytics.gds.get_gds_analytics
    options:
      show_root_full_path: false

---

## Analítica - Riesgo (`analytics/risk.py`)

Prefijo: `/api/analytics/risk`

### Endpoints pre-computados

::: backend.api.routers.analytics.risk.get_risk_concentration
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_commercial_impact
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_supplier_score
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_buyer_fragility
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_overdue_exposure
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_contract_profile
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_contract_detail
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_geographic_risk
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_cross_suppliers
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_cross_buyers
    options:
      show_root_full_path: false

### Endpoints en tiempo real (consulta Neo4j)

::: backend.api.routers.analytics.risk.get_buyer_supplier_recommendations
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_supplier_contracts
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_supplier_pair_overdue
    options:
      show_root_full_path: false

::: backend.api.routers.analytics.risk.get_supplier_invoices
    options:
      show_root_full_path: false