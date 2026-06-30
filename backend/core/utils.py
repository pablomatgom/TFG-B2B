"""Utilidades compartidas por el pipeline ETL y la capa de analítica.

Agrupa dos familias de funciones:

- **Exportación**: escritura de artefactos de ejecución y ficheros JSON
  pre-computados servidos por la API.
- **Conversión segura**: parsers tolerantes a fallos para valores leídos
  desde CSVs sintéticos o variables de entorno donde el tipo no está
  garantizado.
"""
import json
from pathlib import Path
from typing import Any
import pandas as pd
from datetime import date, datetime


# ── Exportación y escritura ───────────────────────────────────────────────────
def write_step_artifact(processed_dir: Path, step: str, payload: dict) -> Path:
    """Crea un archivo JSON con el log de ejecución de una fase del pipeline.

    Cada fase escribe su propio fichero ``{step}_last_run.json`` en
    ``data/processed/``, con timestamps, conteos de filas y cualquier
    metadato relevante para auditoría.

    Args:
        processed_dir: Directorio destino (``Settings.data_processed_dir``).
        step: Nombre de la fase: ``"generate"``, ``"load"``, ``"analyze"``
            o ``"all"``.
        payload: Diccionario con las métricas de la ejecución.

    Returns:
        Ruta absoluta al fichero JSON escrito.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    target = processed_dir / f"{step}_last_run.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def export_dict_to_json(data: dict[str, Any], export_dir: Path, filename: str) -> Path:
    """Crea o sobrescribe un archivo JSON con el contenido de un diccionario.

    Utilizado para exportar los resultados del analizador.

    Args:
        data: Diccionario serializable a JSON.
        export_dir: Directorio destino (``Settings.data_export_dir``).
        filename: Nombre del fichero de salida.

    Returns:
        Ruta absoluta al fichero JSON escrito.
    """
    export_dir.mkdir(parents=True, exist_ok=True)
    target = export_dir / filename
    with target.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return target


def export_df_to_json(df: pd.DataFrame, export_dir: Path, filename: str) -> Path:
    """Crea o sobrescribe un archivo JSON tabular a partir de un DataFrame.

    Exporta los datos como una lista de registros (``orient="records"``). 
    Utilizado habitualmente para exportar métricas tabulares del analizador.

    Args:
        df: DataFrame con los resultados a exportar.
        export_dir: Directorio destino (``Settings.data_export_dir``).
        filename: Nombre del fichero de salida.

    Returns:
        Ruta absoluta al fichero JSON escrito.
    """
    export_dir.mkdir(parents=True, exist_ok=True)
    target = export_dir / filename
    df.to_json(target, orient="records", indent=2, force_ascii=False)
    return target


# ── Conversión segura ─────────────────────────────────────────────────────────
def safe_float(value: str | None, default: float = 0.0) -> float:
    """Convierte un valor a ``float`` tolerando nulos y notación europea.

    Acepta separadores de miles con punto y decimales con coma,
    habitual en datos españoles.

    Args:
        value: Cadena a convertir, puede ser ``None`` o estar vacía.
        default: Valor devuelto si la conversión falla o el input es nulo.

    Returns:
        Valor convertido o ``default``.
    """
    if not value or not str(value).strip():
        return default
    try:
        return float(str(value).strip().replace(",", "."))
    except ValueError:
        return default


def safe_int(value: str | None, default: int = 0) -> int:
    """Convierte un valor a ``int`` tolerando decimales y notación europea.

    Convierte primero a ``float`` para manejar strings como ``"5000.0"``
    o ``"5.000"`` antes de truncar a entero.

    Args:
        value: Cadena a convertir, puede ser ``None`` o estar vacía.
        default: Valor devuelto si la conversión falla o el input es nulo.

    Returns:
        Valor convertido o ``default``.
    """
    if not value or not str(value).strip():
        return default
    try:
        cleaned_val = str(value).strip().replace(".", "").replace(",", ".")
        return int(float(cleaned_val))
    except ValueError:
        return default


def safe_date(value: str | None, default: date) -> date:
    """Extrae una fecha de un texto de forma segura, evitando errores de formato.

    Limpia la cadena de texto para intentar su conversión. Si el texto está 
    vacío o el formato es inválido, devuelve la fecha de respaldo (default).

    Args:
        value: Cadena de fecha (p. ej. ``"2024-03-15T10:00:00Z"``); puede ser
            ``None`` o estar vacía.
        default: Valor devuelto si la conversión falla o el input es nulo.

    Returns:
        Fecha extraída o ``default``.
    """
    if not value or not str(value).strip():
        return default
    try:
        clean_val = str(value).strip().replace("Z", "+00:00")
        return datetime.fromisoformat(clean_val).date()
    except ValueError:
        return default


def pick(row: dict[str, str], *keys: str) -> str | None:
    """Extrae el primer valor no nulo de un dict dado un conjunto de claves candidatas.

    Útil cuando un mismo campo puede aparecer bajo nombres distintos en
    diferentes versiones de CSV.

    Args:
        row: Fila de datos como diccionario.
        *keys: Claves a probar en orden. Se devuelve la primera con valor
            no nulo.

    Returns:
        Primer valor encontrado, o ``None`` si ninguna clave
            tiene valor.
    """
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None