# tests/unit/test_evaluation_layer/test_api_evaluation_routes.py
"""Tests for evaluation API routes."""


def test_list_available_metrics_classification(test_client):
    """Returns available metrics for classification."""
    response = test_client.get("/api/v1/evaluation/metrics/available", params={"task_type": "classification"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_type"] == "classification"
    assert "accuracy" in payload["metrics"]


def test_compute_metrics_classification(test_client):
    """Computes classification metrics from request payload."""
    response = test_client.post(
        "/api/v1/evaluation/metrics/compute",
        json={
            "task_type": "classification",
            "y_true": [0, 1, 1, 0],
            "y_pred": [0, 1, 0, 0],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_type"] == "classification"
    assert "accuracy" in payload["metrics"]
    assert payload["support"] == 4


def test_score_models_endpoint(test_client):
    """Scores and ranks models via API endpoint."""
    response = test_client.post(
        "/api/v1/evaluation/score",
        json={
            "task_type": "classification",
            "results": [
                {
                    "model_name": "Model A",
                    "metrics": {"accuracy": 0.92, "f1": 0.90},
                    "inference_latency_ms": 30,
                },
                {
                    "model_name": "Model B",
                    "metrics": {"accuracy": 0.80, "f1": 0.79},
                    "inference_latency_ms": 30,
                },
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["best_model"] == "Model A"
    assert payload["passed_count"] == 2
    assert len(payload["scores"]) == 2


def test_get_default_weights_endpoint(test_client):
    """Returns default scoring weights."""
    response = test_client.get("/api/v1/evaluation/score/weights/default")

    assert response.status_code == 200
    payload = response.json()
    assert payload["performance"] == 0.40
    assert payload["robustness"] == 0.20
    assert payload["latency"] == 0.20
    assert payload["cost"] == 0.20
