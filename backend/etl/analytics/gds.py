from __future__ import annotations

from typing import Any
import pandas as pd


class GDSMixin:
    """Algoritmos de Graph Data Science sobre la red SUPPLIES de empresas."""

    def _run_gds(self, graph_name: str, project_q: str, compute_q: str) -> list[dict[str, Any]]:
        """Ejecuta el ciclo completo project → compute → drop en una sola sesión Neo4j.

        - El drop inicial limpia proyecciones huérfanas de ejecuciones anteriores fallidas por SO.
        - El drop final corre siempre en un bloque ``finally`` para garantizar limpieza ante fallos internos.
        
        Args:
            graph_name: Nombre único para la proyección en memoria de GDS.
            project_q: Sentencia Cypher ``CALL gds.graph.project(...)`` que crea la proyección en memoria del subgrafo.
            compute_q: Sentencia Cypher ``CALL gds.<algoritmo>.stream(...)`` que ejecuta sobre la proyección y transmite los resultados.

        Returns:
            Resultados de la consulta Cypher (un diccionario por fila):
                
                * Claves: Los alias definidos en el ``RETURN``.
                * Valores: Tipos de datos nativos mapeados automáticamente por el driver.
                
                Ejemplo para ``compute_betweenness_centrality``:

                    [{"company_id": "C01", "legal_name": "Acme S.L.", "betweenness_score": 42.0}, …]
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

        El *score* bruto de GDS cuenta cuántos caminos mínimos entre pares de nodos pasan 
        a través de cada empresa. Se normaliza con la fórmula estándar para grafos dirigidos:

        $$\text{normalized_pct} = \frac{\text{score}}{(n-1)(n-2)} \times 100$$

        donde $n$ es el número total de nodos ``Company``. 
        
        Solo se devuelven empresas con
        score > 0 por lo que los nodos hoja puros (un único proveedor o un único comprador) no tienen
        rol de intermediario y se excluyen.

        Returns:
            DataFrame con una fila por empresa intermediaria y las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``company_id`` | str | Identificador único interno |
                | ``legal_name`` | str | Razón social de la empresa |
                | ``role`` | str | ``SUPPLIER``, ``BUYER`` o ``HYBRID`` |
                | ``betweenness_score`` | float | Nº de caminos mínimos que pasan por este nodo |
                | ``normalized_pct`` | float | Score como % del máximo teórico para el grafo dirigido |

        Note:
            La proyección usa orientación **dirigida** (``SUPPLIES`` conserva su sentido
            proveedor → comprador). Esto captura asimetría por lo que una empresa que conecta
            proveedores upstream con compradores downstream puntúa más que una que solo
            conecta pares al mismo nivel.
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
        """Detecta proveedores con alta influencia estructural.
        
        PageRank propaga importancia a través de los enlaces ``SUPPLIES``, done un proveedor
        que abastece a muchos compradores relevantes recibe un score alto aunque su grado
        directo sea moderado. Las aristas se ponderan por ``agreed_volume_baseline`` para
        que las relaciones de mayor volumen contribuyan más al cálculo.

        Returns:
            DataFrame ordenado de mayor a menor ``pagerank_score`` con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``company_id`` | str | Identificador único interno |
                | ``legal_name`` | str | Razón social de la empresa |
                | ``role`` | str | ``SUPPLIER``, ``BUYER`` o ``HYBRID`` |
                | ``pagerank_score`` | float | Score de influencia estructural (no acotado) |

        Note:
            El peso ``agreed_volume_baseline`` usa ``defaultValue: 1.0`` como fallback
            para aristas ``SUPPLIES`` que no tengan ese atributo, evitando fallos de
            proyección en grafos con datos incompletos.
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
        
        Louvain maximiza la **modularidad** de la red mediante una búsqueda heurística
        iterativa que agrupa nodos densamente interconectados. Cada comunidad resultante
        representa una cadena de suministro cohesionada o un ecosistema logístico propio.
        
        Returns:
            DataFrame ordenado de mayor a menor ``total_empresas`` con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``communityId`` | int | ID interno de GDS (no estable entre ejecuciones) |
                | ``total_empresas`` | int | Número de empresas en el clúster |
                | ``ejemplos_empresas`` | list[str] | Razones sociales de todas las empresas del clúster |

        Note:
            La proyección usa orientación ``UNDIRECTED`` porque Louvain requiere un grafo
            no dirigido por lo que cada arista ``SUPPLIES`` se trata como bidireccional a 
            efectos del cálculo de modularidad, lo que es correcto para detectar ecosistemas
            donde la dirección del flujo comercial es menos relevante que la cohesión del grupo.
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
        """Evalúa la salud estructural y la cohesión de la red detectando fragmentación en islas.

        WCC (Weakly Connected Components) agrupa nodos que están conectados ignorando
        la dirección de los enlaces. Una red sana presenta un componente principal grande
        y pocos nodos aislados; muchos componentes pequeños indican fragmentación severa
        que limita la propagación de información o riesgo.

        Returns:
            Diccionario con las claves:

                | Clave | Tipo | Descripción |
                |---|---|---|
                | ``total_components`` | int | Número total de componentes detectados |
                | ``main_component_size`` | int | Nº de empresas en el componente más grande |
                | ``main_component_pct`` | float | % de la red cubierto por el componente principal |
                | ``isolated_nodes`` | int | Empresas completamente desconectadas (componentes de tamaño 1) |
                | ``components`` | list[dict] | Lista completa ``[{component_id, size}, …]`` |

        Note:
            La proyección es ``UNDIRECTED`` porque WCC pregunta únicamente «¿existe
            algún camino entre estos dos nodos?», sin importar la dirección del flujo.
            Un ``main_component_pct`` > 90 % se considera red cohesionada; por debajo
            de ese umbral conviene investigar proveedores o compradores sin conexiones.
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