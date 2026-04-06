# backend/app/experiment_layer/__init__.py
"""
Experiment Layer (Layer 2) — LangGraph orchestrated experiment execution.

This layer manages:
- Model catalogue registration
- Experiment orchestration via LangGraph StateGraph
- ML/NLP/LLM/RAG/Agent runners
- MLflow + LangFuse tracking integration
"""

from backend.app.experiment_layer.orchestrator.state import ExperimentState
from backend.app.experiment_layer.orchestrator.graph import create_experiment_graph

__all__ = ["ExperimentState", "create_experiment_graph"]
