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

// =============================================================================
// Agent Evaluation Types
// =============================================================================

export type AgentStatus = "SUCCESS" | "FAILED" | "PARTIAL";
export type AgentErrorType = "TECHNICAL" | "BUSINESS" | "TIMEOUT" | "EXTERNAL_API" | "TOOL_REJECTED" | "VALIDATION";
export type JudgmentLevel = "EXCELLENT" | "ACCEPTABLE" | "MARGINAL" | "FAIL";

export interface AgentStepDetail {
  step_name: string;
  status: AgentStatus;
  started_at: string;
  completed_at: string;
  latency_ms: number | null;
  tool_used: string | null;
  output: string | null;
  reasoning: string | null;
}

export interface AgentToolCall {
  tool_name: string;
  status: AgentStatus;
  started_at: string;
  completed_at: string;
  latency_ms: number | null;
  input_params: Record<string, unknown>;
  output_result: unknown;
  error_message: string | null;
}

export interface AgentErrorDetail {
  type: AgentErrorType;
  message: string;
  step: string | null;
  traceback: string | null;
  recoverable: boolean;
}

export interface AgentRunResponseV1 {
  run_id: string;
  agent_id: string;
  agent_version: string;
  status: AgentStatus;
  output: unknown;
  latency_ms: number;
  started_at: string;
  completed_at: string;
  metrics: {
    technical?: {
      cpu_time_ms?: number;
      memory_mb?: number;
      network_calls_count?: number;
      retry_count?: number;
    };
    ai?: {
      prompt_tokens?: number;
      completion_tokens?: number;
      total_tokens?: number;
      estimated_cost_usd?: number;
      model_name?: string;
    };
  };
  steps: AgentStepDetail[];
  tools: AgentToolCall[];
  error: AgentErrorDetail | null;
  metadata: Record<string, unknown>;
}

export interface KPIOverview {
  total_runs: number;
  success_count: number;
  error_count: number;
  partial_count: number;
  success_rate: number;
}

export interface KPIPerformance {
  avg_latency_ms: number;
  min_latency_ms: number;
  max_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  std_latency_ms: number;
}

export interface KPIReliability {
  success_rate: number;
  error_rate: number;
  retry_rate: number;
  mean_time_between_failures_ms: number | null;
  failure_types: Record<string, number>;
}

export interface KPICost {
  total_cost_usd: number;
  avg_cost_per_run_usd: number;
  cost_per_success_usd: number;
  cost_per_token_usd: number | null;
}

export interface KPIAIUsage {
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  avg_prompt_tokens_per_run: number;
  avg_completion_tokens_per_run: number;
  avg_tokens_per_run: number;
}

export interface KPITechnical {
  avg_cpu_time_ms: number | null;
  avg_memory_mb: number | null;
  avg_network_calls: number;
  total_retries: number;
}

export interface StepAnalytics {
  step_name: string;
  avg_latency_ms: number;
  max_latency_ms: number;
  min_latency_ms: number;
  p95_latency_ms: number;
  failure_rate: number;
  success_rate: number;
  occurrence_count: number;
  instability_ms: number;
}

export interface ToolAnalytics {
  tool_name: string;
  avg_latency_ms: number;
  max_latency_ms: number;
  min_latency_ms: number;
  usage_count: number;
  failure_rate: number;
  success_rate: number;
}

export interface KPIAdvanced {
  most_expensive_agent: Record<string, unknown> | null;
  slowest_step: StepAnalytics | null;
  most_unstable_step: StepAnalytics | null;
  slowest_tool: ToolAnalytics | null;
  most_used_tool: ToolAnalytics | null;
  step_efficiency_ratio: number | null;
}

export interface AgentBreakdown {
  latency_by_agent: Record<string, unknown>[];
  cost_by_agent: Record<string, unknown>[];
  success_rate_by_agent: Record<string, unknown>[];
  workflows: Record<string, unknown>[];
  steps: StepAnalytics[];
  tools: ToolAnalytics[];
}

export interface AgentKPIReport {
  evaluation_id: string;
  evaluated_at: string;
  agent_id: string | null;
  workflow_id: string | null;
  run_count: number;
  overview: KPIOverview;
  performance: KPIPerformance;
  reliability: KPIReliability;
  cost: KPICost;
  ai_usage: KPIAIUsage;
  technical: KPITechnical;
  advanced: KPIAdvanced;
  breakdowns: AgentBreakdown;
}

export interface CategoryScore {
  category: string;
  score: number;
  weight: number;
  weighted_score: number;
  interpretation: string;
  standard_reference: string;
}

export interface AgentEvaluationJudgment {
  evaluation_id: string;
  global_score: number;
  judgment: JudgmentLevel;
  confidence: number;
  category_scores: CategoryScore[];
  blocking_violations: string[];
  recommendation: string;
  risk_assessment: string;
  standards_compliance: Record<string, boolean>;
}

export interface AgentBatchEvaluationResponse {
  evaluation_id: string;
  kpi_report: AgentKPIReport;
  judgment: AgentEvaluationJudgment;
  raw_responses_count: number;
  markdown_report: string;
  json_report: Record<string, unknown>;
}
