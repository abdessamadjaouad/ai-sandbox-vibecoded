---
name: benchmark-engine
description: Use this skill when implementing any benchmarking logic, KPI computation, model evaluation, RAG evaluation, or agent evaluation in ai-sandbox. Triggers on: metric calculation, RAGAS, DeepEval, MLflow tracking, scoring formulas, report generation.
license: MIT
---

# Benchmark Engine Skill

## KPI Stack
- Tabular ML: scikit-learn metrics + SHAP via shap library
- LLM/RAG: RAGAS for faithfulness/context adherence, DeepEval for hallucination
- Agent: LangFuse for traces + cost, DeepEval for task success
- Always run minimum 3 configs before recommending

## Scoring Formula
global_score = Σ(normalised_metric_i × weight_i)
Default weights: Performance 40%, Robustness 20%, Latency 20%, Cost 20%
Blocking: if latency > threshold OR cost > budget → penalise or exclude

## MLflow Tracking
Every run logs: run_id, dataset_id, dataset_version, config_hash, all KPI scores
Artifacts stored at: s3://sandbox/{run_id}/{artifact_name} via MinIO
