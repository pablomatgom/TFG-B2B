# Contratos de API (TypeScript)

Los tipos en `frontend/src/types/` modelan exactamente las respuestas del backend FastAPI.
Cada interfaz tiene un comentario TSDoc en el código fuente que explica su origen y semántica.

---

## `types/auth.ts`

### `TokenPayload`

Estructura del JWT decodificado que devuelve `POST /auth/login`.

| Campo | Tipo | Descripción |
|---|---|---|
| `sub` | `string` | Dirección de email |
| `company_id` | `string` | `company_id` en Neo4j de la empresa del usuario |
| `role` | `"company_user" \| "admin"` | `"admin"` puede acceder a la página Pipeline |
| `full_name` | `string?` | Nombre completo opcional |
| `exp` | `number` | Marca temporal de expiración Unix en segundos |

### `AuthUser`

Vista pública del usuario activo en `AuthContext`. No contiene `exp` y la caducidad se 
verifica una vez al montar y la `max-age` de la cookie impone el límite de 24 h.

| Campo | Tipo | Descripción |
|---|---|---|
| `email` | `string` | Identificador del usuario, coincide con `sub` en `TokenPayload` |
| `company_id` | `string` | Empresa del usuario en el grafo Neo4j |
| `role` | `"company_user" | "admin"` | Controla la visibilidad de ítems admin en el `Sidebar` |
| `full_name` | `string?` | Nombre para mostrar en la UI, puede ser nulo |

---

## `types/pipeline.ts`

### `PipelineFormData`

Cuerpo JSON de `POST /api/pipeline/run`. Debe coincidir con
`PipelineRequest` en `backend/api/models/pipeline.py`.

| Campo | Tipo | Descripción |
|---|---|---|
| `rows` | `number` | Número de empresas (nodos `Company`) a generar |
| `gamma` | `number` | Exponente de la ley de potencias para la distribución de grados del modelo LFR. Debe ser `> 1.0` |
| `beta` | `number` | Exponente de la ley de potencias para el tamaño de las comunidades LFR. Debe ser `> 1.0` |
| `mu` | `number` | Coeficiente de mezcla LFR para la conexión inter-comunidad. Debe ser `0 ≤ mu < 1.0` |
| `min_comm` / `max_comm` | `number` | Límites del tamaño de comunidad (empresas por clúster) |
| `avg_degree_supplies` | `number` | Grado medio de la red de suministro (aristas `SUPPLIES`) |
| `avg_degree_documents` | `number` | Grado medio de documentos EDI por par proveedor-comprador activo |
| `avg_degree_products` | `number` | Número medio de productos distintos que vende cada empresa proveedora (aristas `SELLS`) |
| `batch_size` | `number` | Tamaño del lote para la carga en Neo4j. Valores menores reducen RAM pero aumentan el número de transacciones |
| `clear_db` | `boolean` | Si `true`, borra todos los nodos y aristas antes de cargar, garantizando una base de datos limpia |
| `use_random_seed` | `boolean` | Si `true`, ignora `seed_value` y usa una semilla aleatoria no determinada |
| `seed_value` | `number?` | Semilla fija para reproducción exacta del grafo. Solo aplica cuando `use_random_seed` es `false` |

### `StatusState`

Estado del indicador de ejecución de la UI en `InfrastructureSection`.

| Campo | Tipo | Descripción |
|---|---|---|
| `type` | `"success" | "error" | null` | `null` mientras no se ha ejecutado; `"success"` o `"error"` tras la ejecución |
| `msg` | `string` | Mensaje descriptivo del resultado |

---

## `types/dashboard.ts`

Modela la respuesta de `GET /api/dashboard/macro` → `DashboardResponse`.

### `MacroStats`

| Campo | Tipo | Descripción |
|---|---|---|
| `node_counts` | `Record<string, number>` | Conteos por etiqueta: `{ Company, Product, Document, TimeBucket }` |
| `relationship_counts` | `Record<string, number>` | Conteos por tipo de relación: `{ SUPPLIES, SELLS, ISSUES, … }` |
| `top_suppliers` | `object[]` | Top proveedores por `supplies_out` (aristas SUPPLIES de salida) |
| `top_buyers` | `object[]` | Top compradores por `supplies_in` (aristas SUPPLIES de entrada) |
| `doc_type_counts` | `Record<string, number>` | Conteos por `doc_type`: `{ ORDER, INVOICE, SHIPMENT, CREDIT_NOTE }` |
| `economic_volume` | `object` | `invoice_count`, `total_gross_eur`, `total_tax_eur`, `total_net_eur` |
| `document_health` | `object` | `flagged_documents` y `overall_discrepancy_rate_pct` |
| `scale_free_metrics` | `Partial<ScaleFreeMetrics>` | Objeto vacío `{}` si no hay aristas SUPPLIES |

### `ScaleFreeMetrics`

| Campo | Tipo | Descripción |
|---|---|---|
| `node_count` | `number` | Total de nodos `Company` en el grafo |
| `mean_degree` | `number` | Grado medio de la distribución de aristas `SUPPLIES` |
| `median_degree` | `number` | Mediana del grado. Menos sensible a hubs que la media |
| `std_degree` | `number` | Desviación típica del grado |
| `max_degree` | `number` | Grado máximo (el hub más conectado) |
| `min_degree` | `number` | Grado mínimo |
| `gini_coefficient` | `number` | Coeficiente de Gini de la distribución de grados (0 = igualdad, 1 = máxima concentración) |
| `hub_count` | `number` | Nodos cuyo grado supera `hub_threshold` |
| `hub_threshold` | `number` | Umbral a partir del cual un nodo se clasifica como hub |
| `max_mean_ratio` | `number` | `max_degree / mean_degree` valores altos confirman topología libre de escala |

### `TemporalSeriesRow`

Una fila por mes natural. Generada por `MacroMixin.get_temporal_distribution()` vía `Issue_on → TimeBucket`.

| Campo | Tipo | Descripción |
|---|---|---|
| `year` | `number` | Año natural |
| `month` | `number` | Mes (1–12) |
| `documents` | `number` | Total de documentos emitidos en el mes |
| `flagged` | `number` | Documentos del mes con `discrepancy_flag = true` |
| `total_gross_eur` | `number` | Suma de `gross_amount` de todos los documentos del mes |
| `active_companies` | `number` | Empresas con al menos un documento en el mes |
| `active_products` | `number` | Productos referenciados en documentos del mes |
| `active_connections` | `number` | Pares proveedor-comprador activos en el mes |
| `date?` | `string?` | Calculado por el frontend para los ejes del gráfico |

---

## `types/analytics.ts`

Agrupa todos los contratos de las 7 pestañas de analítica.

### Contratos (tab 0)

**`ContractProfileData`** - Perfil agregado de contratos de toda la red.

| Campo | Tipo | Descripción |
|---|---|---|
| `contract_type_distribution` | `Record<string, number>` | Conteo de aristas SUPPLIES por tipo de contrato |
| `exclusivity_pct` | `number` | % de relaciones de suministro marcadas como exclusivas |
| `avg_reliability_score` | `number` | Fiabilidad media de todos los proveedores |
| `avg_payment_terms_days` | `number` | Plazo de pago medio acordado en días |
| `avg_contract_age_days` | `number` | Antigüedad media de las relaciones de suministro en días |

**`ContractDetailRow`** - Detalle de contratos por proveedor.

| Campo | Tipo | Descripción |
|---|---|---|
| `supplier` | `string` | Nombre legal del proveedor |
| `region` | `string` | Comunidad Autónoma del proveedor |
| `total_contracts` | `number` | Número total de aristas SUPPLIES del proveedor |
| `contract_types` | `string[]` | Tipos de contrato distintos que mantiene |
| `exclusive_contracts` | `number` | Contratos marcados como exclusivos |
| `exclusive_pct` | `number` | `exclusive_contracts / total_contracts * 100` |
| `avg_reliability` | `number` | Fiabilidad media ponderada |
| `avg_payment_terms_days` | `number` | Plazo de pago medio acordado |

**`SupplierContractRow`** - Una arista SUPPLIES individual con sus condiciones.

| Campo | Tipo | Descripción |
|---|---|---|
| `buyer` | `string` | Nombre del comprador en la relación |
| `buyer_region` | `string?` | Comunidad Autónoma del comprador |
| `contract_type` | `string` | Tipo de contrato: `SPOT`, `FRAME`, `CONSIGNMENT`, etc. |
| `is_exclusive` | `boolean` | Si la relación es de exclusividad |
| `reliability_score` | `number` | Puntuación de fiabilidad de esta relación |
| `payment_terms_days` | `number` | Días de pago acordados |
| `agreed_volume_eur` | `number` | Volumen comprometido en euros |
| `since_date` | `string?` | Fecha de inicio de la relación |

**`BuyerSupplierRecommendationRow`** - Candidato recomendado para diversificar proveedores.

| Campo | Tipo | Descripción |
|---|---|---|
| `supplier` | `string` | Nombre del proveedor candidato |
| `region` | `string?` | Comunidad Autónoma |
| `size_band` | `string?` | Tamaño de empresa: `micro`, `pyme`, `mid`, `enterprise` |
| `industry_code` | `string?` | Código NACE del sector |
| `supply_degree` | `number` | Número de compradores actuales del candidato |
| `avg_reliability` | `number` | Fiabilidad media del candidato |
| `cat_overlap` | `number` | Categorías de producto compartidas con el comprador |
| `proximity_count` | `number` | Compradores comunes con el comprador actual |

---

### Riesgo (tab 1)

**`RiskData`** - Concentración de riesgo de la red de suministro.

| Campo | Tipo | Descripción |
|---|---|---|
| `total_supplies_edges` | `number` | Total de aristas SUPPLIES en el grafo |
| `top_n` | `number` | Número de proveedores analizados |
| `concentration_pct` | `number` | % del total de aristas que concentran los `top_n` proveedores |
| `top_suppliers` | `{ name, degree, share_pct }[]` | Detalle de cada proveedor dominante |

**`SupplierScoreRow`** - Puntuación de riesgo compuesta por proveedor.

| Campo | Tipo | Descripción |
|---|---|---|
| `supplier` | `string` | Nombre legal del proveedor |
| `avg_reliability` | `number` | Fiabilidad media (mayor = mejor) |
| `discrepancy_pct` | `number` | % de facturas con discrepancia |
| `late_pct` | `number` | % de entregas con retraso |
| `supply_degree` | `number` | Número de compradores activos |
| `risk_score` | `number` | Puntuación compuesta - mayor valor indica mayor riesgo |
| `overdue_count` | `number` | Facturas vencidas sin cobrar |
| `overdue_eur` | `number` | Importe total vencido en euros |

**`BuyerFragilityRow`** - Fragilidad de un comprador por concentración en pocos proveedores.

| Campo | Tipo | Descripción |
|---|---|---|
| `buyer` | `string` | Nombre legal del comprador |
| `node_role` | `string` | Rol en el grafo: `BUYER` o `HYBRID` |
| `region` | `string` | Comunidad Autónoma |
| `supplier_count` | `number` | Número de proveedores activos |
| `top_supplier_pct` | `number` | % del volumen total que proviene del mayor proveedor |
| `total_volume_eur` | `number` | Volumen total recibido en euros |
| `overdue_received` | `number` | Facturas vencidas recibidas |
| `overdue_eur` | `number` | Importe vencido recibido en euros |

**`GeographicRiskRow`** - Riesgo agregado por Comunidad Autónoma.

| Campo | Tipo | Descripción |
|---|---|---|
| `region` | `string` | Comunidad Autónoma |
| `supplier_count` | `number` | Proveedores en la región |
| `avg_reliability` | `number` | Fiabilidad media regional |
| `total_invoices` | `number` | Facturas emitidas desde la región |
| `discrepancy_pct` | `number` | % de facturas con discrepancia en la región |

---

### Discrepancias (tab 2)

**`DiscrepancyRow`** - Tasa de discrepancia por proveedor.

| Campo | Tipo | Descripción |
|---|---|---|
| `supplier` | `string` | Nombre del proveedor |
| `total` | `number` | Total de facturas emitidas |
| `flagged` | `number` | Facturas con `discrepancy_flag = true` |
| `discrepancy_rate_pct` | `number` | `flagged / total * 100` |

**`CommercialImpactRow`** - Comparativa pedido vs. facturas para un par proveedor-comprador.

| Campo | Tipo | Descripción |
|---|---|---|
| `pedido_id` | `string` | ID del pedido de referencia |
| `proveedor` | `string` | Nombre del proveedor |
| `comprador` | `string` | Nombre del comprador |
| `importe_pedido_eur` | `number` | Importe del pedido original |
| `total_facturado_eur` | `number` | Suma de todas las facturas asociadas |
| `delta_eur` | `number` | `total_facturado_eur - importe_pedido_eur` |
| `delta_pct` | `number?` | Variación porcentual respecto al pedido |
| `num_facturas` | `number` | Número de facturas asociadas al pedido |
| `facturas_con_discrepancia` | `number` | Facturas con `discrepancy_flag = true` |
| `importe_en_discrepancia_eur` | `number` | Importe total de las facturas discrepantes |
| `estado_comercial` | `"SOBREFACTURADO" \| "SUBFACTURADO" \| "CONFORME"` | Clasificación del impacto |

---

### Lead Time (tab 3)

**`LeadTimeRow`** - Cumplimiento de plazos de entrega por categoría de producto.

| Campo | Tipo | Descripción |
|---|---|---|
| `category` | `string` | Categoría del producto |
| `avg_delay_days` | `number` | Retraso medio en días (negativo = entrega anticipada) |
| `sample` | `number` | Total de entregas analizadas |
| `late_count` | `number` | Entregas con retraso positivo |
| `late_pct` | `number` | `late_count / sample * 100` |

---

### Exposición (tab 4)

**`PaymentRow`** - Exposición económica por proveedor con facturas pendientes.

| Campo | Tipo | Descripción |
|---|---|---|
| `supplier` | `string` | Nombre del proveedor |
| `total_exposure_eur` | `number` | Suma de facturas con estado ∉ `{PAID, CANCELLED}` |
| `avg_payment_days` | `number` | Días de pago medio real observado |
| `avg_agreed_days` | `number` | Días de pago medio contractual |
| `invoice_count` | `number` | Número de facturas pendientes |

**`OverdueRow`** - Facturas vencidas por par proveedor-comprador.

| Campo | Tipo | Descripción |
|---|---|---|
| `supplier` | `string` | Nombre del proveedor |
| `buyer` | `string` | Nombre del comprador |
| `overdue_invoices` | `number` | Número de facturas vencidas |
| `total_overdue_eur` | `number` | Importe total vencido en euros |
| `avg_payment_days` | `number` | Días de pago medio observado |
| `avg_agreed_days` | `number` | Días de pago medio acordado |

**`SupplierInvoiceRow`** - Factura individual en el drill-down del tab de Exposición.

| Campo | Tipo | Descripción |
|---|---|---|
| `document_id` | `string` | ID del documento |
| `buyer` | `string` | Nombre del comprador receptor |
| `gross_amount` | `number` | Importe bruto en euros |
| `status` | `string` | Estado del documento |
| `payment_terms_days` | `number` | Días de pago acordados |
| `due_date` | `string?` | Fecha de vencimiento |
| `issue_date` | `string?` | Fecha de emisión |
| `discrepancy_flag` | `boolean` | Si la factura tiene discrepancia registrada |

---

### Trazabilidad (tab 5)

**`LineageRow`** - Traza backward: factura con discrepancia → pedido de origen.

| Campo | Tipo | Descripción |
|---|---|---|
| `factura_id` | `string` | ID de la factura discrepante |
| `riesgo_economico` | `number` | Importe en riesgo en euros |
| `pedido_original` | `string` | ID del pedido de origen |
| `proveedor` | `string` | Nombre del proveedor emisor |
| `afectado` | `string` | Nombre del comprador receptor |
| `id_productos_implicados` | `string[]` | IDs de productos en la cadena |
| `saltos_topologicos` | `number` | Número de saltos FULFILLS (normalmente 2) |

**`ChainNode`** - Un nodo dentro del camino FULFILLS.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `string` | ID del documento |
| `tipo` | `string` | `ORDER`, `INVOICE`, `SHIPMENT` o `CREDIT_NOTE` |
| `importe` | `number?` | Importe del documento; `null` si no aplica |
| `discrepancy` | `boolean` | Si el documento tiene `discrepancy_flag = true` |
| `estado` | `string?` | Estado del documento; `null` si no está definido |
| `fecha` | `string?` | Fecha de emisión; `null` si no está disponible |

**`ExactPathRow`** - Camino completo nodo a nodo desde factura hasta pedido.

| Campo | Tipo | Descripción |
|---|---|---|
| `factura_id` | `string` | ID de la factura de origen |
| `pedido_original` | `string` | ID del pedido de destino |
| `proveedor` | `string` | Nombre del proveedor |
| `afectado` | `string` | Nombre del comprador |
| `cadena_completa` | `ChainNode[]` | Secuencia ordenada de nodos del camino |
| `saltos_topologicos` | `number` | Longitud del camino en saltos FULFILLS |
| `importe_factura` | `number` | Importe de la factura de origen |
| `importe_pedido` | `number` | Importe del pedido de destino |

**`ForwardRow`** - Traza forward: pedido → documentos de cumplimiento.

| Campo | Tipo | Descripción |
|---|---|---|
| `pedido_id` | `string` | ID del pedido de origen |
| `importe_pedido_eur` | `number` | Importe del pedido |
| `estado_pedido` | `string?` | Estado del pedido |
| `proveedor` | `string` | Nombre del proveedor |
| `comprador` | `string` | Nombre del comprador |
| `total_docs_cumplimiento` | `number` | Documentos generados a partir del pedido |
| `docs_con_discrepancia` | `number` | Documentos de cumplimiento con discrepancia |
| `documentos_cumplimiento` | `ForwardDoc[]` | Secuencia de documentos de cumplimiento |

`ForwardDoc` es `ChainNode` sin el campo `fecha` (`Omit<ChainNode, "fecha">`).

---

### GDS (tab 6)

**`GdsData`** - Resultados combinados de los 4 algoritmos GDS.

| Campo | Tipo | Descripción |
|---|---|---|
| `bottlenecks` | `object[]` | Top nodos por betweenness: `company_id`, `legal_name`, `role`, `betweenness_score`, `normalized_pct` |
| `communities` | `object[]` | Comunidades Louvain: `communityId`, `total_empresas`, `ejemplos_empresas` |
| `pagerank` | `object[]` | Top nodos por PageRank: `company_id`, `legal_name`, `role`, `pagerank_score` |
| `wcc` | `WccData` | Resultados de componentes débilmente conexas |

**`WccData`** - Componentes débilmente conexas del grafo.

| Campo | Tipo | Descripción |
|---|---|---|
| `total_components` | `number` | Número total de componentes en el grafo |
| `main_component_size` | `number` | Número de nodos en la componente principal |
| `main_component_pct` | `number` | % de nodos en la componente principal (≥ 95 % = red bien conectada) |
| `isolated_nodes` | `number` | Nodos sin ninguna conexión |
| `components` | `{ component_id, size }[]` | Detalle de todas las componentes |
