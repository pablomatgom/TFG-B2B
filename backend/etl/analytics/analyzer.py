from __future__ import annotations

import logging
import textwrap
from typing import Any

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError

from backend.etl.analytics.macro   import MacroMixin,   GraphMacroStats
from backend.etl.analytics.lineage import LineageMixin
from backend.etl.analytics.gds     import GDSMixin
from backend.etl.analytics.risk    import RiskMixin

logger = logging.getLogger(__name__)


def _report_query_error(
    kind: str,
    code: str | None,
    message: str,
    query: str,
    params: dict,
) -> None:
    sep = "─" * 60
    lines = [
        sep,
        f"[ANALYZER ERROR] {kind}" + (f" — {code}" if code else ""),
        f"  message : {message}",
        f"  params  : {params}",
        f"  query   :\n{textwrap.dedent(query).strip()}",
        sep,
    ]
    for line in lines:
        logger.error(line)


class B2BGraphAnalyzer(MacroMixin, LineageMixin, GDSMixin, RiskMixin):
    """
    Motor analítico central.

    Los métodos están organizados en cuatro módulos especializados:
      • macro.py    — estadísticas globales, geografía, series temporales
      • lineage.py  — trazabilidad documental (discrepancias)
      • gds.py      — Graph Data Science: centralidad, comunidades
      • risk.py     — riesgo operacional: concentración, discrepancias, lead time, exposición
    """

    def __init__(
        self,
        neo4j_uri:      str,
        neo4j_user:     str,
        neo4j_password: str,
        neo4j_database: str,
    ) -> None:
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
        """
        Shared read helper used by all mixins.
        Logs full Neo4j error details (code, message, query) before re-raising.
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
