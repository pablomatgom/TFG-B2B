from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import read_json

router = APIRouter(prefix="/gds")


@router.get("")
def get_gds_analytics() -> dict:
    """Resultados de los algoritmos de Graph Data Science (GDS) de Neo4j.

    Agrega en una sola respuesta los cuatro análisis de grafo pre-computados:
    betweenness centrality, detección de comunidades Louvain, PageRank y
    componentes débilmente conectadas (WCC).

    Returns:
        Claves ``bottlenecks``, ``communities``, ``pagerank`` y ``wcc``,
            cada una con el contenido de su JSON exportado.
    """
    return {
        "bottlenecks": read_json("bottlenecks.json", default=[]),
        "communities": read_json("communities.json", default=[]),
        "pagerank":    read_json("pagerank.json",    default=[]),
        "wcc":         read_json("wcc.json",         default={}),
    }