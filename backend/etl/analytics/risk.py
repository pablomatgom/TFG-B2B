from __future__ import annotations

from backend.etl.analytics.risk_concentration import ConcentrationMixin
from backend.etl.analytics.risk_discrepancy   import DiscrepancyMixin
from backend.etl.analytics.risk_operational   import OperationalMixin
from backend.etl.analytics.risk_scoring       import ScoringMixin


class RiskMixin(ConcentrationMixin, DiscrepancyMixin, OperationalMixin, ScoringMixin):
    """Agrega todos los mixins de analítica de riesgo."""