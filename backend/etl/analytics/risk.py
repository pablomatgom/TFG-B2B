from __future__ import annotations

from backend.etl.analytics.risk_discrepancy import DiscrepancyMixin
from backend.etl.analytics.risk_supply      import OperationalMixin
from backend.etl.analytics.risk_scoring     import ScoringMixin
from backend.etl.analytics.risk_cross       import SynthesisMixin


class RiskMixin(
    DiscrepancyMixin,
    OperationalMixin,
    ScoringMixin,
    SynthesisMixin,
):
    """Agrega todos los mixins de analítica de riesgo."""