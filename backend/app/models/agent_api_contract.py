"""
Unified Agent API Contract — Version 1.0

This module defines the standardized request/response schemas that ALL external
agent projects must implement to integrate with the AI Sandbox evaluation layer.

Standards alignment:
- ISO/IEC 25010: Performance Efficiency, Reliability, Functional Suitability
- IEEE 1012: Verification & Validation traceability requirements
- MLCommons AI Efficiency: Cost and token tracking

Usage:
    from backend.app.models.agent_api_contract import (
        AgentRunRequestV1,
        AgentRunResponseV1,
        AgentKPIReport,
    )
"""

import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================


class AgentStatus(str, enum.Enum):
    """Global execution status of an agent run."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class AgentErrorType(str, enum.Enum):
    """Standardized error taxonomy for agent failures."""

    TECHNICAL = "TECHNICAL"
    BUSINESS = "BUSINESS"
    TIMEOUT = "TIMEOUT"
    EXTERNAL_API = "EXTERNAL_API"
    TOOL_REJECTED = "TOOL_REJECTED"
    VALIDATION = "VALIDATION"


class JudgmentLevel(str, enum.Enum):
    """Production-readiness judgment aligned with IEEE 1012 V&V levels."""

    EXCELLENT = "EXCELLENT"      # ≥ 85 — Exceeds production benchmarks
    ACCEPTABLE = "ACCEPTABLE"    # 70–84 — Meets minimum production criteria
    MARGINAL = "MARGINAL"        # 50–69 — Requires remediation
    FAIL = "FAIL"                # < 50 — Unsuitable for production


# =============================================================================
# Request Contract — POST /v1/run-agent
# =============================================================================


class AgentRunContext(BaseModel):
    """Execution context propagated through workflow steps."""

    workflow_id: str | None = Field(
        None, description="Parent workflow identifier (if part of a workflow)"
    )
    step_id: str | None = Field(
        None, description="Current step identifier within the workflow"
    )
    previous_output: Any = Field(
        None, description="Output from the previous workflow step"
    )
    session_id: str | None = Field(
        None, description="User session identifier for traceability"
    )


class AgentRunConfig(BaseModel):
    """Dynamic execution parameters."""

    temperature: float = Field(0.7, ge=0.0, le=2.0, description="LLM sampling temperature")
    max_tokens: int = Field(1000, ge=1, le=32000, description="Maximum tokens to generate")
    timeout_ms: int = Field(30000, ge=1000, le=300000, description="Request timeout in milliseconds")
    max_steps: int | None = Field(None, ge=1, le=100, description="Maximum reasoning steps allowed")
    enable_cot: bool = Field(True, description="Enable Chain-of-Thought logging")


class AgentRunRequestV1(BaseModel):
    """
    Standardized request payload for agent execution.

    Mandatory fields per Section 13.3 of the Sandbox Technical Specification.
    """

    run_id: str = Field(..., description="Unique execution identifier (UUID preferred)")
    agent_id: str = Field(..., description="Agent identifier registered in the Sandbox catalogue")
    agent_version: str = Field("1.0.0", description="Semantic version of the agent")
    input: str | dict[str, Any] = Field(..., description="Primary task input (text or structured)")
    expected_output: str | None = Field(
        None, description="Ground truth for Task Success Rate and Accuracy KPI calculation"
    )
    context: AgentRunContext = Field(
        default_factory=AgentRunContext, description="Workflow and session context"
    )
    config: AgentRunConfig = Field(
        default_factory=AgentRunConfig, description="Dynamic execution parameters"
    )
    allowed_tools: list[str] = Field(
        default_factory=list, description="Tool allowlist enforced by Sandbox"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Audit and tracking metadata (user_id, source, etc.)"
    )

    @field_validator("run_id")
    @classmethod
    def validate_run_id(cls, v: str) -> str:
        if not v or len(v.strip()) < 3:
            raise ValueError("run_id must be at least 3 characters")
        return v


# =============================================================================
# Response Contract — Agent → Sandbox
# =============================================================================


class AgentTechnicalMetrics(BaseModel):
    """Infrastructure-level metrics."""

    cpu_time_ms: float | None = Field(None, ge=0, description="Total CPU time consumed")
    memory_mb: float | None = Field(None, ge=0, description="Peak memory consumption")
    network_calls_count: int = Field(0, ge=0, description="Number of external network calls")
    retry_count: int = Field(0, ge=0, description="Number of automatic retries performed")


class AgentAIMetrics(BaseModel):
    """AI/LLM consumption metrics."""

    prompt_tokens: int = Field(0, ge=0, description="Input/prompt tokens consumed")
    completion_tokens: int = Field(0, ge=0, description="Output/completion tokens generated")
    total_tokens: int = Field(0, ge=0, description="Total token count")
    estimated_cost_usd: float = Field(0.0, ge=0.0, description="Estimated execution cost in USD")
    model_name: str | None = Field(None, description="Actual model used for inference")


class AgentStepDetail(BaseModel):
    """Individual step within the agent execution trace."""

    step_name: str = Field(..., description="Human-readable step identifier")
    status: AgentStatus = Field(..., description="Step execution status")
    started_at: datetime = Field(..., description="Step start timestamp (ISO 8601)")
    completed_at: datetime = Field(..., description="Step end timestamp (ISO 8601)")
    latency_ms: float | None = Field(None, ge=0, description="Computed step latency in ms")
    tool_used: str | None = Field(None, description="Tool invoked during this step")
    output: str | None = Field(None, description="Step output snapshot")
    reasoning: str | None = Field(None, description="Chain-of-Thought reasoning (if enabled)")

    @field_validator("latency_ms", mode="before")
    @classmethod
    def compute_latency(cls, v: float | None, info) -> float | None:
        if v is not None:
            return v
        data = info.data
        if "started_at" in data and "completed_at" in data:
            try:
                start = data["started_at"]
                end = data["completed_at"]
                if isinstance(start, str):
                    start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                if isinstance(end, str):
                    end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                return (end - start).total_seconds() * 1000
            except Exception:
                return None
        return None


class AgentToolCall(BaseModel):
    """Recorded tool invocation."""

    tool_name: str = Field(..., description="Name of the invoked tool")
    status: AgentStatus = Field(..., description="Tool execution status")
    started_at: datetime = Field(..., description="Tool call start timestamp")
    completed_at: datetime = Field(..., description="Tool call end timestamp")
    latency_ms: float | None = Field(None, ge=0, description="Computed tool latency in ms")
    input_params: dict[str, Any] = Field(default_factory=dict, description="Tool input parameters")
    output_result: Any = Field(None, description="Tool output result")
    error_message: str | None = Field(None, description="Error details if tool failed")

    @field_validator("latency_ms", mode="before")
    @classmethod
    def compute_latency(cls, v: float | None, info) -> float | None:
        if v is not None:
            return v
        data = info.data
        if "started_at" in data and "completed_at" in data:
            try:
                start = data["started_at"]
                end = data["completed_at"]
                if isinstance(start, str):
                    start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                if isinstance(end, str):
                    end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                return (end - start).total_seconds() * 1000
            except Exception:
                return None
        return None


class AgentErrorDetail(BaseModel):
    """Structured error information (mandatory when status = FAILED)."""

    type: AgentErrorType = Field(..., description="Error taxonomy category")
    message: str = Field(..., description="Human-readable error description")
    step: str | None = Field(None, description="Step where the error occurred")
    traceback: str | None = Field(None, description="Technical traceback (if applicable)")
    recoverable: bool = Field(False, description="Whether the error is recoverable")


class AgentRunResponseV1(BaseModel):
    """
    Standardized response payload from an agent to the Sandbox.

    Mandatory fields per Section 13.4 of the Sandbox Technical Specification.
    """

    run_id: str = Field(..., description="Echo of the request run_id")
    agent_id: str = Field(..., description="Echo of the request agent_id")
    agent_version: str = Field("1.0.0", description="Echo of the request agent_version")
    status: AgentStatus = Field(..., description="Global execution status")
    output: Any = Field(..., description="Final agent output")
    latency_ms: float = Field(..., ge=0, description="Total execution latency in milliseconds")
    started_at: datetime = Field(..., description="Run start timestamp (ISO 8601)")
    completed_at: datetime = Field(..., description="Run end timestamp (ISO 8601)")
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured metrics block (technical + ai sub-dicts expected)",
    )
    steps: list[AgentStepDetail] = Field(
        default_factory=list, description="Ordered execution trace"
    )
    tools: list[AgentToolCall] = Field(
        default_factory=list, description="Tool invocation log"
    )
    error: AgentErrorDetail | None = Field(
        None, description="Error details (mandatory if status = FAILED)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific metadata"
    )


# =============================================================================
# KPI Report Schemas — Sandbox Output
# =============================================================================


class KPIOverview(BaseModel):
    """High-level execution summary."""

    total_runs: int = Field(..., ge=0)
    success_count: int = Field(..., ge=0)
    error_count: int = Field(..., ge=0)
    partial_count: int = Field(0, ge=0)
    success_rate: float = Field(..., ge=0.0, le=1.0)


class KPIPerformance(BaseModel):
    """Latency and timing statistics."""

    avg_latency_ms: float = Field(..., ge=0)
    min_latency_ms: float = Field(..., ge=0)
    max_latency_ms: float = Field(..., ge=0)
    p50_latency_ms: float = Field(..., ge=0)
    p95_latency_ms: float = Field(..., ge=0)
    p99_latency_ms: float = Field(..., ge=0)
    std_latency_ms: float = Field(..., ge=0)


class KPIReliability(BaseModel):
    """Reliability and stability metrics (ISO/IEC 25010 Reliability)."""

    success_rate: float = Field(..., ge=0.0, le=1.0)
    error_rate: float = Field(..., ge=0.0, le=1.0)
    retry_rate: float = Field(..., ge=0.0, le=1.0)
    mean_time_between_failures_ms: float | None = Field(None, ge=0)
    failure_types: dict[str, int] = Field(default_factory=dict)


class KPICost(BaseModel):
    """Cost efficiency metrics (MLCommons AI Efficiency aligned)."""

    total_cost_usd: float = Field(..., ge=0.0)
    avg_cost_per_run_usd: float = Field(..., ge=0.0)
    cost_per_success_usd: float = Field(..., ge=0.0)
    cost_per_token_usd: float | None = Field(None, ge=0.0)


class KPIAIUsage(BaseModel):
    """AI/LLM consumption aggregates."""

    total_prompt_tokens: int = Field(..., ge=0)
    total_completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)
    avg_prompt_tokens_per_run: float = Field(..., ge=0.0)
    avg_completion_tokens_per_run: float = Field(..., ge=0.0)
    avg_tokens_per_run: float = Field(..., ge=0.0)


class KPITechnical(BaseModel):
    """Infrastructure consumption aggregates."""

    avg_cpu_time_ms: float | None = Field(None, ge=0.0)
    avg_memory_mb: float | None = Field(None, ge=0.0)
    avg_network_calls: float = Field(..., ge=0.0)
    total_retries: int = Field(..., ge=0)


class StepAnalytics(BaseModel):
    """Per-step advanced analytics."""

    step_name: str = Field(...)
    avg_latency_ms: float = Field(..., ge=0.0)
    max_latency_ms: float = Field(..., ge=0.0)
    min_latency_ms: float = Field(..., ge=0.0)
    p95_latency_ms: float = Field(..., ge=0.0)
    failure_rate: float = Field(..., ge=0.0, le=1.0)
    success_rate: float = Field(..., ge=0.0, le=1.0)
    occurrence_count: int = Field(..., ge=0)
    instability_ms: float = Field(..., ge=0.0, description="max - min latency = variance measure")


class ToolAnalytics(BaseModel):
    """Per-tool advanced analytics."""

    tool_name: str = Field(...)
    avg_latency_ms: float = Field(..., ge=0.0)
    max_latency_ms: float = Field(..., ge=0.0)
    min_latency_ms: float = Field(..., ge=0.0)
    usage_count: int = Field(..., ge=0)
    failure_rate: float = Field(..., ge=0.0, le=1.0)
    success_rate: float = Field(..., ge=0.0, le=1.0)


class KPIAdvanced(BaseModel):
    """Advanced diagnostic analytics."""

    most_expensive_agent: dict[str, Any] | None = Field(None)
    slowest_step: StepAnalytics | None = Field(None)
    most_unstable_step: StepAnalytics | None = Field(None)
    slowest_tool: ToolAnalytics | None = Field(None)
    most_used_tool: ToolAnalytics | None = Field(None)
    step_efficiency_ratio: float | None = Field(
        None, ge=0.0, description="Optimal steps / actual steps (if optimal known)"
    )


class AgentBreakdown(BaseModel):
    """Breakdowns by dimension."""

    latency_by_agent: list[dict[str, Any]] = Field(default_factory=list)
    cost_by_agent: list[dict[str, Any]] = Field(default_factory=list)
    success_rate_by_agent: list[dict[str, Any]] = Field(default_factory=list)
    workflows: list[dict[str, Any]] = Field(default_factory=list)
    steps: list[StepAnalytics] = Field(default_factory=list)
    tools: list[ToolAnalytics] = Field(default_factory=list)


class AgentKPIReport(BaseModel):
    """
    Complete KPI evaluation report produced by the Sandbox.

    Mirrors the expected JSON structure from the user's specification.
    """

    evaluation_id: str = Field(..., description="Unique evaluation run identifier")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str | None = Field(None, description="Agent identifier (single-agent eval)")
    workflow_id: str | None = Field(None, description="Workflow identifier (workflow eval)")
    run_count: int = Field(..., ge=0)

    overview: KPIOverview
    performance: KPIPerformance
    reliability: KPIReliability
    cost: KPICost
    ai_usage: KPIAIUsage
    technical: KPITechnical
    advanced: KPIAdvanced
    breakdowns: AgentBreakdown


# =============================================================================
# Scoring & Judgment Schemas
# =============================================================================


class CategoryScore(BaseModel):
    """Score breakdown per ISO/IEC 25010 quality characteristic."""

    category: str = Field(..., description="Quality characteristic name")
    score: float = Field(..., ge=0.0, le=100.0, description="Normalized score 0-100")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight in global score")
    weighted_score: float = Field(..., ge=0.0, le=100.0)
    interpretation: str = Field(..., description="Human-readable interpretation")
    standard_reference: str = Field(..., description="ISO/IEC 25010 or IEEE 1012 clause")


class AgentEvaluationJudgment(BaseModel):
    """
    Final scoring and judgment for an agent evaluation.

    Aligned with IEEE 1012 V&V levels and ISO/IEC 25010 quality model.
    """

    evaluation_id: str = Field(...)
    global_score: float = Field(..., ge=0.0, le=100.0, description="Weighted composite score 0-100")
    judgment: JudgmentLevel = Field(..., description="Production-readiness verdict")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Statistical confidence based on sample size")
    category_scores: list[CategoryScore] = Field(default_factory=list)
    blocking_violations: list[str] = Field(default_factory=list)
    recommendation: str = Field(..., description="Actionable recommendation")
    risk_assessment: str = Field(..., description="Production deployment risk summary")
    standards_compliance: dict[str, bool] = Field(
        default_factory=dict,
        description="ISO/IEC 25010 clause compliance checklist",
    )


# =============================================================================
# Batch Evaluation Schemas
# =============================================================================


class AgentBatchEvaluationRequest(BaseModel):
    """Submit multiple agent responses for batch KPI calculation."""

    responses: list[AgentRunResponseV1] = Field(..., min_length=1, max_length=10000)
    expected_outputs: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of run_id → expected output for accuracy calculation",
    )
    scoring_weights: dict[str, float] | None = Field(
        None, description="Optional custom scoring weights"
    )
    constraints: dict[str, Any] | None = Field(
        None, description="Constraint thresholds (max_latency_ms, min_success_rate, etc.)"
    )


class AgentBatchEvaluationResponse(BaseModel):
    """Batch evaluation result with KPI report + judgment."""

    evaluation_id: str = Field(...)
    kpi_report: AgentKPIReport
    judgment: AgentEvaluationJudgment
    raw_responses_count: int = Field(..., ge=0)
    markdown_report: str = Field(..., description="Human-readable Markdown report")
    json_report: dict[str, Any] = Field(..., description="Machine-readable JSON report")
