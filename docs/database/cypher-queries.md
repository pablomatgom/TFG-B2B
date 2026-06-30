# Consultas Cypher de Referencia

Consultas Cypher organizadas por dominio analítico. Cada bloque corresponde a
un método de `B2BGraphAnalyzer` y al endpoint o fichero de exportación que lo consume.

---

## Trazabilidad documental

### Trazabilidad hacia atrás — factura con discrepancia → pedido original

**Método:** `LineageMixin.get_discrepancy_lineage()`  
**Exportación:** `data/export/data_lineage.json`  
**Endpoint:** `GET /api/analytics/lineage/backward`

```cypher
MATCH (invoice:Document {doc_type: 'INVOICE', discrepancy_flag: true})
MATCH lineage_path = (invoice)-[:FULFILLS*1..5]->(order:Document {doc_type: 'ORDER'})
MATCH (supplier:Company)-[:ISSUES]->(order)-[:SENT_TO]->(buyer:Company)
MATCH (order)-[c:CONTAINS]->(product:Product)
RETURN
    invoice.document_id                     AS factura_id,
    invoice.gross_amount                    AS riesgo_economico,
    order.document_id                       AS pedido_original,
    supplier.legal_name                     AS proveedor,
    buyer.legal_name                        AS afectado,
    collect(DISTINCT product.product_id)    AS id_productos_implicados,
    length(lineage_path)                    AS saltos_topologicos
ORDER BY invoice.gross_amount DESC
```

La cadena estándar tiene dos saltos: `INVOICE → FULFILLS → DESADV → FULFILLS → ORDER`.
El límite `*1..5` cubre cadenas más largas con albaranes intermedios adicionales.

---

### Camino exacto nodo a nodo

**Método:** `LineageMixin.get_exact_paths()`  
**Exportación:** `data/export/exact_paths.json`  
**Endpoint:** `GET /api/analytics/lineage/exact-paths`

```cypher
MATCH (invoice:Document {doc_type: 'INVOICE', discrepancy_flag: true})
MATCH path = (invoice)-[:FULFILLS*1..5]->(order:Document {doc_type: 'ORDER'})
OPTIONAL MATCH (supplier:Company)-[:ISSUES]->(order)
OPTIONAL MATCH (order)-[:SENT_TO]->(buyer:Company)
WITH invoice, order, supplier, buyer,
     length(path) AS hop_count,
     [n IN nodes(path) | {
         id:          n.document_id,
         tipo:        n.doc_type,
         importe:     n.gross_amount,
         discrepancy: n.discrepancy_flag,
         estado:      n.status,
         fecha:       toString(n.issue_date)
     }] AS cadena_completa
ORDER BY invoice.document_id, order.document_id, hop_count ASC
WITH invoice, order, supplier, buyer,
     collect(cadena_completa)[0] AS cadena_completa,
     collect(hop_count)[0]       AS saltos_topologicos
RETURN
    invoice.document_id                          AS factura_id,
    order.document_id                            AS pedido_original,
    coalesce(supplier.legal_name, 'Desconocido') AS proveedor,
    coalesce(buyer.legal_name, 'Desconocido')    AS afectado,
    cadena_completa,
    saltos_topologicos,
    invoice.gross_amount                         AS importe_factura,
    order.gross_amount                           AS importe_pedido
ORDER BY saltos_topologicos DESC, invoice.gross_amount DESC
```

`nodes(path)` devuelve todos los nodos intermedios como lista, permitiendo renderizar
el `ChainDiagram` del frontend con los nodos SVG de cada documento de la cadena.

---

### Trazabilidad hacia adelante — pedido → documentos de cumplimiento

**Método:** `LineageMixin.get_forward_lineage()`  
**Exportación:** `data/export/forward_lineage.json`  
**Endpoint:** `GET /api/analytics/lineage/forward`

```cypher
MATCH (order:Document {doc_type: 'ORDER'})
MATCH (supplier:Company)-[:ISSUES]->(order)-[:SENT_TO]->(buyer:Company)
OPTIONAL MATCH (fulfiller:Document)-[:FULFILLS*1..5]->(order)
WITH order, supplier, buyer,
     collect(DISTINCT CASE WHEN fulfiller IS NOT NULL THEN {
         id:          fulfiller.document_id,
         tipo:        fulfiller.doc_type,
         importe:     fulfiller.gross_amount,
         discrepancy: fulfiller.discrepancy_flag,
         estado:      fulfiller.status
     } END) AS documentos_cumplimiento
RETURN
    order.document_id                AS pedido_id,
    order.gross_amount               AS importe_pedido_eur,
    order.status                     AS estado_pedido,
    supplier.legal_name              AS proveedor,
    buyer.legal_name                 AS comprador,
    size(documentos_cumplimiento)    AS total_docs_cumplimiento,
    documentos_cumplimiento
ORDER BY total_docs_cumplimiento DESC
```

---

## Concentración de riesgo

### Top-N proveedores por grado de salida SUPPLIES

**Método:** `RiskMixin.get_supplier_risk_concentration(top_n=10)`  
**Exportación:** `data/export/risk_concentration.json`  
**Endpoint:** `GET /api/analytics/risk`

```cypher
MATCH ()-[s:SUPPLIES]->()
WITH count(s) AS total_edges
MATCH (sup:Company)-[r:SUPPLIES]->()
WITH sup, count(r) AS supply_degree, total_edges
ORDER BY supply_degree DESC
LIMIT $top_n
RETURN
    sup.legal_name                                   AS supplier,
    supply_degree,
    round(100.0 * supply_degree / total_edges, 2)    AS concentration_pct,
    total_edges
```

El campo `concentration_pct` alimenta el `TreemapChart` de la pestaña Riesgo —
un proveedor con >10 % representa un chokepoint crítico en la red.

---

### Recomendación de proveedores alternativos para un comprador

**Método:** `ScoringMixin.get_buyer_supplier_recommendations(buyer_name)`  
**Endpoint:** `GET /api/analytics/risk/buyer-supplier-recommendations?buyer={name}`

```cypher
MATCH (buyer:Company {legal_name: $buyer_name})
OPTIONAL MATCH (buyer)<-[:SUPPLIES]-(cur:Company)-[:SELLS]->(p:Product)
WITH buyer, collect(DISTINCT p.category) AS sourced_cats

MATCH (pot:Company)
WHERE pot.node_role IN ['SUPPLIER', 'HYBRID']
  AND pot.legal_name <> $buyer_name
  AND NOT (pot)-[:SUPPLIES]->(buyer)

OPTIONAL MATCH (pot)-[:SELLS]->(cp:Product)
WHERE cp.category IN sourced_cats
WITH buyer, sourced_cats, pot, count(DISTINCT cp) AS cat_overlap

OPTIONAL MATCH (pot)-[:SUPPLIES]->(proxy:Company)
WHERE proxy.region = buyer.region
   OR proxy.industry_code = buyer.industry_code
WITH buyer, pot, cat_overlap, count(DISTINCT proxy) AS proximity_count

WHERE cat_overlap > 0 OR proximity_count > 0

OPTIONAL MATCH (pot)-[es:SUPPLIES]->()
WITH pot, cat_overlap, proximity_count,
     count(DISTINCT es)                     AS supply_degree,
     round(avg(es.reliability_score), 3)    AS avg_reliability

RETURN pot.legal_name    AS supplier,
       pot.region        AS region,
       pot.size_band     AS size_band,
       supply_degree,
       avg_reliability,
       cat_overlap,
       proximity_count
ORDER BY avg_reliability DESC, supply_degree DESC
LIMIT 20
```

`cat_overlap` cuenta categorías de producto en común; `proximity_count` mide
proximidad geográfica/sectorial. La combinación filtra candidatos irrelevantes.

---

## Lead time

### Retraso medio por categoría de producto

**Método:** `OperationalMixin.get_lead_time_compliance()`  
**Exportación:** `data/export/lead_time_compliance.json`  
**Endpoint:** `GET /api/analytics/lead-time`

```cypher
MATCH (d:Document {doc_type: 'INVOICE'})-[:CONTAINS]->(p:Product)
WHERE d.lead_time_days IS NOT NULL
  AND p.lead_time_baseline_days IS NOT NULL
WITH p.category AS category,
     d.lead_time_days             AS actual,
     p.lead_time_baseline_days    AS baseline
WITH category,
     round(avg(actual - baseline), 1) AS avg_delay_days,
     count(*)                         AS sample,
     sum(CASE WHEN actual > baseline THEN 1 ELSE 0 END) AS late_count
RETURN category,
       avg_delay_days,
       sample,
       late_count,
       round(100.0 * late_count / sample, 1) AS late_pct
ORDER BY avg_delay_days DESC
```

---

## Pagos y exposición

### Exposición financiera por proveedor (facturas pendientes)

**Método:** `OperationalMixin.get_payment_terms_exposure(top_n=15)`  
**Exportación:** `data/export/payment_exposure.json`  
**Endpoint:** `GET /api/analytics/payment`

```cypher
MATCH (sup:Company)-[:ISSUES]->(inv:Document {doc_type: 'INVOICE'})
WHERE inv.status NOT IN ['PAID', 'CANCELLED']
RETURN
    sup.legal_name                       AS supplier,
    round(sum(inv.total_amount), 2)      AS total_exposure_eur,
    round(avg(inv.payment_terms_days))   AS avg_payment_days,
    count(inv)                           AS invoice_count
ORDER BY total_exposure_eur DESC
LIMIT $top_n
```

---

## Agregación temporal

### Documentos por mes via TimeBucket

**Método:** `MacroMixin.get_temporal_distribution()`  
**Exportación:** `data/export/temporal_series.json`

```cypher
MATCH (d:Document)-[:Issue_on]->(tb:TimeBucket)
WITH tb.year AS year, tb.month AS month,
     count(d)                                              AS documents,
     sum(CASE WHEN d.discrepancy_flag THEN 1 ELSE 0 END)  AS flagged,
     round(sum(d.gross_amount), 2)                        AS gross_eur
ORDER BY year, month
RETURN year, month, documents, flagged, gross_eur
```

Los `TimeBucket` se crean durante la carga (`Neo4jBulkLoader`) usando `MERGE`
sobre la propiedad `date: "YYYY-MM-DD"`, garantizando un único nodo por día.

---

## Graph Data Science (GDS)

Todos los algoritmos GDS siguen el ciclo **project → compute → drop** gestionado
por `GDSMixin._run_gds()`. Si una proyección anterior quedó huérfana (por fallo),
el `CALL gds.graph.drop(..., false)` inicial la limpia sin lanzar error.

### Betweenness centrality — cuellos de botella

**Método:** `GDSMixin.compute_betweenness_centrality()`  
**Exportación:** `data/export/bottlenecks.json`

```cypher
-- Paso 1: crear proyección en memoria
CALL gds.graph.project('b2b_betweenness', 'Company', 'SUPPLIES')
YIELD graphName

-- Paso 2: ejecutar algoritmo
CALL gds.betweenness.stream('b2b_betweenness')
YIELD nodeId, score
WHERE score > 0
WITH gds.util.asNode(nodeId) AS company, score
RETURN company.company_id    AS company_id,
       company.legal_name    AS legal_name,
       company.node_role     AS role,
       score                 AS betweenness_score
ORDER BY score DESC

-- Paso 3: liberar proyección (siempre en bloque finally)
CALL gds.graph.drop('b2b_betweenness', false) YIELD graphName
```

El score normalizado se calcula en Python: `score / ((n-1) * (n-2)) * 100`
donde `n` es el número total de nodos `Company`.

---

### PageRank — influencia estructural

**Método:** `GDSMixin.compute_pagerank()`

```cypher
-- Proyección con peso por volumen acordado
CALL gds.graph.project('b2b_pagerank', 'Company', {
    SUPPLIES: {
        properties: {
            agreed_volume_baseline: { defaultValue: 1.0 }
        }
    }
}) YIELD graphName

-- PageRank ponderado
CALL gds.pageRank.stream('b2b_pagerank', {
    relationshipWeightProperty: 'agreed_volume_baseline'
})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS company, score
RETURN company.company_id    AS company_id,
       company.legal_name    AS legal_name,
       company.node_role     AS role,
       score                 AS pagerank_score
ORDER BY score DESC

CALL gds.graph.drop('b2b_pagerank', false) YIELD graphName
```

---

### Louvain — detección de comunidades

**Método:** `GDSMixin.detect_communities_louvain()`  
**Exportación:** `data/export/communities.json`

```cypher
CALL gds.graph.project('b2b_louvain', 'Company', {
    SUPPLIES: { orientation: 'UNDIRECTED' }
}) YIELD graphName

CALL gds.louvain.stream('b2b_louvain')
YIELD nodeId, communityId
WITH communityId,
     collect(gds.util.asNode(nodeId).legal_name) AS members,
     count(*) AS size
ORDER BY size DESC
RETURN communityId, size, members[0..5] AS sample_members

CALL gds.graph.drop('b2b_louvain', false) YIELD graphName
```

La proyección usa `UNDIRECTED` para que Louvain detecte comunidades basadas en
densidad de interacciones bidireccionales, no en dirección del flujo de suministro.

---

### WCC — componentes débilmente conexas

**Método:** `GDSMixin.get_wcc_stats()`

```cypher
CALL gds.graph.project('b2b_wcc', 'Company', {
    SUPPLIES: { orientation: 'UNDIRECTED' }
}) YIELD graphName

CALL gds.wcc.stream('b2b_wcc')
YIELD nodeId, componentId
WITH componentId, count(*) AS component_size
ORDER BY component_size DESC
WITH collect({ id: componentId, size: component_size }) AS components,
     count(*) AS total_components,
     collect(component_size)[0] AS main_size,
     sum(CASE WHEN component_size = 1 THEN 1 ELSE 0 END) AS isolated
RETURN total_components, main_size, isolated, components

CALL gds.graph.drop('b2b_wcc', false) YIELD graphName
```