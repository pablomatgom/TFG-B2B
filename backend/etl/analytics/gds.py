from __future__ import annotations

from typing import Any
import pandas as pd


class GDSMixin:
    """Algoritmos de Graph Data Science sobre la red SUPPLIES de empresas."""

    def _run_gds(self, graph_name: str, project_q: str, compute_q: str) -> list[dict[str, Any]]:
        """Ejecuta el ciclo completo project → compute → drop en una sola sesión Neo4j.
        
        Args:
            graph_name: Nombre único para la proyección en memoria de GDS.
            project_q: Sentencia Cypher ``CALL gds.graph.project(...)`` que crea la proyección en memoria del subgrafo.
            compute_q: Sentencia Cypher ``CALL gds.<algoritmo>.stream(...)`` que ejecuta sobre la proyección y transmite los resultados.

        Returns:
            Resultados de la consulta Cypher (un diccionario por fila):
                
                * **Claves:** Los alias definidos en el ``RETURN``.
                * **Valores:** Los tipos de datos nativos mapeados automáticamente por el driver.
                
                Ejemplo para ``compute_betweenness_centrality``:

                    [{"company_id": "C01", "legal_name": "Acme S.L.", "betweenness_score": 42.0}, …]
        
        Note:
            El drop inicial limpia proyecciones huérfanas de ejecuciones anteriores fallidas 
            por SO mientras que el drop final corre siempre en un bloque ``finally`` 
            para garantizar limpieza ante fallos internos.
        """
        drop_q = f"CALL gds.graph.drop('{graph_name}', false) YIELD graphName"
        with self._driver.session(database=self.neo4j_database) as s:
            s.run(drop_q)
            s.run(project_q)
            try:
                records = [r.data() for r in s.run(compute_q)]
            finally:
                s.run(drop_q)
        return records

    # ── Centralidad ──────────────────────────────────────────────────────────

    def compute_betweenness_centrality(self) -> pd.DataFrame:
        r"""Identifica empresas que actúan como cuellos de botella en la red de suministro.

        Returns:
            DataFrame con una fila por empresa intermediaria y las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``company_id`` | str | Identificador único interno |
                | ``legal_name`` | str | Razón social de la empresa |
                | ``role`` | str | ``SUPPLIER``, ``BUYER`` o ``HYBRID`` |
                | ``betweenness_score`` | float | Nº de caminos mínimos que pasan por este nodo |
                | ``normalized_pct`` | float | Score como % del máximo teórico para el grafo dirigido |

        Notes:
            **Cálculo y Normalización:**
            El score bruto de GDS cuenta cuántos caminos mínimos entre pares de nodos 
            pasan a través de cada empresa. Se normaliza mediante la fórmula estándar 
            para grafos dirigidos:

            $$\text{normalized_pct} = \frac{\text{score}}{(n-1)(n-2)} \times 100$$

            donde $n$ es el número total de nodos ``Company``. 
            
            **Criterio de Exclusión:**
            Solo se devuelven empresas con score > 0, excluyendo los nodos hoja puros 
            (un único proveedor o un único comprador) al carecer de rol intermediario.

            **Proyección del Grafo:**
            Se utiliza una orientación estrictamente dirigida (``SUPPLIES`` conserva 
            el sentido proveedor → comprador). Esto captura la asimetría de la red, 
            haciendo que un nodo que conecte proveedores upstream con compradores 
            downstream obtenga mayor puntuación que uno conectando nodos del mismo nivel.
        """
        graph_name = "b2b_betweenness"

        project_q = f"CALL gds.graph.project('{graph_name}', 'Company', 'SUPPLIES') YIELD graphName"

        compute_q = f"""
            CALL gds.betweenness.stream('{graph_name}')
            YIELD nodeId, score
            WHERE score > 0
            WITH gds.util.asNode(nodeId)    AS company, score
            RETURN company.company_id       AS company_id,
                   company.legal_name       AS legal_name,
                   company.node_role        AS role,
                   score                    AS betweenness_score
            ORDER BY score DESC
        """

        with self._driver.session(database=self.neo4j_database) as s:
            n = s.run("MATCH (c:Company) RETURN count(c) AS n").single()["n"]
        # Count is fetched before _run_gds because _run_gds uses its own session.
        max_possible = (n - 1) * (n - 2) if n > 2 else 1

        df = pd.DataFrame(self._run_gds(graph_name, project_q, compute_q))
        if not df.empty:
            df["normalized_pct"] = (df["betweenness_score"] / max_possible * 100).round(2)
        return df

    def compute_pagerank(self) -> pd.DataFrame:
        """Detecta proveedores con alta influencia estructural en la red.

        Returns:
            DataFrame ordenado de mayor a menor ``pagerank_score`` con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``company_id`` | str | Identificador único interno |
                | ``legal_name`` | str | Razón social de la empresa |
                | ``role`` | str | ``SUPPLIER``, ``BUYER`` o ``HYBRID`` |
                | ``pagerank_score`` | float | Score de influencia estructural (no acotado) |

        Notes:
            **Propagación de Influencia (PageRank):**
            El algoritmo propaga la importancia a través de los enlaces ``SUPPLIES``. 
            Un proveedor que abastece a muchos compradores relevantes recibe un score 
            alto, incluso si su grado directo (número de clientes) es moderado. 
            
            **Ponderación de Aristas:**
            Las relaciones se ponderan mediante el atributo ``agreed_volume_baseline`` 
            para que los suministros de mayor volumen contribuyan proporcionalmente 
            más al cálculo de influencia.
            
            **Tolerancia a Datos Incompletos:**
            La proyección del grafo asigna ``defaultValue: 1.0`` como fallback para 
            las aristas ``SUPPLIES`` que carezcan de volumen definido, evitando fallos 
            de proyección en el motor GDS.
        """
        graph_name = "b2b_pagerank"

        project_q = f"""
            CALL gds.graph.project('{graph_name}', 'Company',{{
                SUPPLIES: {{
                    properties: {{
                        agreed_volume_baseline: {{
                            defaultValue: 1.0
                        }}
                    }}
                }}
            }}
            ) YIELD graphName
        """

        compute_q = f"""
            CALL gds.pageRank.stream('{graph_name}', {{ relationshipWeightProperty: 'agreed_volume_baseline' }})
            YIELD nodeId, score
            WITH gds.util.asNode(nodeId)    AS company, score
            RETURN company.company_id       AS company_id,
                   company.legal_name       AS legal_name,
                   company.node_role        AS role,
                   score                    AS pagerank_score
            ORDER BY score DESC
        """
        return pd.DataFrame(self._run_gds(graph_name, project_q, compute_q))

    # ── Comunidades ──────────────────────────────────────────────────────────

    def detect_communities_louvain(self) -> pd.DataFrame:
        """Detecta ecosistemas industriales y clústeres de empresas densamente interconectadas.
        
        Returns:
            DataFrame ordenado de mayor a menor ``total_empresas`` con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``communityId`` | int | ID interno de GDS (no estable entre ejecuciones) |
                | ``total_empresas`` | int | Número de empresas en el clúster |
                | ``ejemplos_empresas`` | list[dict] | Datos detallados (nombre, rol, región, etc.) de las empresas del clúster |

        Notes:
            **Maximización de Modularidad (Louvain):**
            El algoritmo agrupa nodos mediante una búsqueda heurística iterativa que 
            maximiza la modularidad de la red. Cada comunidad detectada representa 
            una cadena de suministro cohesionada o un ecosistema logístico propio.
            
            **Proyección del Grafo (UNDIRECTED):**
            La proyección fuerza la orientación ``UNDIRECTED`` en las relaciones 
            ``SUPPLIES``. El algoritmo de Louvain requiere un grafo no dirigido para 
            calcular la modularidad de forma matemáticamente correcta, priorizando 
            la cohesión estructural del grupo por encima de la direccionalidad del 
            flujo comercial.

            **Ponderación de Aristas:**
            Al igual que en otros algoritmos de influencia, las conexiones utilizan 
            ``agreed_volume_baseline`` como peso (con un valor por defecto de 1.0) 
            para que los flujos de mayor volumen consoliden mejor las comunidades.
        """
        graph_name = "b2b_louvain"

        project_q = f"""
            CALL gds.graph.project('{graph_name}', 'Company',{{
                SUPPLIES: {{
                    orientation: 'UNDIRECTED',
                    properties: {{
                        agreed_volume_baseline: {{
                            defaultValue: 1.0
                        }}
                    }}
                }}
            }}
            ) YIELD graphName
        """

        compute_q = f"""
            CALL gds.louvain.stream('{graph_name}', {{ relationshipWeightProperty: 'agreed_volume_baseline' }})
            YIELD nodeId, communityId
            WITH gds.util.asNode(nodeId)                AS company, 
                communityId
            RETURN communityId,
                   count(company)                       AS total_empresas,
                   collect({{
                        name:   company.legal_name,
                        role:   company.node_role,
                        region: company.region,
                        band:   company.size_band,
                        sector: company.industry_code
                   }})                                  AS ejemplos_empresas
            ORDER BY total_empresas DESC
        """
        return pd.DataFrame(self._run_gds(graph_name, project_q, compute_q))

    # ── Conectividad ─────────────────────────────────────────────────────────

    def detect_weakly_connected_components(self) -> dict:
        """Evalúa la salud estructural y la cohesión de la red detectando su nivel de fragmentación.

        Returns:
            Diccionario con las claves:

                | Clave | Tipo | Descripción |
                |---|---|---|
                | ``total_components`` | int | Número total de componentes detectados |
                | ``main_component_size`` | int | Nº de empresas en el componente más grande |
                | ``main_component_pct`` | float | % de la red cubierto por el componente principal |
                | ``isolated_nodes`` | int | Empresas completamente desconectadas (componentes de tamaño 1) |
                | ``components`` | list[dict] | Lista completa ``[{component_id, size}, …]`` |

        Notes:
            **Algoritmo WCC (Weakly Connected Components):**
            Agrupa nodos que están conectados entre sí ignorando la dirección de los 
            enlaces. Evalúa la topología puramente en base a la existencia de caminos.

            **Proyección del Grafo (UNDIRECTED):**
            Se utiliza una proyección no dirigida, ya que WCC busca responder a la 
            pregunta «¿existe algún camino entre estos dos nodos?» sin importar si el 
            flujo comercial es de compra o de venta.

            **Diagnóstico de Salud Estructural:**
            Una red sana presenta un componente principal masivo y muy pocos nodos 
            aislados. Un valor de ``main_component_pct`` > 90 % se considera indicativo 
            de una red altamente cohesionada. Por el contrario, la presencia de múltiples 
            componentes pequeños evidencia una fragmentación severa que limita la 
            propagación de información o riesgo, lo que requiere investigar los nodos 
            desconectados.
        """
        graph_name = "b2b_wcc"

        project_q = f"""
            CALL gds.graph.project('{graph_name}', 'Company',
                {{ SUPPLIES: {{ orientation: 'UNDIRECTED' }} }}
            ) YIELD graphName
        """

        compute_q = f"""
            CALL gds.wcc.stream('{graph_name}')
            YIELD nodeId, componentId
            RETURN componentId, count(nodeId)   AS size
            ORDER BY size DESC
        """
        rows = self._run_gds(graph_name, project_q, compute_q)

        if not rows:
            return {}

        total_nodes = sum(r["size"] for r in rows)
        main_size = rows[0]["size"]
        isolated_nodes = sum(1 for r in rows if r["size"] == 1)

        return {
            "total_components":    len(rows),
            "main_component_size": main_size,
            "main_component_pct":  round(main_size / total_nodes * 100, 1) if total_nodes else 0.0,
            "isolated_nodes":      isolated_nodes,
            "components": [
                {"component_id": r["componentId"], "size": r["size"]}
                for r in rows
            ],
        }