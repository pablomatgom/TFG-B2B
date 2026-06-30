# Análisis de Riesgos (`risk_*.py`)

El subsistema de riesgo se descompone en cuatro mixins especializados que `RiskMixin`
agrega sin añadir lógica propia. Cada submódulo cubre un eje de vulnerabilidad distinto:
discrepancias documentales, operaciones y geografía, scoring compuesto, y síntesis cruzada.

---

## Síntesis multidimensional (`risk_cross.py`)

::: backend.etl.analytics.risk_cross.SynthesisMixin
    options:
      show_root_full_path: false

---

## Discrepancias e impacto comercial (`risk_discrepancy.py`)

::: backend.etl.analytics.risk_discrepancy.DiscrepancyMixin
    options:
      show_root_full_path: false

---

## Scoring y fragilidad (`risk_scoring.py`)

::: backend.etl.analytics.risk_scoring.ScoringMixin
    options:
      show_root_full_path: false

---

## Operaciones y geografía (`risk_supply.py`)

::: backend.etl.analytics.risk_supply.OperationalMixin
    options:
      show_root_full_path: false