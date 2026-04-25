"""
Unit tests for Agent KPI Calculator.

Validates computation correctness across all 7 KPI categories.
"""

import uuid
from datetime import datetime, timedelta

import pytest

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


class TestAgentKPICalculator:
    def test_empty_batch_raises(self):
        calc = AgentKPICalculator()
        with pytest.raises(ValueError, match="At least one response"):
            calc.evaluate_batch([])

    def test_single_success_response(self):
        calc = AgentKPICalculator()
        resp = _make_response(latency_ms=500, status=AgentStatus.SUCCESS)
        report = calc.evaluate_batch([resp])

        assert report.run_count == 1
        assert report.overview.total_runs == 1
        assert report.overview.success_count == 1
        assert report.overview.error_count == 0
        assert report.overview.success_rate == 1.0

        assert report.performance.avg_latency_ms == 500.0
        assert report.performance.min_latency_ms == 500.0
        assert report.performance.max_latency_ms == 500.0

        assert report.reliability.success_rate == 1.0
        assert report.reliability.error_rate == 0.0
        assert report.reliability.retry_rate == 0.0

        assert report.cost.total_cost_usd == 0.004
        assert report.cost.avg_cost_per_run_usd == 0.004
        assert report.cost.cost_per_success_usd == 0.004

        assert report.ai_usage.total_prompt_tokens == 100
        assert report.ai_usage.total_completion_tokens == 80
        assert report.ai_usage.total_tokens == 180

        assert report.technical.avg_cpu_time_ms == 150.0
        assert report.technical.avg_memory_mb == 128.0
        assert report.technical.avg_network_calls == 2.0
        assert report.technical.total_retries == 0

    def test_mixed_success_failure(self):
        calc = AgentKPICalculator()
        responses = [
            _make_response(latency_ms=400, status=AgentStatus.SUCCESS),
            _make_response(latency_ms=600, status=AgentStatus.SUCCESS),
            _make_response(latency_ms=30000, status=AgentStatus.FAILED),
        ]
        report = calc.evaluate_batch(responses)

        assert report.overview.total_runs == 3
        assert report.overview.success_count == 2
        assert report.overview.error_count == 1
        assert report.overview.success_rate == pytest.approx(2 / 3)

        assert report.performance.avg_latency_ms == pytest.approx((400 + 600 + 30000) / 3)
        assert report.performance.min_latency_ms == 400.0
        assert report.performance.max_latency_ms == 30000.0

        assert report.reliability.success_rate == pytest.approx(2 / 3)
        assert report.reliability.error_rate == pytest.approx(1 / 3)

    def test_cost_per_success_with_failures(self):
        calc = AgentKPICalculator()
        responses = [
            _make_response(latency_ms=400, status=AgentStatus.SUCCESS, cost=0.005),
            _make_response(latency_ms=400, status=AgentStatus.FAILED, cost=0.001),
        ]
        report = calc.evaluate_batch(responses)

        assert report.cost.total_cost_usd == 0.006
        assert report.cost.cost_per_success_usd == 0.005

    def test_step_analytics(self):
        calc = AgentKPICalculator()
        responses = [
            _make_response(latency_ms=500, steps=[
                AgentStepDetail(
                    step_name="step_a",
                    status=AgentStatus.SUCCESS,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow() + timedelta(milliseconds=50),
                ),
            ]),
            _make_response(latency_ms=700, steps=[
                AgentStepDetail(
                    step_name="step_a",
                    status=AgentStatus.SUCCESS,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow() + timedelta(milliseconds=70),
                ),
            ]),
        ]
        report = calc.evaluate_batch(responses)

        assert len(report.breakdowns.steps) == 1
        step = report.breakdowns.steps[0]
        assert step.step_name == "step_a"
        assert step.avg_latency_ms == 60.0
        assert step.min_latency_ms == 50.0
        assert step.max_latency_ms == 70.0
        assert step.instability_ms == 20.0
        assert step.occurrence_count == 2

    def test_tool_analytics(self):
        calc = AgentKPICalculator()
        responses = [
            _make_response(latency_ms=500, tools=[
                AgentToolCall(
                    tool_name="tool_x",
                    status=AgentStatus.SUCCESS,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow() + timedelta(milliseconds=500),
                ),
            ]),
            _make_response(latency_ms=800, tools=[
                AgentToolCall(
                    tool_name="tool_x",
                    status=AgentStatus.SUCCESS,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow() + timedelta(milliseconds=800),
                ),
            ]),
        ]
        report = calc.evaluate_batch(responses)

        assert len(report.breakdowns.tools) == 1
        tool = report.breakdowns.tools[0]
        assert tool.tool_name == "tool_x"
        assert tool.avg_latency_ms == 650.0
        assert tool.usage_count == 2
        assert tool.failure_rate == 0.0

    def test_advanced_insights(self):
        calc = AgentKPICalculator()
        responses = [
            _make_response(latency_ms=400, cost=0.003),
            _make_response(latency_ms=800, cost=0.007),
        ]
        report = calc.evaluate_batch(responses)

        assert report.advanced.most_expensive_agent is not None
        assert report.advanced.most_expensive_agent["agent_id"] == "test_agent"
        assert report.advanced.most_expensive_agent["total_cost_usd"] == 0.01

    def test_evaluation_id_generation(self):
        calc = AgentKPICalculator()
        resp = _make_response()
        report = calc.evaluate_batch([resp])
        assert report.evaluation_id.startswith("eval_")

    def test_custom_evaluation_id(self):
        calc = AgentKPICalculator()
        resp = _make_response()
        report = calc.evaluate_batch([resp], evaluation_id="my_custom_id")
        assert report.evaluation_id == "my_custom_id"
