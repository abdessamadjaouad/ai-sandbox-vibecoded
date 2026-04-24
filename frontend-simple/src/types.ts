// /home/jao/Desktop/sandbox-project-vibecoded/frontend-simple/src/types.ts

export type TaskType = "classification" | "regression";

// Dataset types (from /api/upload, /api/datasets)
export interface SimpleDatasetInfo {
  dataset_id: string;
  filename: string;
  rows: number;
  columns: number;
  column_names: string[];
  numeric_columns: string[];
  categorical_columns: string[];
  missing_values: Record<string, number>;
  file_size_kb: number;
  uploaded_at?: string;
}

// Config suggestion (from /api/dataset/{id}/suggest)
export interface SuggestionResponse {
  target_column: string;
  task_type: string;
  n_unique_target: number;
}

// Run config (sent to /api/run)
export interface SimpleRunConfig {
  task_type: TaskType;
  target_column: string;
  dataset_id: string;
  description?: string;
  models?: string[];
  test_size?: number;
  random_state?: number;
  weight_performance?: number;
  weight_robustness?: number;
  weight_latency?: number;
  weight_size?: number;
  latency_threshold_s?: number | null;
  timeout_per_model_s?: number | null;
}

// Model result (in RunResult)
export interface SimpleModelResult {
  model_name: string;
  metrics: Record<string, number>;
  training_time_ms: number;
  prediction_time_ms: number;
  model_size_kb: number;
  global_score: number | null;
  rank: number | null;
}

// Run result (from /api/run, /api/results/{run_id})
export interface SimpleRunResult {
  run_id: string;
  task_type: string;
  target_column: string;
  dataset_id: string;
  model_results: SimpleModelResult[];
  best_model: string;
  report_path: string | null;
}

// Available models
export const AVAILABLE_MODELS = {
  classification: [
    "logistic_regression",
    "random_forest",
    "xgboost",
    "lightgbm",
    "extra_trees",
    "knn",
  ],
  regression: [
    "linear_regression",
    "random_forest",
    "xgboost",
    "lightgbm",
    "extra_trees",
  ],
} as const;

// Default weights
export const DEFAULT_WEIGHTS = {
  performance: 0.4,
  robustness: 0.2,
  latency: 0.2,
  size: 0.2,
};

// Wizard step types
export type WizardStep = "home" | "upload" | "config" | "run" | "results";