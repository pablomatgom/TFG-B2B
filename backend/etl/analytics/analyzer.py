from __future__ import annotations

import logging
import textwrap
from typing import Any

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError

from backend.etl.analytics.macro_stats   import MacroMixin
from backend.etl.analytics.traceability  import LineageMixin
from backend.etl.analytics.gds           import GDSMixin
from backend.etl.analytics.risk          import RiskMixin

logger = logging.getLogger(__name__)

        
def _report_query_error(kind: str, code: str | None,
                        message: str, query: str, params: dict) -> None:
    """Formatea y registra los detalles completos de un fallo de consulta Neo4j.

    Centraliza el formato del mensaje de error para que todos los fallos de ``_fetch_data``
    produzcan entradas de log homogéneas con contexto suficiente para reproducir el fallo.

    Args:
        kind: Tipo de error (``"Neo4j"`` para ``Neo4jError``, nombre de clase para el resto).
        code: Código de error Neo4j (``Neo4jError.code``); ``None`` si no aplica.
        message: Mensaje de error sin procesar.
        query: Sentencia Cypher que provocó el fallo.
        params: Parámetros pasados a la consulta.
    """
    code_suffix = f" [{code}]" if code else ""
    clean_query = textwrap.dedent(query).strip()
    
    log_message = (
        f"Query execution failed in analyzer ({kind}){code_suffix}\n"
        f"  Detail: {message}\n"
        f"  Params: {params}\n"
        f"  Query :\n{textwrap.indent(clean_query, '    ')}"
    )
    
    logger.error(log_message)


class B2BGraphAnalyzer(MacroMixin, LineageMixin, GDSMixin, RiskMixin):
    """Motor analítico central que agrega cuatro mixins especializados sobre la red Neo4j B2B.

    Gestiona el ciclo de vida de la conexión Neo4j (``__enter__``/``__exit__``) y expone
    ``_fetch_data`` como helper compartido de lectura para todos los mixins.

    Los métodos de análisis están organizados en cuatro módulos:

    - ``macro_stats.py``    — estructura global, rankings, series temporales y topología scale-free
    - ``traceability.py``   — trazabilidad documental (backward, exact path, forward)
    - ``gds.py``            — Graph Data Science: centralidad, PageRank, comunidades, WCC
    - ``risk.py``           — agrega cuatro submódulos de riesgo:

        - ``risk_supply.py``      — lead time, pagos, vencidos, concentración, geografía
        - ``risk_discrepancy.py`` — tasa de discrepancias e impacto comercial
        - ``risk_scoring.py``     — scoring compuesto, fragilidad de comprador, contratos
        - ``risk_cross.py``       — análisis cruzado multidimensional
    """

    def __init__(self, neo4j_uri: str, neo4j_user: str,
                 neo4j_password: str, neo4j_database: str) -> None:
        self.neo4j_database = neo4j_database
        self._driver: Driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> "B2BGraphAnalyzer":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def verify_connection(self) -> None:
        self._driver.verify_connectivity()

    def _fetch_data(self, query: str, **params: Any) -> list[dict[str, Any]]:
        """Ejecuta una consulta Cypher de solo lectura y devuelve los resultados como lista de dicts.

        Abre una sesión Neo4j, ejecuta la consulta en una operación de lectura y devuelve
        los resultados como lista de dicts. Ante cualquier fallo delega en
        ``_report_query_error`` para registrar el contexto completo.

        Args:
            query: Sentencia Cypher de solo lectura.
            **params: Parámetros de la consulta (interpolados por el driver).

        Returns:
            Lista de dicts con los resultados; una fila por registro del ``RETURN`` Cypher.
        """
        try:
            with self._driver.session(database=self.neo4j_database) as session:
                return session.execute_read(lambda tx: tx.run(query, **params).data())
        except Neo4jError as exc:
            _report_query_error("Neo4j", exc.code, str(exc.message), query, params)
            raise
        except Exception as exc:
            _report_query_error(type(exc).__name__, None, str(exc), query, params)
            raise
