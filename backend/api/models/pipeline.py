from pydantic import BaseModel
from typing import Optional


class PipelineRequest(BaseModel):
    rows: int = 200
    avg_degree_supplies: int = 7
    avg_degree_documents: int = 5
    gamma: float = 2.4
    beta: float = 1.8
    mu: float = 0.30
    min_comm: int = 6
    max_comm: int = 45
    avg_degree_products: int = 25
    batch_size: int = 10000
    clear_db: bool = True
    use_random_seed: bool = True
    seed_value: Optional[int] = 42

