// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/types.ts
export type DatasetStatus = "pending" | "validating" | "validated" | "failed" | "indexed";
export type DatasetType = "tabular" | "text" | "image" | "mixed";
export type TaskType = "classification" | "regression" | "clustering";
export type ExperimentStatus =
  | "pending"
  | "validating"
  | "preparing"
  | "running"
  | "evaluating"
  | "completed"
  | "failed"
  | "cancelled";

export interface DatasetRead {
  id: string;
  name: string;
  description: string | null;
  dataset_type: DatasetType;
  status: DatasetStatus;
  file_path: string;
  file_size_bytes: number;
  file_format: string;
  row_count: number | null;
  column_count: number | null;
  schema_info: {
    columns?: string[];
    dtypes?: Record<string, string>;
    nullable?: Record<string, boolean>;
  } | null;
  validation_report: ValidationReport | null;
  created_at: string;
  updated_at: string;
}

export interface DatasetListResponse {
  items: DatasetRead[];
  total: number;
  page: number;
  page_size: number;
}

export interface ValidationReport {
  is_valid: boolean;
  total_rows: number;
  total_columns: number;
  null_counts: Record<string, number>;
  null_percentages: Record<string, number>;
  dtypes: Record<string, string>;
  duplicate_rows: number;
  issues: string[];
  warnings: string[];
}

export interface DatasetVersionRead {
  id: string;
  dataset_id: string;
  version: number;
  split_config: Record<string, unknown>;
  train_path: string;
  val_path: string | null;
  test_path: string | null;
  train_rows: number;
  val_rows: number | null;
  test_rows: number | null;
  random_seed: number;
  config_hash: string;
  chroma_collection_id: string | null;
  created_at: string;
}

export interface DatasetAutoConfigRead {
  dataset_id: string;
  suggested_name: string;
  task_type: "classification" | "regression";
  target_column: string | null;
  feature_columns: string[];
  stratify_column: string | null;
  confidence: "low" | "medium" | "high";
  rationale: string;
}

export interface ModelCatalogueEntry {
  name: string;
  family: string;
  class_name: string;
  task_types: TaskType[];
  default_hyperparameters: Record<string, unknown>;
  description: string;
}

export interface ModelConfigPayload {
  name: string;
  family: string;
  class_name: string;
  hyperparameters: Record<string, unknown>;
  enabled: boolean;
}

export interface ExperimentCreatePayload {
  name: string;
  description: string | null;
  experiment_type: "tabular_ml";
  task_type: TaskType;
  dataset_id: string;
  dataset_version_id: string;
  target_column: string;
  feature_columns: string[];
  models: ModelConfigPayload[];
  random_seed: number;
}

export interface ExperimentRead {
  id: string;
  name: string;
  description: string | null;
  experiment_type: "tabular_ml" | "nlp" | "llm" | "rag" | "agent";
  task_type: TaskType | null;
  status: ExperimentStatus;
  user_id: string | null;
  dataset_id: string | null;
  dataset_version_id: string | null;
  target_column: string | null;
  feature_columns: string[] | null;
  models_config: { models?: ModelConfigPayload[] };
  constraints: Record<string, unknown> | null;
  mlflow_experiment_id: string | null;
  mlflow_run_id: string | null;
  random_seed: number;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExperimentResultRead {
  id: string;
  experiment_id: string;
  model_name: string;
  model_family: string;
  model_config: Record<string, unknown>;
  hyperparameters: Record<string, unknown> | null;
  metrics: Record<string, unknown>;
  global_score: number | null;
  rank: number | null;
  training_duration_seconds: number | null;
  inference_latency_ms: number | null;
  artefact_path: string | null;
  mlflow_run_id: string | null;
  error_message: string | null;
  created_at: string;
}

export interface ExperimentSummary {
  experiment_id: string;
  experiment_name: string;
  status: ExperimentStatus;
  total_models: number;
  successful_models: number;
  failed_models: number;
  best_model_name: string | null;
  best_model_score: number | null;
  recommendation: string | null;
  duration_seconds: number | null;
}

export interface EvaluationReportResponse {
  experiment_id: string;
  experiment_name: string;
  markdown_content: string;
  summary: string;
  recommendation: string;
  best_model: string | null;
  best_score: number | null;
}

export interface WizardDraft {
  taskType: TaskType;
  dataset: DatasetRead | null;
  datasetVersion: DatasetVersionRead | null;
  targetColumn: string;
  selectedFeatures: string[];
  selectedModels: ModelCatalogueEntry[];
  experimentName: string;
  experimentDescription: string;
  randomSeed: number;
  trainRatio: number;
  valRatio: number;
  testRatio: number;
  stratifyColumn: string;
}
