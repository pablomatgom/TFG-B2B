from pydantic import BaseModel
from typing import Optional


class PipelineRequest(BaseModel):
    """Configuración completa para lanzar el pipeline ETL sintético desde la API.

    Este modelo es el cuerpo del endpoint ``POST /api/pipeline/run``, donde dodos
    los parámetros tienen valores por defecto que reproducen una red B2B
    de tamaño mediano con una topología realista de acuerdo a los modelos.

    Attributes:
        rows: Número de empresas (nodos ``Company``) a generar.
        avg_degree_supplies: Grado medio de la red de suministro
            (aristas ``SUPPLIES``).
        avg_degree_documents: Grado medio de documentos EDI por par
            proveedor-comprador activo.
        gamma: Exponente de la ley de potencias para la distribución de grados
            del modelo LFR. Debe ser ``> 1.0``.
        beta: Exponente de la ley de potencias para el tamaño de las
            comunidades LFR. Debe ser ``> 1.0``.
        mu: Coeficiente de mezcla LFR para la conexión inter-comunidad.
            Debe ser ``0 <= mu < 1.0``.
        avg_degree_products: Número medio de productos distintos que vende
            cada empresa proveedora (aristas ``SELLS``).
        batch_size: Tamaño del lote para la carga y eliminación de datos en Neo4j. 
            Valores menores reducen el consumo de RAM, pero aumentan 
            la cantidad de transacciones
        clear_db: Si ``True``, borra todos los nodos y aristas de Neo4j antes
            de iniciar la carga, garantizando una base de datos limpia.
        use_random_seed: Si ``True``, ignora ``seed_value`` y usa una semilla
            aleatoria no determinada.
        seed_value: Semilla fija para la generación pseudoaleatoria. Solo se
            aplica cuando ``use_random_seed`` es ``False``, permitiendo
            reproducir exactamente el mismo grafo sintético.
    """

    rows: int = 200
    avg_degree_supplies: int = 7
    avg_degree_documents: int = 5
    gamma: float = 2.4
    beta: float = 1.8
    mu: float = 0.30
    avg_degree_products: int = 25
    batch_size: int = 10000
    clear_db: bool = True
    use_random_seed: bool = True
    seed_value: Optional[int] = 42

