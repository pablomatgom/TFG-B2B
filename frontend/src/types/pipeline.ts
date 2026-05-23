// types/pipeline.ts
export interface PipelineFormData {
  rows: number;
  avg_degree_supplies: number;
  avg_degree_documents: number;
  gamma: number;
  beta: number;
  mu: number;
  min_comm: number;
  max_comm: number;
  avg_degree_products: number;
  batch_size: number;
  clear_db: boolean;
  use_random_seed: boolean;
  seed_value: number;
}

export interface StatusState {
  type: "success" | "error" | null;
  msg: string;
}