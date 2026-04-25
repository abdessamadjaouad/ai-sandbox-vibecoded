// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/AgentEvaluationTesterPage.tsx
/**
 * Agent Evaluation Tester — Demo Interface
 *
 * A standalone, meeting-ready demonstration page for the Unified Agent API
 * Contract v1.0 and the Sandbox KPI Evaluation Engine.
 *
 * Features:
 *   • Interactive API Contract Explorer (request/response schemas)
 *   • Built-in Simulator (generates compliant agent responses)
 *   • One-click Evaluation (submits batch to Sandbox backend)
 *   • Full KPI Dashboard with visualizations
 */

import { useCallback, useState } from "react";
import type {
  AgentBatchEvaluationResponse,
  AgentRunResponseV1,
  AgentStatus,
} from "../types";

interface AgentEvaluationTesterPageProps {
  apiBaseUrl: string;
}

// ─── Demo Data Generators ───────────────────────────────────────────────────

const SCENARIOS = [
  { id: "success_standard", label: "✅ Success (Standard)", color: "var(--success)" },
  { id: "success_heavy", label: "✅ Success (Heavy Load)", color: "var(--dxc-blue)" },
  { id: "fail_technical", label: "❌ Failure (Technical)", color: "var(--error)" },
  { id: "fail_timeout", label: "❌ Failure (Timeout)", color: "var(--warning)" },
  { id: "fail_tool", label: "❌ Failure (Tool Rejected)", color: "var(--dxc-coral)" },
];

function generateAgentResponse(scenario: string, index: number): AgentRunResponseV1 {
  const runId = `demo_run_${String(index + 1).padStart(3, "0")}`;
  const agentId = "market_analysis_agent";
  const baseTime = new Date(Date.now() - (5 - index) * 60000).toISOString();

  const base: AgentRunResponseV1 = {
    run_id: runId,
    agent_id: agentId,
    agent_version: "1.2.0",
    status: "SUCCESS",
    output: { summary: `Market analysis batch ${index + 1} completed successfully.` },
    latency_ms: 420 + Math.floor(Math.random() * 200),
    started_at: baseTime,
    completed_at: new Date(new Date(baseTime).getTime() + 450).toISOString(),
    metrics: {
      technical: {
        cpu_time_ms: 180 + Math.floor(Math.random() * 100),
        memory_mb: 128 + Math.floor(Math.random() * 64),
        network_calls_count: 2,
        retry_count: 0,
      },
      ai: {
        prompt_tokens: 120 + Math.floor(Math.random() * 50),
        completion_tokens: 80 + Math.floor(Math.random() * 40),
        total_tokens: 200 + Math.floor(Math.random() * 90),
        estimated_cost_usd: 0.004 + Math.random() * 0.003,
        model_name: "gpt-4o-mini",
      },
    },
    steps: [
      {
        step_name: "validate_input",
        status: "SUCCESS" as AgentStatus,
        started_at: baseTime,
        completed_at: new Date(new Date(baseTime).getTime() + 35).toISOString(),
        latency_ms: 35,
        tool_used: null,
        output: "Input validated and sanitized",
        reasoning: null,
      },
      {
        step_name: "retrieve_context",
        status: "SUCCESS" as AgentStatus,
        started_at: new Date(new Date(baseTime).getTime() + 35).toISOString(),
        completed_at: new Date(new Date(baseTime).getTime() + 120).toISOString(),
        latency_ms: 85,
        tool_used: "vector_search",
        output: "Retrieved 3 relevant market reports",
        reasoning: null,
      },
      {
        step_name: "generate_analysis",
        status: "SUCCESS" as AgentStatus,
        started_at: new Date(new Date(baseTime).getTime() + 120).toISOString(),
        completed_at: new Date(new Date(baseTime).getTime() + 380).toISOString(),
        latency_ms: 260,
        tool_used: "mock_llm",
        output: "Analysis generated with citations",
        reasoning: "Using retrieved context to synthesize answer...",
      },
      {
        step_name: "format_output",
        status: "SUCCESS" as AgentStatus,
        started_at: new Date(new Date(baseTime).getTime() + 380).toISOString(),
        completed_at: new Date(new Date(baseTime).getTime() + 420).toISOString(),
        latency_ms: 40,
        tool_used: null,
        output: "JSON formatted output ready",
        reasoning: null,
      },
    ],
    tools: [
      {
        tool_name: "vector_search",
        status: "SUCCESS" as AgentStatus,
        started_at: new Date(new Date(baseTime).getTime() + 35).toISOString(),
        completed_at: new Date(new Date(baseTime).getTime() + 120).toISOString(),
        latency_ms: 85,
        input_params: { query: "Q2 2026 market trends", top_k: 3 },
        output_result: ["doc_1", "doc_2", "doc_3"],
        error_message: null,
      },
      {
        tool_name: "mock_llm",
        status: "SUCCESS" as AgentStatus,
        started_at: new Date(new Date(baseTime).getTime() + 120).toISOString(),
        completed_at: new Date(new Date(baseTime).getTime() + 380).toISOString(),
        latency_ms: 260,
        input_params: { prompt: "Analyze market trends based on context", max_tokens: 500 },
        output_result: "Market shows 12% growth in Q2...",
        error_message: null,
      },
    ],
    error: null,
    metadata: { scenario, demo_index: index, source: "sandbox_tester" },
  };

  // Apply scenario modifications
  if (scenario === "success_heavy") {
    base.latency_ms = 2800 + Math.floor(Math.random() * 400);
    base.metrics!.technical!.memory_mb = 512 + Math.floor(Math.random() * 256);
    base.metrics!.technical!.network_calls_count = 5;
    base.metrics!.ai!.prompt_tokens = 450;
    base.metrics!.ai!.completion_tokens = 320;
    base.metrics!.ai!.estimated_cost_usd = 0.018;
    base.metrics!.ai!.model_name = "gpt-4";
    base.steps![2].latency_ms = 2100;
    base.tools![1].latency_ms = 2100;
  } else if (scenario === "fail_technical") {
    base.status = "FAILED";
    base.output = null;
    base.error = {
      type: "TECHNICAL",
      message: "LLM inference failed after 2 retries: connection reset",
      step: "generate_analysis",
      traceback: "Traceback (most recent call last):\n  File...",
      recoverable: true,
    };
    base.steps![2].status = "FAILED";
    base.steps![2].output = null;
    base.tools![1].status = "FAILED";
    base.tools![1].error_message = "Connection reset by peer";
    base.metrics!.technical!.retry_count = 2;
  } else if (scenario === "fail_timeout") {
    base.status = "FAILED";
    base.latency_ms = 30000;
    base.output = null;
    base.error = {
      type: "TIMEOUT",
      message: "Agent exceeded configured timeout (30000ms)",
      step: "generate_analysis",
      traceback: null,
      recoverable: true,
    };
    base.steps![2].status = "FAILED";
    base.steps![2].completed_at = new Date(new Date(baseTime).getTime() + 30000).toISOString();
    base.steps![2].latency_ms = 29920;
    base.tools![1].status = "FAILED";
    base.tools![1].completed_at = new Date(new Date(baseTime).getTime() + 30000).toISOString();
    base.tools![1].latency_ms = 29920;
    base.tools![1].error_message = "Request timeout after 30s";
  } else if (scenario === "fail_tool") {
    base.status = "FAILED";
    base.output = null;
    base.error = {
      type: "TOOL_REJECTED",
      message: "Attempted to use unauthorized tool: external_api_v2",
      step: "retrieve_context",
      traceback: null,
      recoverable: false,
    };
    base.steps![1].status = "FAILED";
    base.steps![1].tool_used = "external_api_v2";
    base.tools![0].tool_name = "external_api_v2";
    base.tools![0].status = "FAILED";
    base.tools![0].error_message = "Tool not in allowlist";
    base.tools = [base.tools![0]]; // Remove LLM tool since we failed earlier
  }

  return base;
}

// ─── Sub-components ─────────────────────────────────────────────────────────

const Section = ({ title, children, className = "" }: { title: string; children: React.ReactNode; className?: string }) => (
  <section className={`tester-section glass-card ${className}`}>
    <h3 className="section-title">{title}</h3>
    {children}
  </section>
);

const JsonBlock = ({ data }: { data: unknown }) => (
  <pre className="json-block">{JSON.stringify(data, null, 2)}</pre>
);

const Badge = ({ text, color }: { text: string; color: string }) => (
  <span className="demo-badge" style={{ color, borderColor: color, background: `${color}15` }}>
    {text}
  </span>
);

// ─── Main Page ──────────────────────────────────────────────────────────────

export const AgentEvaluationTesterPage = ({ apiBaseUrl }: AgentEvaluationTesterPageProps) => {
  const [activeTab, setActiveTab] = useState<"contract" | "simulator" | "results">("contract");
  const [responses, setResponses] = useState<AgentRunResponseV1[]>([]);
  const [batchSize, setBatchSize] = useState(5);
  const [selectedScenario, setSelectedScenario] = useState("mixed");
  const [evaluating, setEvaluating] = useState(false);
  const [result, setResult] = useState<AgentBatchEvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Contract Data ───────────────────────────────────────────────────────
  const contract = {
    version: "1.0.0",
    endpoint: "POST /v1/run-agent",
    standards: ["ISO/IEC 25010:2023", "IEEE 1012-2016", "MLCommons AI Efficiency"],
    request_fields: [
      { name: "run_id", type: "string", required: true, description: "Unique execution identifier" },
      { name: "agent_id", type: "string", required: true, description: "Agent identifier in catalogue" },
      { name: "agent_version", type: "string", required: false, description: "Semantic version (default: 1.0.0)" },
      { name: "input", type: "string | object", required: true, description: "Primary task input" },
      { name: "expected_output", type: "string", required: false, description: "Ground truth for accuracy KPI" },
      { name: "context", type: "object", required: false, description: "workflow_id, step_id, previous_output, session_id" },
      { name: "config", type: "object", required: false, description: "temperature, max_tokens, timeout_ms, max_steps, enable_cot" },
      { name: "allowed_tools", type: "string[]", required: false, description: "Tool allowlist enforced by Sandbox" },
      { name: "metadata", type: "object", required: false, description: "Audit metadata (user_id, source)" },
    ],
    response_fields: [
      { name: "run_id", type: "string", required: true, description: "Echo of request run_id" },
      { name: "agent_id", type: "string", required: true, description: "Echo of request agent_id" },
      { name: "status", type: "SUCCESS | FAILED | PARTIAL", required: true, description: "Global execution status" },
      { name: "output", type: "any", required: true, description: "Final agent output" },
      { name: "latency_ms", type: "number", required: true, description: "Total execution latency (ms)" },
      { name: "started_at", type: "ISO-8601", required: true, description: "Run start timestamp" },
      { name: "completed_at", type: "ISO-8601", required: true, description: "Run end timestamp" },
      { name: "metrics", type: "object", required: true, description: "technical {cpu_time_ms, memory_mb, network_calls_count, retry_count} + ai {prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd, model_name}" },
      { name: "steps", type: "StepDetail[]", required: false, description: "Ordered execution trace" },
      { name: "tools", type: "ToolCall[]", required: false, description: "Tool invocation log" },
      { name: "error", type: "ErrorDetail", required: false, description: "Structured error (mandatory if FAILED)" },
    ],
  };

  // ── Actions ─────────────────────────────────────────────────────────────

  const generateBatch = useCallback(() => {
    const batch: AgentRunResponseV1[] = [];
    for (let i = 0; i < batchSize; i++) {
      const scenario = selectedScenario === "mixed"
        ? SCENARIOS[Math.floor(Math.random() * SCENARIOS.length)].id
        : selectedScenario;
      batch.push(generateAgentResponse(scenario, i));
    }
    setResponses(batch);
    setResult(null);
    setError(null);
  }, [batchSize, selectedScenario]);

  const evaluateBatch = useCallback(async () => {
    if (responses.length === 0) return;
    setEvaluating(true);
    setError(null);
    try {
      const res = await fetch(`${apiBaseUrl}/evaluation/agent/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ responses }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
      setActiveTab("results");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  }, [responses, apiBaseUrl]);

  const clearAll = useCallback(() => {
    setResponses([]);
    setResult(null);
    setError(null);
  }, []);

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="agent-tester-page">
      {/* Header */}
      <div className="tester-hero">
        <p className="eyebrow">AI Sandbox — Agent Evaluation Demo</p>
        <h1>Unified Agent API Contract v1.0</h1>
        <p className="subtitle">
          Demonstration of the standardized agent integration contract, KPI measurement engine,
          and ISO/IEC 25010 aligned scoring for production readiness assessment.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="tester-tabs">
        {[
          { id: "contract", label: "📋 API Contract" },
          { id: "simulator", label: "🔬 Simulator & Evaluator" },
          { id: "results", label: "📊 Results", disabled: !result },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`tester-tab ${activeTab === tab.id ? "is-active" : ""} ${tab.disabled ? "is-disabled" : ""}`}
            onClick={() => !tab.disabled && setActiveTab(tab.id as typeof activeTab)}
            disabled={tab.disabled}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ─── CONTRACT TAB ──────────────────────────────────────────────── */}
      {activeTab === "contract" && (
        <div className="tester-content">
          <Section title="Contract Overview">
            <div className="contract-meta">
              <Badge text={`Version ${contract.version}`} color="var(--dxc-blue)" />
              <Badge text={contract.endpoint} color="var(--dxc-coral)" />
              {contract.standards.map((s) => (
                <Badge key={s} text={s} color="var(--success)" />
              ))}
            </div>
            <p className="contract-description">
              This contract defines the <strong>mandatory</strong> request/response schema that all
              external agent projects must implement to integrate with the AI Sandbox evaluation layer.
              Compliance ensures reliable KPI computation, cross-team interoperability, and
              standards-aligned production readiness scoring.
            </p>
          </Section>

          <div className="contract-grid">
            <Section title="Request Schema (POST /v1/run-agent)">
              <table className="contract-table">
                <thead>
                  <tr><th>Field</th><th>Type</th><th>Required</th><th>Description</th></tr>
                </thead>
                <tbody>
                  {contract.request_fields.map((f) => (
                    <tr key={f.name} className={f.required ? "is-required" : ""}>
                      <td><code>{f.name}</code></td>
                      <td><span className="type-tag">{f.type}</span></td>
                      <td>{f.required ? "✅ Yes" : "No"}</td>
                      <td>{f.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>

            <Section title="Response Schema (Agent → Sandbox)">
              <table className="contract-table">
                <thead>
                  <tr><th>Field</th><th>Type</th><th>Required</th><th>Description</th></tr>
                </thead>
                <tbody>
                  {contract.response_fields.map((f) => (
                    <tr key={f.name} className={f.required ? "is-required" : ""}>
                      <td><code>{f.name}</code></td>
                      <td><span className="type-tag">{f.type}</span></td>
                      <td>{f.required ? "✅ Yes" : "No"}</td>
                      <td>{f.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          </div>

          <Section title="Example Request">
            <JsonBlock data={{
              run_id: "run_abc123",
              agent_id: "market_agent",
              agent_version: "1.0.0",
              input: "Analyze Q2 2026 market trends for fintech sector",
              expected_output: "Fintech market grew 12% in Q2 2026...",
              context: { workflow_id: "wf_123", step_id: "step_1" },
              config: { temperature: 0.7, max_tokens: 1000, timeout_ms: 30000 },
              allowed_tools: ["vector_search", "calculator", "news_api"],
              metadata: { user_id: "user_1", source: "sandbox" },
            }} />
          </Section>

          <Section title="Example Response">
            <JsonBlock data={{
              run_id: "run_abc123",
              agent_id: "market_agent",
              agent_version: "1.0.0",
              status: "SUCCESS",
              output: { summary: "Fintech sector shows 12% QoQ growth..." },
              latency_ms: 1450,
              started_at: "2026-04-24T10:00:00Z",
              completed_at: "2026-04-24T10:00:01.450Z",
              metrics: {
                technical: { cpu_time_ms: 420, memory_mb: 256, network_calls_count: 2, retry_count: 0 },
                ai: { prompt_tokens: 350, completion_tokens: 180, total_tokens: 530, estimated_cost_usd: 0.0085, model_name: "gpt-4" },
              },
              steps: [
                { step_name: "validate_input", status: "SUCCESS", started_at: "2026-04-24T10:00:00Z", completed_at: "2026-04-24T10:00:00.050Z", latency_ms: 50 },
                { step_name: "retrieve_context", status: "SUCCESS", started_at: "2026-04-24T10:00:00.050Z", completed_at: "2026-04-24T10:00:00.350Z", latency_ms: 300, tool_used: "vector_search" },
                { step_name: "generate_analysis", status: "SUCCESS", started_at: "2026-04-24T10:00:00.350Z", completed_at: "2026-04-24T10:00:01.300Z", latency_ms: 950, tool_used: "mock_llm" },
                { step_name: "format_output", status: "SUCCESS", started_at: "2026-04-24T10:00:01.300Z", completed_at: "2026-04-24T10:00:01.450Z", latency_ms: 150 },
              ],
              tools: [
                { tool_name: "vector_search", status: "SUCCESS", started_at: "2026-04-24T10:00:00.050Z", completed_at: "2026-04-24T10:00:00.350Z", latency_ms: 300 },
                { tool_name: "mock_llm", status: "SUCCESS", started_at: "2026-04-24T10:00:00.350Z", completed_at: "2026-04-24T10:00:01.300Z", latency_ms: 950 },
              ],
              error: null,
              metadata: {},
            }} />
          </Section>
        </div>
      )}

      {/* ─── SIMULATOR TAB ─────────────────────────────────────────────── */}
      {activeTab === "simulator" && (
        <div className="tester-content">
          <Section title="1. Configure Test Batch">
            <div className="simulator-config">
              <div className="config-field">
                <label>Batch Size</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={batchSize}
                  onChange={(e) => setBatchSize(Math.min(50, Math.max(1, parseInt(e.target.value) || 1)))}
                  className="config-input"
                />
              </div>
              <div className="config-field">
                <label>Scenario</label>
                <select
                  value={selectedScenario}
                  onChange={(e) => setSelectedScenario(e.target.value)}
                  className="config-select"
                >
                  <option value="mixed">🎲 Mixed (Random)</option>
                  {SCENARIOS.map((s) => (
                    <option key={s.id} value={s.id}>{s.label}</option>
                  ))}
                </select>
              </div>
              <div className="config-actions">
                <button type="button" className="btn btn-primary" onClick={generateBatch}>
                  Generate Batch
                </button>
                <button type="button" className="btn btn-ghost" onClick={clearAll}>
                  Clear
                </button>
              </div>
            </div>
          </Section>

          {responses.length > 0 && (
            <>
              <Section title={`2. Generated Responses (${responses.length})`}>
                <div className="response-summary-bar">
                  <span>✅ Success: {responses.filter((r) => r.status === "SUCCESS").length}</span>
                  <span>❌ Failed: {responses.filter((r) => r.status === "FAILED").length}</span>
                  <span>⏱️ Avg Latency: {Math.round(responses.reduce((a, r) => a + r.latency_ms, 0) / responses.length)}ms</span>
                  <span>💰 Total Cost: ${responses.reduce((a, r) => a + (r.metrics?.ai?.estimated_cost_usd || 0), 0).toFixed(4)}</span>
                </div>
                <div className="response-list">
                  {responses.map((resp) => (
                    <div key={resp.run_id} className={`response-card ${resp.status === "FAILED" ? "is-failed" : ""}`}>
                      <div className="response-header">
                        <code>{resp.run_id}</code>
                        <Badge
                          text={resp.status}
                          color={resp.status === "SUCCESS" ? "var(--success)" : "var(--error)"}
                        />
                        <span className="response-latency">{resp.latency_ms}ms</span>
                      </div>
                      <div className="response-body">
                        <div className="response-mini">
                          <span>Agent: <strong>{resp.agent_id}</strong></span>
                          <span>Steps: {resp.steps?.length || 0}</span>
                          <span>Tools: {resp.tools?.length || 0}</span>
                          <span>Tokens: {resp.metrics?.ai?.total_tokens || 0}</span>
                          <span>Cost: ${(resp.metrics?.ai?.estimated_cost_usd || 0).toFixed(4)}</span>
                        </div>
                        {resp.error && (
                          <div className="response-error-mini">
                            ⚠️ {resp.error.type}: {resp.error.message}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Section>

              <Section title="3. Raw JSON (Editable)">
                <textarea
                  className="agent-json-input"
                  rows={12}
                  value={JSON.stringify(responses, null, 2)}
                  onChange={(e) => {
                    try {
                      setResponses(JSON.parse(e.target.value));
                      setError(null);
                    } catch {
                      // Invalid JSON, ignore while typing
                    }
                  }}
                />
              </Section>

              <Section title="4. Evaluate">
                <div className="evaluate-actions">
                  <button
                    type="button"
                    className="btn btn-brand btn-lg"
                    onClick={evaluateBatch}
                    disabled={evaluating || responses.length === 0}
                  >
                    {evaluating ? "Evaluating..." : "▶ Run Evaluation"}
                  </button>
                  <p className="evaluate-hint">
                    Submits batch to <code>POST {apiBaseUrl}/evaluation/agent/batch</code>
                  </p>
                </div>
                {error && <div className="error-banner">{error}</div>}
              </Section>
            </>
          )}
        </div>
      )}

      {/* ─── RESULTS TAB ───────────────────────────────────────────────── */}
      {activeTab === "results" && result && (
        <div className="tester-content">
          {/* Judgment Hero */}
          <div className={`judgment-hero judgment-${result.judgment.judgment.toLowerCase()}`}>
            <div className="judgment-badge-xl">
              {result.judgment.judgment === "EXCELLENT" && "✅"}
              {result.judgment.judgment === "ACCEPTABLE" && "🟡"}
              {result.judgment.judgment === "MARGINAL" && "🟠"}
              {result.judgment.judgment === "FAIL" && "🔴"}
              {" "}{result.judgment.judgment}
            </div>
            <div className="judgment-score-xl">
              {result.judgment.global_score.toFixed(1)}<span>/100</span>
            </div>
            <div className="judgment-confidence">
              Confidence: {(result.judgment.confidence * 100).toFixed(1)}% · {result.raw_responses_count} runs evaluated
            </div>
            <p className="judgment-recommendation">{result.judgment.recommendation}</p>
          </div>

          {/* KPI Grid */}
          <Section title="Key Performance Indicators">
            <div className="kpi-grid-large">
              <KpiCard
                title="Success Rate"
                value={`${(result.kpi_report.overview.success_rate * 100).toFixed(1)}%`}
                subtitle={`${result.kpi_report.overview.success_count}/${result.kpi_report.overview.total_runs} runs`}
                color="var(--success)"
              />
              <KpiCard
                title="Avg Latency"
                value={`${result.kpi_report.performance.avg_latency_ms.toFixed(0)}ms`}
                subtitle={`P95: ${result.kpi_report.performance.p95_latency_ms.toFixed(0)}ms`}
                color="var(--dxc-blue)"
              />
              <KpiCard
                title="Total Cost"
                value={`$${result.kpi_report.cost.total_cost_usd.toFixed(4)}`}
                subtitle={`$${result.kpi_report.cost.avg_cost_per_run_usd.toFixed(4)}/run`}
                color="var(--dxc-coral)"
              />
              <KpiCard
                title="Total Tokens"
                value={result.kpi_report.ai_usage.total_tokens.toLocaleString()}
                subtitle={`${result.kpi_report.ai_usage.avg_tokens_per_run.toFixed(0)}/run`}
                color="var(--dxc-purple)"
              />
              <KpiCard
                title="Error Rate"
                value={`${(result.kpi_report.reliability.error_rate * 100).toFixed(1)}%`}
                subtitle={`${result.kpi_report.overview.error_count} failures`}
                color="var(--error)"
              />
              <KpiCard
                title="Retry Rate"
                value={`${(result.kpi_report.reliability.retry_rate * 100).toFixed(1)}%`}
                subtitle={`${result.kpi_report.technical.total_retries} retries`}
                color="var(--warning)"
              />
            </div>
          </Section>

          {/* Category Scores */}
          <Section title="Category Scores (ISO/IEC 25010)">
            <div className="category-scores">
              {result.judgment.category_scores.map((cs) => (
                <div key={cs.category} className="category-score-row">
                  <div className="category-info">
                    <span className="category-name">{cs.category}</span>
                    <span className="category-weight">{(cs.weight * 100).toFixed(0)}%</span>
                  </div>
                  <div className="category-bar-track">
                    <div
                      className="category-bar-fill"
                      style={{ width: `${cs.score}%`, background: getScoreColor(cs.score) }}
                    />
                  </div>
                  <span className="category-score-value">{cs.score.toFixed(1)}</span>
                </div>
              ))}
            </div>
          </Section>

          {/* Standards Compliance */}
          <Section title="Standards Compliance">
            <div className="compliance-grid">
              {Object.entries(result.judgment.standards_compliance).map(([clause, compliant]) => (
                <div key={clause} className={`compliance-item ${compliant ? "is-compliant" : ""}`}>
                  <span className="compliance-icon">{compliant ? "✅" : "❌"}</span>
                  <span className="compliance-name">{clause.replace(/_/g, " ")}</span>
                </div>
              ))}
            </div>
          </Section>

          {/* Detailed Tables */}
          <Section title="Step Breakdown">
            {result.kpi_report.breakdowns.steps.length > 0 ? (
              <table className="kpi-table">
                <thead>
                  <tr>
                    <th>Step</th><th>Avg (ms)</th><th>P95 (ms)</th><th>Min (ms)</th><th>Max (ms)</th>
                    <th>Instability</th><th>Success</th><th>Occurrences</th>
                  </tr>
                </thead>
                <tbody>
                  {result.kpi_report.breakdowns.steps.map((s) => (
                    <tr key={s.step_name}>
                      <td><strong>{s.step_name}</strong></td>
                      <td>{s.avg_latency_ms.toFixed(0)}</td>
                      <td>{s.p95_latency_ms.toFixed(0)}</td>
                      <td>{s.min_latency_ms.toFixed(0)}</td>
                      <td>{s.max_latency_ms.toFixed(0)}</td>
                      <td>{s.instability_ms.toFixed(0)}ms</td>
                      <td>{(s.success_rate * 100).toFixed(0)}%</td>
                      <td>{s.occurrence_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p className="muted">No step data available.</p>}
          </Section>

          <Section title="Tool Breakdown">
            {result.kpi_report.breakdowns.tools.length > 0 ? (
              <table className="kpi-table">
                <thead>
                  <tr><th>Tool</th><th>Avg (ms)</th><th>Max (ms)</th><th>Usage</th><th>Failure</th><th>Success</th></tr>
                </thead>
                <tbody>
                  {result.kpi_report.breakdowns.tools.map((t) => (
                    <tr key={t.tool_name}>
                      <td><strong>{t.tool_name}</strong></td>
                      <td>{t.avg_latency_ms.toFixed(0)}</td>
                      <td>{t.max_latency_ms.toFixed(0)}</td>
                      <td>{t.usage_count}</td>
                      <td>{(t.failure_rate * 100).toFixed(1)}%</td>
                      <td>{(t.success_rate * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p className="muted">No tool data available.</p>}
          </Section>

          {/* Risk & Violations */}
          {result.judgment.blocking_violations.length > 0 && (
            <Section title="Blocking Violations">
              <ul className="violation-list">
                {result.judgment.blocking_violations.map((v, i) => (
                  <li key={i} className="violation-item">⚠️ {v}</li>
                ))}
              </ul>
            </Section>
          )}

          <Section title="Risk Assessment">
            <div className="risk-box">
              {result.judgment.risk_assessment}
            </div>
          </Section>

          {/* Raw Reports */}
          <Section title="Raw JSON Report">
            <JsonBlock data={result.json_report} />
          </Section>

          <Section title="Markdown Report">
            <pre className="markdown-report">{result.markdown_report}</pre>
          </Section>
        </div>
      )}
    </div>
  );
};

// ─── Helpers ────────────────────────────────────────────────────────────────

function getScoreColor(score: number): string {
  if (score >= 85) return "var(--success)";
  if (score >= 70) return "var(--dxc-blue)";
  if (score >= 50) return "var(--warning)";
  return "var(--error)";
}

function KpiCard({
  title,
  value,
  subtitle,
  color,
}: {
  title: string;
  value: string | number;
  subtitle: string;
  color: string;
}) {
  return (
    <div className="kpi-card-large glass-card">
      <div className="kpi-card-title">{title}</div>
      <div className="kpi-card-value" style={{ color }}>
        {value}
      </div>
      <div className="kpi-card-subtitle">{subtitle}</div>
    </div>
  );
}
