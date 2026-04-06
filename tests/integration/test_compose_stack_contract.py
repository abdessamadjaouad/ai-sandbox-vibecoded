from pathlib import Path


def _compose_text() -> str:
    root = Path(__file__).resolve().parents[2]
    compose_file = root / "docker-compose.yml"
    return compose_file.read_text(encoding="utf-8")


def test_compose_defines_core_services() -> None:
    """Verify docker compose declares the expected core platform services."""
    compose = _compose_text()

    for service_name in ("postgres:", "chromadb:", "mlflow:", "minio:", "backend:"):
        assert f"\n  {service_name}" in compose, f"Missing service {service_name}"


def test_mlflow_uses_internal_postgres_service() -> None:
    """Ensure MLflow backend points to the compose postgres service."""
    compose = _compose_text()

    assert "--backend-store-uri" in compose, "Missing MLflow backend store configuration."
    assert "@postgres:5432/" in compose, "MLflow backend should target the postgres service."
