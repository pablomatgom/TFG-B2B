from __future__ import annotations

from backend.etl.analytics.risk_concentration import ConcentrationMixin
from backend.etl.analytics.risk_discrepancy   import DiscrepancyMixin
from backend.etl.analytics.risk_operational   import OperationalMixin
from backend.etl.analytics.risk_scoring       import ScoringMixin
from backend.etl.analytics.risk_geographic    import GeographicMixin
from backend.etl.analytics.risk_synthesis     import SynthesisMixin


class RiskMixin(
    ConcentrationMixin,
    DiscrepancyMixin,
    OperationalMixin,
    ScoringMixin,
    GeographicMixin,
    SynthesisMixin,
):
    """Agrega todos los mixins de analítica de riesgo."""