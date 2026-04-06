# AI Sandbox

Modular experimentation platform for testing, comparing, validating, and benchmarking AI models (ML / NLP / LLM / RAG / Agentic AI) before production integration.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Local Development Setup

1. **Clone and setup environment**

   ```bash
   git clone <repository-url>
   cd sandbox-project-vibecoded
   cp .env.example .env
   ```

2. **Install Python dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Start infrastructure services**

   ```bash
   docker compose up -d postgres chromadb mlflow minio
   ```

4. **Run the backend locally**

   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Verify installation**

   ```bash
   curl http://localhost:8000/health
   ```

### Full Stack with Docker

```bash
docker compose up --build
```

Services will be available at:

| Service   | URL                     |
|-----------|-------------------------|
| Backend   | http://localhost:8000   |
| MLflow    | http://localhost:5000   |
| ChromaDB  | http://localhost:8000   |
| MinIO     | http://localhost:9001   |

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

## Project Structure

```
ai_sandbox/
├── backend/app/
│   ├── api/              # FastAPI routers
│   ├── core/             # Config, database, logging
│   ├── data_layer/       # Ingestion, validation, versioning
│   ├── experiment_layer/ # LangGraph orchestrator, runners
│   ├── evaluation_layer/ # Metrics, scoring, reports
│   ├── governance/       # RBAC, audit, auth
│   └── models/           # Pydantic schemas
├── frontend/             # React application
├── tests/                # pytest test suites
├── docker/               # Dockerfiles
└── infra/                # Infrastructure configs
```

## Architecture

The platform is built as 4 layers:

1. **Data Layer** - Ingestion, validation, versioning, vector indexing
2. **Experiment Layer** - LangGraph orchestrator, model runners, tracking
3. **Evaluation Layer** - Metrics, scoring, report generation
4. **Governance Layer** - RBAC, audit logs, compliance

## License

MIT
