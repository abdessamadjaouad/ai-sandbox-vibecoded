#!/usr/bin/env python3
"""
Agent API Simulator — Unified Contract Compliant Server

A local FastAPI server that simulates AI agent responses conforming to
the AI Sandbox Unified Agent API Contract v1.0.

Usage (server mode):
    python scripts/agent_api_simulator.py --mode server --port 9001

Usage (batch generation mode):
    python scripts/agent_api_simulator.py --mode batch --count 10 --output ./data/agent_simulations/

Supported scenarios:
    success_standard   : Baseline compliant response
    success_heavy_load : High latency, high token usage
    failure_technical  : TECHNICAL error at step level
    failure_timeout    : TIMEOUT error
    failure_tool       : Tool not in allowlist
    mixed              : Random mix for batch evaluation
"""

import argparse
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta
from typing import Any

# Ensure project root is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.models.agent_api_contract import (
    AgentAIMetrics,
    AgentErrorDetail,
    AgentErrorType,
    AgentRunRequestV1,
    AgentRunResponseV1,
    AgentStatus,
    AgentStepDetail,
    AgentTechnicalMetrics,
    AgentToolCall,
)


def _now() -> datetime:
    return datetime.utcnow()


def _make_latency(base_ms: float, variance: float = 0.2) -> float:
    """Generate realistic latency with log-normal distribution."""
    sigma = variance
    mu = base_ms / 1000.0
    return max(10.0, random.lognormvariate(mu, sigma) * 1000)


def _make_tokens(input_chars: int) -> tuple[int, int]:
    """Estimate prompt/completion tokens from input size."""
    prompt = max(50, int(input_chars * 0.25) + random.randint(-20, 20))
    completion = max(30, int(prompt * random.uniform(0.3, 0.8)))
    return prompt, completion


# =============================================================================
# Scenario Generators
# =============================================================================

def generate_success_standard(request: AgentRunRequestV1) -> AgentRunResponseV1:
    """Baseline successful agent response."""
    start = _now()
    input_text = str(request.input)
    input_len = len(input_text)

    prompt_tok, comp_tok = _make_tokens(input_len)
    cost = round((prompt_tok + comp_tok) * 0.00002, 6)

    step1_end = start + timedelta(milliseconds=_make_latency(30, 0.3))
    step2_end = step1_end + timedelta(milliseconds=_make_latency(400, 0.4))
    end = step2_end + timedelta(milliseconds=_make_latency(20, 0.2))

    latency_ms = (end - start).total_seconds() * 1000

    return AgentRunResponseV1(
        run_id=request.run_id,
        agent_id=request.agent_id,
        agent_version=request.agent_version,
        status=AgentStatus.SUCCESS,
        output={"summary": f"Processed: {input_text[:60]}...", "result": "ok"},
        latency_ms=round(latency_ms, 2),
        started_at=start,
        completed_at=end,
        metrics={
            "technical": {
                "cpu_time_ms": round(latency_ms * 0.3, 2),
                "memory_mb": random.uniform(64, 256),
                "network_calls_count": 1,
                "retry_count": 0,
            },
            "ai": {
                "prompt_tokens": prompt_tok,
                "completion_tokens": comp_tok,
                "total_tokens": prompt_tok + comp_tok,
                "estimated_cost_usd": cost,
                "model_name": "gpt-4o-mini",
            },
        },
        steps=[
            AgentStepDetail(
                step_name="validate_input",
                status=AgentStatus.SUCCESS,
                started_at=start,
                completed_at=step1_end,
                tool_used=None,
                output="Input validated",
            ),
            AgentStepDetail(
                step_name="generate_response",
                status=AgentStatus.SUCCESS,
                started_at=step1_end,
                completed_at=step2_end,
                tool_used="mock_llm",
                output="Response generated",
            ),
            AgentStepDetail(
                step_name="format_output",
                status=AgentStatus.SUCCESS,
                started_at=step2_end,
                completed_at=end,
                tool_used=None,
                output="Output formatted",
            ),
        ],
        tools=[
            AgentToolCall(
                tool_name="mock_llm",
                status=AgentStatus.SUCCESS,
                started_at=step1_end,
                completed_at=step2_end,
                input_params={"prompt": input_text[:100]},
                output_result="Generated text",
            ),
        ],
        error=None,
        metadata={"scenario": "success_standard", "workflow_id": request.context.workflow_id},
    )


def generate_success_heavy_load(request: AgentRunRequestV1) -> AgentRunResponseV1:
    """High latency, high token usage scenario."""
    start = _now()
    input_text = str(request.input)
    input_len = len(input_text)

    prompt_tok = max(500, int(input_len * 0.5))
    comp_tok = max(400, int(prompt_tok * random.uniform(0.8, 1.2)))
    cost = round((prompt_tok + comp_tok) * 0.00005, 6)

    step1_end = start + timedelta(milliseconds=_make_latency(100, 0.5))
    step2_end = step1_end + timedelta(milliseconds=_make_latency(2500, 0.5))
    step3_end = step2_end + timedelta(milliseconds=_make_latency(800, 0.4))
    end = step3_end + timedelta(milliseconds=_make_latency(100, 0.3))

    latency_ms = (end - start).total_seconds() * 1000

    return AgentRunResponseV1(
        run_id=request.run_id,
        agent_id=request.agent_id,
        agent_version=request.agent_version,
        status=AgentStatus.SUCCESS,
        output={"summary": f"Heavy analysis: {input_text[:60]}...", "result": "ok"},
        latency_ms=round(latency_ms, 2),
        started_at=start,
        completed_at=end,
        metrics={
            "technical": {
                "cpu_time_ms": round(latency_ms * 0.4, 2),
                "memory_mb": random.uniform(512, 1024),
                "network_calls_count": 3,
                "retry_count": 1,
            },
            "ai": {
                "prompt_tokens": prompt_tok,
                "completion_tokens": comp_tok,
                "total_tokens": prompt_tok + comp_tok,
                "estimated_cost_usd": cost,
                "model_name": "gpt-4",
            },
        },
        steps=[
            AgentStepDetail(
                step_name="validate_input",
                status=AgentStatus.SUCCESS,
                started_at=start,
                completed_at=step1_end,
            ),
            AgentStepDetail(
                step_name="deep_analysis",
                status=AgentStatus.SUCCESS,
                started_at=step1_end,
                completed_at=step2_end,
                tool_used="mock_llm",
            ),
            AgentStepDetail(
                step_name="post_process",
                status=AgentStatus.SUCCESS,
                started_at=step2_end,
                completed_at=step3_end,
                tool_used="data_transformer",
            ),
            AgentStepDetail(
                step_name="format_output",
                status=AgentStatus.SUCCESS,
                started_at=step3_end,
                completed_at=end,
            ),
        ],
        tools=[
            AgentToolCall(
                tool_name="mock_llm",
                status=AgentStatus.SUCCESS,
                started_at=step1_end,
                completed_at=step2_end,
            ),
            AgentToolCall(
                tool_name="data_transformer",
                status=AgentStatus.SUCCESS,
                started_at=step2_end,
                completed_at=step3_end,
            ),
        ],
        error=None,
        metadata={"scenario": "success_heavy_load", "workflow_id": request.context.workflow_id},
    )


def generate_failure_technical(request: AgentRunRequestV1) -> AgentRunResponseV1:
    """Technical error during step execution."""
    start = _now()
    input_text = str(request.input)

    step1_end = start + timedelta(milliseconds=_make_latency(40, 0.3))
    step2_end = step1_end + timedelta(milliseconds=_make_latency(200, 0.4))
    end = step2_end + timedelta(milliseconds=_make_latency(20, 0.2))

    latency_ms = (end - start).total_seconds() * 1000

    return AgentRunResponseV1(
        run_id=request.run_id,
        agent_id=request.agent_id,
        agent_version=request.agent_version,
        status=AgentStatus.FAILED,
        output=None,
        latency_ms=round(latency_ms, 2),
        started_at=start,
        completed_at=end,
        metrics={
            "technical": {
                "cpu_time_ms": round(latency_ms * 0.35, 2),
                "memory_mb": random.uniform(128, 512),
                "network_calls_count": 1,
                "retry_count": 2,
            },
            "ai": {
                "prompt_tokens": 120,
                "completion_tokens": 0,
                "total_tokens": 120,
                "estimated_cost_usd": 0.0024,
                "model_name": "gpt-4o-mini",
            },
        },
        steps=[
            AgentStepDetail(
                step_name="validate_input",
                status=AgentStatus.SUCCESS,
                started_at=start,
                completed_at=step1_end,
            ),
            AgentStepDetail(
                step_name="generate_response",
                status=AgentStatus.FAILED,
                started_at=step1_end,
                completed_at=step2_end,
                tool_used="mock_llm",
                output=None,
            ),
        ],
        tools=[
            AgentToolCall(
                tool_name="mock_llm",
                status=AgentStatus.FAILED,
                started_at=step1_end,
                completed_at=step2_end,
                error_message="Connection reset by peer",
            ),
        ],
        error=AgentErrorDetail(
            type=AgentErrorType.TECHNICAL,
            message="LLM inference failed after 2 retries",
            step="generate_response",
            recoverable=True,
        ),
        metadata={"scenario": "failure_technical", "workflow_id": request.context.workflow_id},
    )


def generate_failure_timeout(request: AgentRunRequestV1) -> AgentRunResponseV1:
    """Timeout error scenario."""
    start = _now()
    timeout_ms = request.config.timeout_ms if request.config else 30000
    end = start + timedelta(milliseconds=timeout_ms + random.randint(100, 500))
    latency_ms = (end - start).total_seconds() * 1000

    return AgentRunResponseV1(
        run_id=request.run_id,
        agent_id=request.agent_id,
        agent_version=request.agent_version,
        status=AgentStatus.FAILED,
        output=None,
        latency_ms=round(latency_ms, 2),
        started_at=start,
        completed_at=end,
        metrics={
            "technical": {
                "cpu_time_ms": round(latency_ms * 0.1, 2),
                "memory_mb": random.uniform(64, 128),
                "network_calls_count": 0,
                "retry_count": 0,
            },
            "ai": {
                "prompt_tokens": 80,
                "completion_tokens": 0,
                "total_tokens": 80,
                "estimated_cost_usd": 0.0016,
                "model_name": "gpt-4o-mini",
            },
        },
        steps=[
            AgentStepDetail(
                step_name="validate_input",
                status=AgentStatus.SUCCESS,
                started_at=start,
                completed_at=start + timedelta(milliseconds=50),
            ),
            AgentStepDetail(
                step_name="generate_response",
                status=AgentStatus.FAILED,
                started_at=start + timedelta(milliseconds=50),
                completed_at=end,
                tool_used="mock_llm",
            ),
        ],
        tools=[
            AgentToolCall(
                tool_name="mock_llm",
                status=AgentStatus.FAILED,
                started_at=start + timedelta(milliseconds=50),
                completed_at=end,
                error_message="Request timeout",
            ),
        ],
        error=AgentErrorDetail(
            type=AgentErrorType.TIMEOUT,
            message=f"Agent exceeded configured timeout ({timeout_ms}ms)",
            step="generate_response",
            recoverable=True,
        ),
        metadata={"scenario": "failure_timeout", "workflow_id": request.context.workflow_id},
    )


def generate_failure_tool(request: AgentRunRequestV1) -> AgentRunResponseV1:
    """Tool rejected (not in allowlist) scenario."""
    start = _now()
    step1_end = start + timedelta(milliseconds=_make_latency(30, 0.3))
    step2_end = step1_end + timedelta(milliseconds=_make_latency(100, 0.4))
    end = step2_end + timedelta(milliseconds=_make_latency(15, 0.2))
    latency_ms = (end - start).total_seconds() * 1000

    return AgentRunResponseV1(
        run_id=request.run_id,
        agent_id=request.agent_id,
        agent_version=request.agent_version,
        status=AgentStatus.FAILED,
        output=None,
        latency_ms=round(latency_ms, 2),
        started_at=start,
        completed_at=end,
        metrics={
            "technical": {
                "cpu_time_ms": round(latency_ms * 0.3, 2),
                "memory_mb": random.uniform(64, 128),
                "network_calls_count": 0,
                "retry_count": 0,
            },
            "ai": {
                "prompt_tokens": 100,
                "completion_tokens": 0,
                "total_tokens": 100,
                "estimated_cost_usd": 0.002,
                "model_name": "gpt-4o-mini",
            },
        },
        steps=[
            AgentStepDetail(
                step_name="validate_input",
                status=AgentStatus.SUCCESS,
                started_at=start,
                completed_at=step1_end,
            ),
            AgentStepDetail(
                step_name="select_tool",
                status=AgentStatus.FAILED,
                started_at=step1_end,
                completed_at=step2_end,
                tool_used="unauthorized_api",
            ),
        ],
        tools=[
            AgentToolCall(
                tool_name="unauthorized_api",
                status=AgentStatus.FAILED,
                started_at=step1_end,
                completed_at=step2_end,
                error_message="Tool not in allowlist",
            ),
        ],
        error=AgentErrorDetail(
            type=AgentErrorType.TOOL_REJECTED,
            message="Attempted to use unauthorized tool: unauthorized_api",
            step="select_tool",
            recoverable=False,
        ),
        metadata={"scenario": "failure_tool", "workflow_id": request.context.workflow_id},
    )


SCENARIO_HANDLERS = {
    "success_standard": generate_success_standard,
    "success_heavy_load": generate_success_heavy_load,
    "failure_technical": generate_failure_technical,
    "failure_timeout": generate_failure_timeout,
    "failure_tool": generate_failure_tool,
}


def pick_scenario(scenario: str | None = None) -> str:
    if scenario and scenario in SCENARIO_HANDLERS:
        return scenario
    if scenario == "mixed":
        return random.choice(list(SCENARIO_HANDLERS.keys()))
    return "success_standard"


# =============================================================================
# FastAPI Server
# =============================================================================

def create_app() -> Any:
    try:
        from fastapi import FastAPI, HTTPException, Header
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError:
        print("ERROR: fastapi not installed. Run: pip install fastapi uvicorn")
        sys.exit(1)

    app = FastAPI(
        title="Agent API Simulator",
        description="Simulates AI agent responses compliant with AI Sandbox Unified API Contract v1.0",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": "agent-api-simulator"}

    @app.post("/v1/run-agent", response_model=AgentRunResponseV1)
    async def run_agent(
        request: AgentRunRequestV1,
        x_scenario: str | None = Header(None, description="Override scenario"),
    ) -> AgentRunResponseV1:
        """
        Simulate agent execution.

        Accepts a standardized request and returns a compliant response.
        Use X-Scenario header to force a specific scenario.
        """
        scenario = pick_scenario(x_scenario)
        handler = SCENARIO_HANDLERS[scenario]
        return handler(request)

    @app.get("/v1/scenarios")
    async def list_scenarios() -> dict[str, Any]:
        """List available simulation scenarios."""
        return {
            "scenarios": [
                {"id": k, "description": v.__doc__.strip() if v.__doc__ else k}
                for k, v in SCENARIO_HANDLERS.items()
            ],
            "mixed": "Randomly selects from all scenarios (useful for batch testing)",
        }

    @app.get("/v1/contract")
    async def get_contract() -> dict[str, Any]:
        """Return the API contract schema."""
        return {
            "version": "1.0.0",
            "endpoint": "POST /v1/run-agent",
            "request_schema": AgentRunRequestV1.model_json_schema(),
            "response_schema": AgentRunResponseV1.model_json_schema(),
        }

    return app


# =============================================================================
# Batch Generation Mode
# =============================================================================

def generate_batch(
    count: int,
    scenario: str = "mixed",
    agent_id: str = "market_agent",
    workflow_id: str | None = None,
) -> list[AgentRunResponseV1]:
    """Generate a batch of simulated responses."""
    responses: list[AgentRunResponseV1] = []
    for i in range(count):
        picked = pick_scenario(scenario)
        handler = SCENARIO_HANDLERS[picked]

        request = AgentRunRequestV1(
            run_id=f"run_{uuid.uuid4().hex[:8]}",
            agent_id=agent_id,
            agent_version="1.0.0",
            input=f"Test input scenario {picked} batch {i+1}",
            context=AgentRunRequestV1.__fields__["context"].default_factory(),
        )
        if workflow_id:
            request.context.workflow_id = workflow_id

        resp = handler(request)
        responses.append(resp)

    return responses


def save_batch(
    responses: list[AgentRunResponseV1],
    output_dir: str,
    filename: str | None = None,
) -> str:
    """Save batch responses as JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    fname = filename or f"agent_simulations_{_now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(output_dir, fname)

    data = [r.model_dump(mode="json") for r in responses]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return path


# =============================================================================
# CLI Entrypoint
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Agent API Simulator")
    parser.add_argument(
        "--mode",
        choices=["server", "batch"],
        default="server",
        help="Run mode: server (FastAPI) or batch (generate JSON files)",
    )
    parser.add_argument("--port", type=int, default=9002, help="Server port")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host")
    parser.add_argument("--count", type=int, default=10, help="Batch count")
    parser.add_argument("--scenario", type=str, default="mixed", help="Scenario name")
    parser.add_argument("--output", type=str, default="./data/agent_simulations", help="Output directory")
    parser.add_argument("--agent-id", type=str, default="market_agent", help="Agent identifier")
    parser.add_argument("--workflow-id", type=str, default=None, help="Workflow identifier")
    args = parser.parse_args()

    if args.mode == "server":
        try:
            import uvicorn
        except ImportError:
            print("ERROR: uvicorn not installed. Run: pip install uvicorn")
            sys.exit(1)

        app = create_app()
        print(f"🚀 Agent API Simulator starting at http://{args.host}:{args.port}")
        print(f"   POST /v1/run-agent  → Simulate agent execution")
        print(f"   GET  /v1/scenarios  → List available scenarios")
        print(f"   GET  /v1/contract   → View API contract")
        print(f"   GET  /health        → Health check")
        uvicorn.run(app, host=args.host, port=args.port)

    elif args.mode == "batch":
        print(f"📦 Generating {args.count} responses (scenario={args.scenario})...")
        responses = generate_batch(
            count=args.count,
            scenario=args.scenario,
            agent_id=args.agent_id,
            workflow_id=args.workflow_id,
        )
        path = save_batch(responses, args.output)
        print(f"✅ Saved {len(responses)} responses to: {path}")

        # Print summary
        success = sum(1 for r in responses if r.status == AgentStatus.SUCCESS)
        failed = sum(1 for r in responses if r.status == AgentStatus.FAILED)
        print(f"   Success: {success} | Failed: {failed}")


if __name__ == "__main__":
    main()
