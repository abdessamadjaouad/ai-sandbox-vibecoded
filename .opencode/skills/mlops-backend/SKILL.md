---
name: mlops-backend
description: Use this skill whenever building FastAPI routes, LangGraph orchestrator nodes, SQLAlchemy models, or any backend component for the ai-sandbox project. Triggers on: API endpoint creation, agent graph nodes, database models, governance middleware, audit logging.
license: MIT
---

# MLOps Backend Skill

## FastAPI Rules
- All routes async, Pydantic v2 schemas, dependency injection for DB + auth
- Every route checks RBAC before executing, writes audit log after

## LangGraph Rules  
- State must be TypedDict, always log reasoning traces
- Check ChromaDB memory for prior patterns before building new graph
- Node order: validate → select_models → prepare_data → run_experiments → evaluate → score → report → audit

## SQLAlchemy Rules
- Async sessions only, never raw SQL except migrations
- Every sensitive query masked before audit logging
