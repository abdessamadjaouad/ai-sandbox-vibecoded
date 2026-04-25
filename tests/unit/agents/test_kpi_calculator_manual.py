"""
Manual unit tests for Agent KPI Calculator (no pytest dependency).
"""

import uuid
from datetime import datetime, timedelta

from backend.app.models.agent_api_contract import (
    AgentRunResponseV1,
    AgentStatus,
    AgentStepDetail,
    AgentToolCall,
)
from backend.app.evaluation_layer.agents.kpi_calculator import AgentKPICalculator


def _make_response(
    latency_ms: float = 500,
    status: AgentStatus = AgentStatus.SUCCESS,
    prompt_tokens: int = 100,
    completion_tokens: int = 80,
    cost: float = 0.004,
    cpu_time_ms: float | None = 150,
    memory_mb: float | None = 128,
    network_calls: int = 2,
    retries: int = 0,
    steps: list | None = None,
    tools: list | None = None,
) -> AgentRunResponseV1:
    start = datetime.utcnow()
    end = start + timedelta(milliseconds=latency_ms)

    return AgentRunResponseV1(
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        agent_id="test_agent",
        agent_version="1.0.0",
        status=status,
        output={"result": "ok"} if status == AgentStatus.SUCCESS else None,
        latency_ms=latency_ms,
        started_at=start,
        completed_at=end,
        metrics={
            "technical": {
                "cpu_time_ms": cpu_time_ms,
                "memory_mb": memory_mb,
                "network_calls_count": network_calls,
                "retry_count": retries,
            },
            "ai": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "estimated_cost_usd": cost,
                "model_name": "gpt-4o-mini",
            },
        },
        steps=steps or [
            AgentStepDetail(
                step_name="validate",
                status=AgentStatus.SUCCESS,
                started_at=start,
                completed_at=start + timedelta(milliseconds=20),
            ),
            AgentStepDetail(
                step_name="process",
                status=status,
                started_at=start + timedelta(milliseconds=20),
                completed_at=end,
                tool_used="mock_llm",
            ),
        ],
        tools=tools or [
            AgentToolCall(
                tool_name="mock_llm",
                status=status,
                started_at=start + timedelta(milliseconds=20),
                completed_at=end,
            ),
        ],
        error=None,
        metadata={},
    )


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}: expected {expected}, got {actual}")


def assert_approx(actual, expected, tol=0.01, msg=""):
    if abs(actual - expected) > tol:
        raise AssertionError(f"{msg}: expected ~{expected}, got {actual}")


def test_empty_batch_raises():
    calc = AgentKPICalculator()
    try:
        calc.evaluate_batch([])
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "At least one response" in str(e)


def test_single_success_response():
    calc = AgentKPICalculator()
    resp = _make_response(latency_ms=500, status=AgentStatus.SUCCESS)
    report = calc.evaluate_batch([resp])

    assert_eq(report.run_count, 1, "run_count")
    assert_eq(report.overview.total_runs, 1, "total_runs")
    assert_eq(report.overview.success_count, 1, "success_count")
    assert_eq(report.overview.error_count, 0, "error_count")
    assert_eq(report.overview.success_rate, 1.0, "success_rate")

    assert_eq(report.performance.avg_latency_ms, 500.0, "avg_latency")
    assert_eq(report.performance.min_latency_ms, 500.0, "min_latency")
    assert_eq(report.performance.max_latency_ms, 500.0, "max_latency")

    assert_eq(report.reliability.success_rate, 1.0, "reliability success_rate")
    assert_eq(report.reliability.error_rate, 0.0, "error_rate")
    assert_eq(report.reliability.retry_rate, 0.0, "retry_rate")

    assert_eq(report.cost.total_cost_usd, 0.004, "total_cost")
    assert_eq(report.cost.avg_cost_per_run_usd, 0.004, "avg_cost")
    assert_eq(report.cost.cost_per_success_usd, 0.004, "cost_per_success")

    assert_eq(report.ai_usage.total_prompt_tokens, 100, "prompt_tokens")
    assert_eq(report.ai_usage.total_completion_tokens, 80, "completion_tokens")
    assert_eq(report.ai_usage.total_tokens, 180, "total_tokens")

    assert_eq(report.technical.avg_cpu_time_ms, 150.0, "cpu_time")
    assert_eq(report.technical.avg_memory_mb, 128.0, "memory")
    assert_eq(report.technical.avg_network_calls, 2.0, "network_calls")
    assert_eq(report.technical.total_retries, 0, "retries")


def test_mixed_success_failure():
    calc = AgentKPICalculator()
    responses = [
        _make_response(latency_ms=400, status=AgentStatus.SUCCESS),
        _make_response(latency_ms=600, status=AgentStatus.SUCCESS),
        _make_response(latency_ms=30000, status=AgentStatus.FAILED),
    ]
    report = calc.evaluate_batch(responses)

    assert_eq(report.overview.total_runs, 3, "total_runs")
    assert_eq(report.overview.success_count, 2, "success_count")
    assert_eq(report.overview.error_count, 1, "error_count")
    assert_approx(report.overview.success_rate, 2 / 3, msg="success_rate")

    assert_approx(report.performance.avg_latency_ms, (400 + 600 + 30000) / 3, msg="avg_latency")
    assert_eq(report.performance.min_latency_ms, 400.0, "min_latency")
    assert_eq(report.performance.max_latency_ms, 30000.0, "max_latency")

    assert_approx(report.reliability.success_rate, 2 / 3, msg="reliability success_rate")
    assert_approx(report.reliability.error_rate, 1 / 3, msg="error_rate")


def test_cost_per_success_with_failures():
    calc = AgentKPICalculator()
    responses = [
        _make_response(latency_ms=400, status=AgentStatus.SUCCESS, cost=0.005),
        _make_response(latency_ms=400, status=AgentStatus.FAILED, cost=0.001),
    ]
    report = calc.evaluate_batch(responses)

    assert_eq(report.cost.total_cost_usd, 0.006, "total_cost")
    assert_eq(report.cost.cost_per_success_usd, 0.005, "cost_per_success")


def test_step_analytics():
    calc = AgentKPICalculator()
    now = datetime.utcnow()
    responses = [
        _make_response(latency_ms=500, steps=[
            AgentStepDetail(
                step_name="step_a",
                status=AgentStatus.SUCCESS,
                started_at=now,
                completed_at=now + timedelta(milliseconds=50),
            ),
        ]),
        _make_response(latency_ms=700, steps=[
            AgentStepDetail(
                step_name="step_a",
                status=AgentStatus.SUCCESS,
                started_at=now,
                completed_at=now + timedelta(milliseconds=70),
            ),
        ]),
    ]
    report = calc.evaluate_batch(responses)

    assert_eq(len(report.breakdowns.steps), 1, "step_count")
    step = report.breakdowns.steps[0]
    assert_eq(step.step_name, "step_a", "step_name")
    assert_eq(step.avg_latency_ms, 60.0, "avg_latency")
    assert_eq(step.min_latency_ms, 50.0, "min_latency")
    assert_eq(step.max_latency_ms, 70.0, "max_latency")
    assert_eq(step.instability_ms, 20.0, "instability")
    assert_eq(step.occurrence_count, 2, "occurrence_count")


def test_tool_analytics():
    calc = AgentKPICalculator()
    now = datetime.utcnow()
    responses = [
        _make_response(latency_ms=500, tools=[
            AgentToolCall(
                tool_name="tool_x",
                status=AgentStatus.SUCCESS,
                started_at=now,
                completed_at=now + timedelta(milliseconds=500),
            ),
        ]),
        _make_response(latency_ms=800, tools=[
            AgentToolCall(
                tool_name="tool_x",
                status=AgentStatus.SUCCESS,
                started_at=now,
                completed_at=now + timedelta(milliseconds=800),
            ),
        ]),
    ]
    report = calc.evaluate_batch(responses)

    assert_eq(len(report.breakdowns.tools), 1, "tool_count")
    tool = report.breakdowns.tools[0]
    assert_eq(tool.tool_name, "tool_x", "tool_name")
    assert_eq(tool.avg_latency_ms, 650.0, "avg_latency")
    assert_eq(tool.usage_count, 2, "usage_count")
    assert_eq(tool.failure_rate, 0.0, "failure_rate")


def test_advanced_insights():
    calc = AgentKPICalculator()
    responses = [
        _make_response(latency_ms=400, cost=0.003),
        _make_response(latency_ms=800, cost=0.007),
    ]
    report = calc.evaluate_batch(responses)

    assert report.advanced.most_expensive_agent is not None
    assert_eq(report.advanced.most_expensive_agent["agent_id"], "test_agent", "agent_id")
    assert_eq(report.advanced.most_expensive_agent["total_cost_usd"], 0.01, "total_cost")


def test_evaluation_id_generation():
    calc = AgentKPICalculator()
    resp = _make_response()
    report = calc.evaluate_batch([resp])
    assert report.evaluation_id.startswith("eval_"), "evaluation_id prefix"


def test_custom_evaluation_id():
    calc = AgentKPICalculator()
    resp = _make_response()
    report = calc.evaluate_batch([resp], evaluation_id="my_custom_id")
    assert_eq(report.evaluation_id, "my_custom_id", "custom_id")


def run_all_tests():
    tests = [
        test_empty_batch_raises,
        test_single_success_response,
        test_mixed_success_failure,
        test_cost_per_success_with_failures,
        test_step_analytics,
        test_tool_analytics,
        test_advanced_insights,
        test_evaluation_id_generation,
        test_custom_evaluation_id,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_all_tests() else 1)
