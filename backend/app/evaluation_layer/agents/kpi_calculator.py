"""
Agent KPI Calculator

Transforms raw AgentRunResponseV1 objects into structured KPI reports
across 7 categories: overview, performance, reliability, cost, ai_usage,
technical, advanced, and breakdowns.

Calculation methods follow ISO/IEC 25010 quality model and MLCommons
AI Efficiency standards for metric definitions.
"""

import uuid
from datetime import datetime
from typing import Any

import numpy as np

from backend.app.models.agent_api_contract import (
    AgentBreakdown,
    AgentKPIReport,
    AgentRunResponseV1,
    AgentStatus,
    KPIAdvanced,
    KPIAIUsage,
    KPICost,
    KPIOverview,
    KPIPerformance,
    KPIReliability,
    KPITechnical,
    StepAnalytics,
    ToolAnalytics,
)

import structlog

logger = structlog.get_logger(__name__)


class AgentKPICalculator:
    """
    Compute comprehensive KPI reports from agent execution traces.

    Usage:
        calculator = AgentKPICalculator()
        report = calculator.evaluate_batch(responses)
    """

    def __init__(self) -> None:
        self._latencies: list[float] = []
        self._costs: list[float] = []
        self._statuses: list[AgentStatus] = []
        self._retry_counts: list[int] = []
        self._prompt_tokens: list[int] = []
        self._completion_tokens: list[int] = []
        self._cpu_times: list[float] = []
        self._memory_mbs: list[float] = []
        self._network_calls: list[int] = []
        self._responses: list[AgentRunResponseV1] = []
        self._errors_by_type: dict[str, int] = {}

        # Per-dimension collectors
        self._steps_by_name: dict[str, list[AgentRunResponseV1]] = {}
        self._tools_by_name: dict[str, list[AgentRunResponseV1]] = {}
        self._by_agent: dict[str, list[AgentRunResponseV1]] = {}
        self._by_workflow: dict[str, list[AgentRunResponseV1]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_batch(
        self,
        responses: list[AgentRunResponseV1],
        evaluation_id: str | None = None,
    ) -> AgentKPIReport:
        """
        Compute a full KPI report from a batch of agent responses.

        Args:
            responses: List of AgentRunResponseV1 objects
            evaluation_id: Optional custom evaluation identifier

        Returns:
            AgentKPIReport with all 7 categories populated
        """
        if not responses:
            raise ValueError("At least one response is required for evaluation")

        self._reset_state()
        self._responses = responses

        for resp in responses:
            self._ingest_response(resp)

        report = AgentKPIReport(
            evaluation_id=evaluation_id or f"eval_{uuid.uuid4().hex[:12]}",
            evaluated_at=datetime.utcnow(),
            agent_id=self._infer_agent_id(),
            workflow_id=self._infer_workflow_id(),
            run_count=len(responses),
            overview=self._compute_overview(),
            performance=self._compute_performance(),
            reliability=self._compute_reliability(),
            cost=self._compute_cost(),
            ai_usage=self._compute_ai_usage(),
            technical=self._compute_technical(),
            advanced=self._compute_advanced(),
            breakdowns=self._compute_breakdowns(),
        )

        logger.info(
            "agent_kpi_report_generated",
            evaluation_id=report.evaluation_id,
            run_count=report.run_count,
            success_rate=report.overview.success_rate,
        )
        return report

    # ------------------------------------------------------------------
    # Internal ingestion
    # ------------------------------------------------------------------

    def _reset_state(self) -> None:
        """Reset all internal accumulator state."""
        self._latencies.clear()
        self._costs.clear()
        self._statuses.clear()
        self._retry_counts.clear()
        self._prompt_tokens.clear()
        self._completion_tokens.clear()
        self._cpu_times.clear()
        self._memory_mbs.clear()
        self._network_calls.clear()
        self._responses = []
        self._errors_by_type.clear()
        self._steps_by_name.clear()
        self._tools_by_name.clear()
        self._by_agent.clear()
        self._by_workflow.clear()

    def _ingest_response(self, resp: AgentRunResponseV1) -> None:
        """Extract and classify metrics from a single response."""
        self._latencies.append(resp.latency_ms)
        self._statuses.append(resp.status)

        # Metrics block (may be flat or nested)
        metrics = resp.metrics or {}
        technical = metrics.get("technical", metrics)
        ai = metrics.get("ai", metrics)

        self._retry_counts.append(int(technical.get("retry_count", 0)))
        self._network_calls.append(int(technical.get("network_calls_count", 0)))

        if technical.get("cpu_time_ms") is not None:
            self._cpu_times.append(float(technical["cpu_time_ms"]))
        if technical.get("memory_mb") is not None:
            self._memory_mbs.append(float(technical["memory_mb"]))

        # AI metrics
        self._prompt_tokens.append(int(ai.get("prompt_tokens", 0)))
        self._completion_tokens.append(int(ai.get("completion_tokens", 0)))
        self._costs.append(float(ai.get("estimated_cost_usd", 0.0)))

        # Errors
        if resp.error:
            err_type = resp.error.type.value
            self._errors_by_type[err_type] = self._errors_by_type.get(err_type, 0) + 1

        # Dimension grouping
        self._by_agent.setdefault(resp.agent_id, []).append(resp)
        # Workflow ID may be in metadata or steps
        wf_id = resp.metadata.get("workflow_id") if resp.metadata else None
        if wf_id:
            self._by_workflow.setdefault(str(wf_id), []).append(resp)

        # Steps
        for step in resp.steps:
            self._steps_by_name.setdefault(step.step_name, []).append(resp)

        # Tools
        for tool in resp.tools:
            self._tools_by_name.setdefault(tool.tool_name, []).append(resp)

    # ------------------------------------------------------------------
    # Category calculators
    # ------------------------------------------------------------------

    def _compute_overview(self) -> KPIOverview:
        total = len(self._statuses)
        success = sum(1 for s in self._statuses if s == AgentStatus.SUCCESS)
        error = sum(1 for s in self._statuses if s == AgentStatus.FAILED)
        partial = sum(1 for s in self._statuses if s == AgentStatus.PARTIAL)
        return KPIOverview(
            total_runs=total,
            success_count=success,
            error_count=error,
            partial_count=partial,
            success_rate=success / total if total > 0 else 0.0,
        )

    def _compute_performance(self) -> KPIPerformance:
        arr = np.array(self._latencies, dtype=float)
        return KPIPerformance(
            avg_latency_ms=float(np.mean(arr)),
            min_latency_ms=float(np.min(arr)),
            max_latency_ms=float(np.max(arr)),
            p50_latency_ms=float(np.percentile(arr, 50)),
            p95_latency_ms=float(np.percentile(arr, 95)),
            p99_latency_ms=float(np.percentile(arr, 99)),
            std_latency_ms=float(np.std(arr)),
        )

    def _compute_reliability(self) -> KPIReliability:
        total = len(self._statuses)
        success = sum(1 for s in self._statuses if s == AgentStatus.SUCCESS)
        retries = sum(self._retry_counts)

        # MTBF: approximate as avg latency between failures
        mtbf = None
        failure_latencies = [
            r.latency_ms for r, s in zip(self._responses, self._statuses) if s == AgentStatus.FAILED
        ]
        if failure_latencies and len(failure_latencies) < total:
            mtbf = float(np.mean([r.latency_ms for r in self._responses if r.status == AgentStatus.SUCCESS]))

        return KPIReliability(
            success_rate=success / total if total > 0 else 0.0,
            error_rate=sum(1 for s in self._statuses if s == AgentStatus.FAILED) / total if total > 0 else 0.0,
            retry_rate=retries / total if total > 0 else 0.0,
            mean_time_between_failures_ms=mtbf,
            failure_types=dict(self._errors_by_type),
        )

    def _compute_cost(self) -> KPICost:
        total_cost = sum(self._costs)
        total_runs = len(self._costs)
        success_runs = sum(
            1 for r in self._responses if r.status == AgentStatus.SUCCESS
        )
        success_cost = sum(
            c for r, c in zip(self._responses, self._costs) if r.status == AgentStatus.SUCCESS
        )
        total_tokens = sum(self._prompt_tokens) + sum(self._completion_tokens)

        return KPICost(
            total_cost_usd=total_cost,
            avg_cost_per_run_usd=total_cost / total_runs if total_runs > 0 else 0.0,
            cost_per_success_usd=success_cost / success_runs if success_runs > 0 else 0.0,
            cost_per_token_usd=total_cost / total_tokens if total_tokens > 0 else None,
        )

    def _compute_ai_usage(self) -> KPIAIUsage:
        total_prompt = sum(self._prompt_tokens)
        total_completion = sum(self._completion_tokens)
        total = total_prompt + total_completion
        n = len(self._prompt_tokens)

        return KPIAIUsage(
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_completion,
            total_tokens=total,
            avg_prompt_tokens_per_run=total_prompt / n if n > 0 else 0.0,
            avg_completion_tokens_per_run=total_completion / n if n > 0 else 0.0,
            avg_tokens_per_run=total / n if n > 0 else 0.0,
        )

    def _compute_technical(self) -> KPITechnical:
        n = len(self._responses)
        return KPITechnical(
            avg_cpu_time_ms=float(np.mean(self._cpu_times)) if self._cpu_times else None,
            avg_memory_mb=float(np.mean(self._memory_mbs)) if self._memory_mbs else None,
            avg_network_calls=float(np.mean(self._network_calls)) if self._network_calls else 0.0,
            total_retries=sum(self._retry_counts),
        )

    def _compute_advanced(self) -> KPIAdvanced:
        # Most expensive agent
        most_expensive = None
        if self._by_agent:
            agent_costs = {
                aid: sum(
                    float(r.metrics.get("ai", r.metrics).get("estimated_cost_usd", 0.0))
                    for r in runs
                )
                for aid, runs in self._by_agent.items()
            }
            top_agent = max(agent_costs, key=agent_costs.get)
            most_expensive = {
                "agent_id": top_agent,
                "total_cost_usd": round(agent_costs[top_agent], 6),
            }

        # Step analytics
        step_analytics = self._build_step_analytics()
        slowest = None
        most_unstable = None
        if step_analytics:
            slowest = max(step_analytics, key=lambda s: s.avg_latency_ms)
            most_unstable = max(step_analytics, key=lambda s: s.instability_ms)

        # Tool analytics
        tool_analytics = self._build_tool_analytics()
        slowest_tool = None
        most_used_tool = None
        if tool_analytics:
            slowest_tool = max(tool_analytics, key=lambda t: t.avg_latency_ms)
            most_used_tool = max(tool_analytics, key=lambda t: t.usage_count)

        return KPIAdvanced(
            most_expensive_agent=most_expensive,
            slowest_step=slowest,
            most_unstable_step=most_unstable,
            slowest_tool=slowest_tool,
            most_used_tool=most_used_tool,
            step_efficiency_ratio=None,  # Requires optimal step count (external input)
        )

    def _compute_breakdowns(self) -> AgentBreakdown:
        # Latency by agent
        latency_by_agent = []
        for aid, runs in self._by_agent.items():
            latencies = [r.latency_ms for r in runs]
            latency_by_agent.append({
                "agent_id": aid,
                "avg_latency_ms": round(float(np.mean(latencies)), 2),
                "max_latency_ms": round(float(np.max(latencies)), 2),
                "run_count": len(runs),
            })

        # Cost by agent
        cost_by_agent = []
        for aid, runs in self._by_agent.items():
            cost = sum(
                float(r.metrics.get("ai", r.metrics).get("estimated_cost_usd", 0.0))
                for r in runs
            )
            cost_by_agent.append({
                "agent_id": aid,
                "total_cost_usd": round(cost, 6),
            })

        # Success rate by agent
        success_rate_by_agent = []
        for aid, runs in self._by_agent.items():
            success = sum(1 for r in runs if r.status == AgentStatus.SUCCESS)
            success_rate_by_agent.append({
                "agent_id": aid,
                "success_rate": round(success / len(runs), 4) if runs else 0.0,
                "total_runs": len(runs),
            })

        # Workflows
        workflows = []
        for wf_id, runs in self._by_workflow.items():
            latencies = [r.latency_ms for r in runs]
            success = sum(1 for r in runs if r.status == AgentStatus.SUCCESS)
            workflows.append({
                "workflow_id": wf_id,
                "workflow_success_rate": round(success / len(runs), 4) if runs else 0.0,
                "workflow_avg_latency_ms": round(float(np.mean(latencies)), 2) if latencies else 0.0,
                "total_runs": len(runs),
            })

        return AgentBreakdown(
            latency_by_agent=latency_by_agent,
            cost_by_agent=cost_by_agent,
            success_rate_by_agent=success_rate_by_agent,
            workflows=workflows,
            steps=self._build_step_analytics(),
            tools=self._build_tool_analytics(),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_step_analytics(self) -> list[StepAnalytics]:
        analytics: list[StepAnalytics] = []
        for step_name, responses in self._steps_by_name.items():
            latencies: list[float] = []
            failures = 0
            for resp in responses:
                for step in resp.steps:
                    if step.step_name == step_name:
                        lat = step.latency_ms
                        if lat is not None:
                            latencies.append(lat)
                        if step.status == AgentStatus.FAILED:
                            failures += 1

            if not latencies:
                continue

            arr = np.array(latencies, dtype=float)
            occurrences = len(latencies)
            analytics.append(StepAnalytics(
                step_name=step_name,
                avg_latency_ms=round(float(np.mean(arr)), 2),
                max_latency_ms=round(float(np.max(arr)), 2),
                min_latency_ms=round(float(np.min(arr)), 2),
                p95_latency_ms=round(float(np.percentile(arr, 95)), 2),
                failure_rate=round(failures / occurrences, 4) if occurrences > 0 else 0.0,
                success_rate=round(1 - (failures / occurrences), 4) if occurrences > 0 else 1.0,
                occurrence_count=occurrences,
                instability_ms=round(float(np.max(arr) - np.min(arr)), 2),
            ))
        return analytics

    def _build_tool_analytics(self) -> list[ToolAnalytics]:
        analytics: list[ToolAnalytics] = []
        for tool_name, responses in self._tools_by_name.items():
            latencies: list[float] = []
            failures = 0
            for resp in responses:
                for tool in resp.tools:
                    if tool.tool_name == tool_name:
                        lat = tool.latency_ms
                        if lat is not None:
                            latencies.append(lat)
                        if tool.status == AgentStatus.FAILED:
                            failures += 1

            if not latencies:
                continue

            arr = np.array(latencies, dtype=float)
            usage_count = len(latencies)
            analytics.append(ToolAnalytics(
                tool_name=tool_name,
                avg_latency_ms=round(float(np.mean(arr)), 2),
                max_latency_ms=round(float(np.max(arr)), 2),
                min_latency_ms=round(float(np.min(arr)), 2),
                usage_count=usage_count,
                failure_rate=round(failures / usage_count, 4) if usage_count > 0 else 0.0,
                success_rate=round(1 - (failures / usage_count), 4) if usage_count > 0 else 1.0,
            ))
        return analytics

    def _infer_agent_id(self) -> str | None:
        if len(self._by_agent) == 1:
            return list(self._by_agent.keys())[0]
        return None

    def _infer_workflow_id(self) -> str | None:
        if len(self._by_workflow) == 1:
            return list(self._by_workflow.keys())[0]
        return None
