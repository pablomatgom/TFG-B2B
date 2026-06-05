from __future__ import annotations

from typing import Any


class ConcentrationMixin:
    """Riesgo de concentración de proveedores en la red SUPPLIES."""

    def get_supplier_risk_concentration(self, top_n: int = 10) -> dict[str, Any]:
        """
        Concentración de riesgo: qué % del total de enlaces SUPPLIES acaparan los top-N proveedores.
        Un concentration_pct alto indica dependencia peligrosa de pocos actores.
        """
        q_total = "MATCH ()-[:SUPPLIES]->() RETURN count(*) AS total"
        q_top = """
            MATCH (c:Company)-[:SUPPLIES]->()
            WITH c, count(*) AS degree
            ORDER BY degree DESC LIMIT $top_n
            RETURN c.legal_name AS name, degree
        """
        with self._driver.session(database=self.neo4j_database) as s:
            total_row   = s.run(q_total).single()
            total       = int(total_row["total"]) if total_row else 0
            top_records = s.run(q_top, top_n=top_n).data()

        top_degree_sum = sum(int(r["degree"]) for r in top_records)
        top_suppliers = [
            {
                "name":      r["name"],
                "degree":    int(r["degree"]),
                "share_pct": round(int(r["degree"]) / total * 100, 2) if total else 0,
            }
            for r in top_records
        ]
        return {
            "total_supplies_edges": total,
            "top_n":                top_n,
            "concentration_pct":    round(top_degree_sum / total * 100, 2) if total else 0,
            "top_suppliers":        top_suppliers,
        }