// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/AgentEvaluationPage.tsx
import { useCallback, useState } from "react";
import type {
  AgentBatchEvaluationResponse,
  AgentKPIReport,
  AgentEvaluationJudgment,
  StepAnalytics,
  ToolAnalytics,
} from "../types";

interface AgentEvaluationPageProps {
  onEvaluate: (jsonInput: string) => Promise<AgentBatchEvaluationResponse>;
  onLoadExample: () => string;
  loading: boolean;
  error: string | null;
}

const JUDGMENT_STYLES: Record<string, { badge: string; color: string; bg: string }> = {
  EXCELLENT: { badge: "✅ EXCELLENT", color: "var(--success)", bg: "var(--success-soft)" },
  ACCEPTABLE: { badge: "🟡 ACCEPTABLE", color: "var(--warning)", bg: "var(--warning-soft)" },
  MARGINAL: { badge: "🟠 MARGINAL", color: "var(--dxc-coral)", bg: "rgba(255,120,78,0.1)" },
  FAIL: { badge: "🔴 FAIL", color: "var(--error)", bg: "var(--error-soft)" },
};

export const AgentEvaluationPage = ({
  onEvaluate,
  onLoadExample,
  loading,
  error,
}: AgentEvaluationPageProps) => {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<AgentBatchEvaluationResponse | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "performance" | "reliability" | "cost" | "ai" | "technical" | "advanced" | "breakdowns" | "judgment" | "report"
  >("overview");

  const handleEvaluate = useCallback(async () => {
    if (!input.trim()) return;
    try {
      const res = await onEvaluate(input);
      setResult(res);
      setActiveTab("overview");
    } catch {
      // Error handled by parent
    }
  }, [input, onEvaluate]);

  const handleLoadExample = useCallback(() => {
    setInput(onLoadExample());
  }, [onLoadExample]);

  const handleClear = useCallback(() => {
    setInput("");
    setResult(null);
  }, []);

  return (
    <div className="agent-evaluation-page">
      <div className="page-header">
        <p className="eyebrow">AI Sandbox — Agent Evaluation</p>
        <h1>Agent KPI Dashboard</h1>
        <p className="subtitle">
          Submit agent API responses to compute KPIs, scoring, and production-readiness judgment
          aligned with ISO/IEC 25010 and IEEE 1012.
        </p>
      </div>

      {/* Input Section */}
      <div className="glass-card input-card">
        <h3>Submit Agent Responses</h3>
        <p className="muted">
          Paste a JSON array of AgentRunResponseV1 objects, or a single object. 
          The sandbox will compute KPIs and generate a full evaluation report.
        </p>
        <textarea
          className="agent-json-input"
          rows={12}
          placeholder='[{"run_id": "run_1", "agent_id": "market_agent", "status": "SUCCESS", ...}]'
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        {error && <div className="error-banner">{error}</div>}
        <div className="input-actions">
          <button type="button" className="btn btn-ghost" onClick={handleLoadExample} disabled={loading}>
            Load Example
          </button>
          <button type="button" className="btn btn-ghost" onClick={handleClear} disabled={loading}>
            Clear
          </button>
          <button type="button" className="btn btn-primary" onClick={handleEvaluate} disabled={loading || !input.trim()}>
            {loading ? "Evaluating..." : "Evaluate Agent"}
          </button>
        </div>
      </div>

      {/* Results Section */}
      {result && (
        <div className="evaluation-results">
          {/* Judgment Header */}
          <JudgmentHeader judgment={result.judgment} kpiReport={result.kpi_report} />

          {/* Tab Navigation */}
          <div className="tab-nav">
            {[
              { id: "overview", label: "Overview" },
              { id: "performance", label: "Performance" },
              { id: "reliability", label: "Reliability" },
              { id: "cost", label: "Cost" },
              { id: "ai", label: "AI Usage" },
              { id: "technical", label: "Technical" },
              { id: "advanced", label: "Advanced" },
              { id: "breakdowns", label: "Breakdowns" },
              { id: "judgment", label: "Judgment" },
              { id: "report", label: "Full Report" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`tab-btn ${activeTab === tab.id ? "is-active" : ""}`}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="tab-content glass-card">
            {activeTab === "overview" && <OverviewTab report={result.kpi_report} />}
            {activeTab === "performance" && <PerformanceTab report={result.kpi_report} />}
            {activeTab === "reliability" && <ReliabilityTab report={result.kpi_report} />}
            {activeTab === "cost" && <CostTab report={result.kpi_report} />}
            {activeTab === "ai" && <AIUsageTab report={result.kpi_report} />}
            {activeTab === "technical" && <TechnicalTab report={result.kpi_report} />}
            {activeTab === "advanced" && <AdvancedTab report={result.kpi_report} />}
            {activeTab === "breakdowns" && <BreakdownsTab report={result.kpi_report} />}
            {activeTab === "judgment" && <JudgmentTab judgment={result.judgment} />}
            {activeTab === "report" && <ReportTab markdown={result.markdown_report} />}
          </div>
        </div>
      )}
    </div>
  );
};

// =============================================================================
// Sub-components
// =============================================================================

const JudgmentHeader = ({
  judgment,
  kpiReport,
}: {
  judgment: AgentEvaluationJudgment;
  kpiReport: AgentKPIReport;
}) => {
  const style = JUDGMENT_STYLES[judgment.judgment] || JUDGMENT_STYLES.FAIL;
  return (
    <div className="glass-card judgment-header" style={{ borderColor: style.color }}>
      <div className="judgment-badge" style={{ color: style.color, background: style.bg }}>
        {style.badge}
      </div>
      <div className="judgment-score">
        <span className="score-value" style={{ color: style.color }}>
          {judgment.global_score.toFixed(1)}
        </span>
        <span className="score-max">/ 100</span>
      </div>
      <div className="judgment-meta">
        <span>Confidence: {(judgment.confidence * 100).toFixed(1)}%</span>
        <span>Runs: {kpiReport.run_count}</span>
        <span>Success: {(kpiReport.overview.success_rate * 100).toFixed(1)}%</span>
      </div>
      <p className="judgment-recommendation">{judgment.recommendation}</p>
    </div>
  );
};

const OverviewTab = ({ report }: { report: AgentKPIReport }) => (
  <div className="kpi-grid">
    <MetricCard title="Total Runs" value={report.overview.total_runs} />
    <MetricCard title="Successful" value={report.overview.success_count} color="var(--success)" />
    <MetricCard title="Failed" value={report.overview.error_count} color="var(--error)" />
    <MetricCard title="Success Rate" value={`${(report.overview.success_rate * 100).toFixed(1)}%`} />
    <MetricCard title="Avg Latency" value={`${report.performance.avg_latency_ms.toFixed(0)} ms`} />
    <MetricCard title="P95 Latency" value={`${report.performance.p95_latency_ms.toFixed(0)} ms`} />
    <MetricCard title="Total Cost" value={`$${report.cost.total_cost_usd.toFixed(4)}`} />
    <MetricCard title="Total Tokens" value={report.ai_usage.total_tokens.toLocaleString()} />
  </div>
);

const PerformanceTab = ({ report }: { report: AgentKPIReport }) => (
  <div className="kpi-section">
    <h4>Latency Statistics (ISO/IEC 25010 §8.1)</h4>
    <table className="kpi-table">
      <thead>
        <tr><th>Metric</th><th>Value (ms)</th></tr>
      </thead>
      <tbody>
        <tr><td>Average</td><td>{report.performance.avg_latency_ms.toFixed(1)}</td></tr>
        <tr><td>Minimum</td><td>{report.performance.min_latency_ms.toFixed(1)}</td></tr>
        <tr><td>Maximum</td><td>{report.performance.max_latency_ms.toFixed(1)}</td></tr>
        <tr><td>P50 (Median)</td><td>{report.performance.p50_latency_ms.toFixed(1)}</td></tr>
        <tr><td>P95</td><td>{report.performance.p95_latency_ms.toFixed(1)}</td></tr>
        <tr><td>P99</td><td>{report.performance.p99_latency_ms.toFixed(1)}</td></tr>
        <tr><td>Std Dev</td><td>{report.performance.std_latency_ms.toFixed(1)}</td></tr>
      </tbody>
    </table>
    <LatencyBarChart performance={report.performance} />
  </div>
);

const ReliabilityTab = ({ report }: { report: AgentKPIReport }) => (
  <div className="kpi-section">
    <h4>Reliability Metrics (ISO/IEC 25010 §8.6)</h4>
    <div className="kpi-grid">
      <MetricCard title="Success Rate" value={`${(report.reliability.success_rate * 100).toFixed(1)}%`} color="var(--success)" />
      <MetricCard title="Error Rate" value={`${(report.reliability.error_rate * 100).toFixed(1)}%`} color="var(--error)" />
      <MetricCard title="Retry Rate" value={`${(report.reliability.retry_rate * 100).toFixed(1)}%`} />
      {report.reliability.mean_time_between_failures_ms && (
        <MetricCard title="MTBF" value={`${report.reliability.mean_time_between_failures_ms.toFixed(0)} ms`} />
      )}
    </div>
    {Object.keys(report.reliability.failure_types).length > 0 && (
      <>
        <h5>Failure Type Distribution</h5>
        <table className="kpi-table">
          <thead><tr><th>Type</th><th>Count</th></tr></thead>
          <tbody>
            {Object.entries(report.reliability.failure_types).map(([type, count]) => (
              <tr key={type}><td>{type}</td><td>{count}</td></tr>
            ))}
          </tbody>
        </table>
      </>
    )}
  </div>
);

const CostTab = ({ report }: { report: AgentKPIReport }) => (
  <div className="kpi-section">
    <h4>Cost Efficiency (MLCommons)</h4>
    <div className="kpi-grid">
      <MetricCard title="Total Cost" value={`$${report.cost.total_cost_usd.toFixed(6)}`} />
      <MetricCard title="Avg Cost / Run" value={`$${report.cost.avg_cost_per_run_usd.toFixed(6)}`} />
      <MetricCard title="Cost / Success" value={`$${report.cost.cost_per_success_usd.toFixed(6)}`} />
      {report.cost.cost_per_token_usd && (
        <MetricCard title="Cost / Token" value={`$${report.cost.cost_per_token_usd.toFixed(8)}`} />
      )}
    </div>
  </div>
);

const AIUsageTab = ({ report }: { report: AgentKPIReport }) => (
  <div className="kpi-section">
    <h4>AI / LLM Usage</h4>
    <div className="kpi-grid">
      <MetricCard title="Prompt Tokens" value={report.ai_usage.total_prompt_tokens.toLocaleString()} />
      <MetricCard title="Completion Tokens" value={report.ai_usage.total_completion_tokens.toLocaleString()} />
      <MetricCard title="Total Tokens" value={report.ai_usage.total_tokens.toLocaleString()} />
      <MetricCard title="Avg / Run" value={report.ai_usage.avg_tokens_per_run.toFixed(1)} />
    </div>
  </div>
);

const TechnicalTab = ({ report }: { report: AgentKPIReport }) => (
  <div className="kpi-section">
    <h4>Technical Metrics</h4>
    <div className="kpi-grid">
      {report.technical.avg_cpu_time_ms !== null && (
        <MetricCard title="Avg CPU Time" value={`${report.technical.avg_cpu_time_ms.toFixed(1)} ms`} />
      )}
      {report.technical.avg_memory_mb !== null && (
        <MetricCard title="Avg Memory" value={`${report.technical.avg_memory_mb.toFixed(1)} MB`} />
      )}
      <MetricCard title="Avg Network Calls" value={report.technical.avg_network_calls.toFixed(1)} />
      <MetricCard title="Total Retries" value={report.technical.total_retries} />
    </div>
  </div>
);

const AdvancedTab = ({ report }: { report: AgentKPIReport }) => (
  <div className="kpi-section">
    <h4>Advanced Analytics</h4>
    {report.advanced.most_expensive_agent && (
      <div className="insight-card">
        <strong>Most Expensive Agent:</strong> {String(report.advanced.most_expensive_agent.agent_id)} — ${(report.advanced.most_expensive_agent.total_cost_usd as number).toFixed(6)}
      </div>
    )}
    {report.advanced.slowest_step && (
      <InsightCard title="Slowest Step" data={report.advanced.slowest_step} />
    )}
    {report.advanced.most_unstable_step && (
      <InsightCard title="Most Unstable Step" data={report.advanced.most_unstable_step} />
    )}
    {report.advanced.slowest_tool && (
      <ToolInsightCard title="Slowest Tool" data={report.advanced.slowest_tool} />
    )}
    {report.advanced.most_used_tool && (
      <ToolInsightCard title="Most Used Tool" data={report.advanced.most_used_tool} />
    )}
    {report.advanced.step_efficiency_ratio !== null && (
      <div className="insight-card">
        <strong>Step Efficiency Ratio:</strong> {(report.advanced.step_efficiency_ratio * 100).toFixed(1)}%
      </div>
    )}
  </div>
);

const BreakdownsTab = ({ report }: { report: AgentKPIReport }) => (
  <div className="kpi-section">
    <h4>Step Breakdown</h4>
    {report.breakdowns.steps.length > 0 ? (
      <table className="kpi-table">
        <thead>
          <tr>
            <th>Step</th><th>Avg (ms)</th><th>P95 (ms)</th><th>Min (ms)</th><th>Max (ms)</th>
            <th>Instability</th><th>Success</th><th>Count</th>
          </tr>
        </thead>
        <tbody>
          {report.breakdowns.steps.map((s) => (
            <tr key={s.step_name}>
              <td>{s.step_name}</td>
              <td>{s.avg_latency_ms.toFixed(0)}</td>
              <td>{s.p95_latency_ms.toFixed(0)}</td>
              <td>{s.min_latency_ms.toFixed(0)}</td>
              <td>{s.max_latency_ms.toFixed(0)}</td>
              <td>{s.instability_ms.toFixed(0)}</td>
              <td>{(s.success_rate * 100).toFixed(0)}%</td>
              <td>{s.occurrence_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    ) : <p className="muted">No step data available.</p>}

    <h4>Tool Breakdown</h4>
    {report.breakdowns.tools.length > 0 ? (
      <table className="kpi-table">
        <thead>
          <tr><th>Tool</th><th>Avg (ms)</th><th>Max (ms)</th><th>Usage</th><th>Failure</th><th>Success</th></tr>
        </thead>
        <tbody>
          {report.breakdowns.tools.map((t) => (
            <tr key={t.tool_name}>
              <td>{t.tool_name}</td>
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
  </div>
);

const JudgmentTab = ({ judgment }: { judgment: AgentEvaluationJudgment }) => {
  const style = JUDGMENT_STYLES[judgment.judgment] || JUDGMENT_STYLES.FAIL;
  return (
    <div className="kpi-section">
      <h4>Scoring & Judgment</h4>
      <div className="judgment-summary" style={{ borderColor: style.color }}>
        <div className="judgment-badge-large" style={{ color: style.color, background: style.bg }}>
          {style.badge}
        </div>
        <div className="global-score">{judgment.global_score.toFixed(1)} <span>/ 100</span></div>
        <div className="confidence">Confidence: {(judgment.confidence * 100).toFixed(1)}%</div>
      </div>

      <h5>Category Scores</h5>
      <table className="kpi-table">
        <thead>
          <tr><th>Category</th><th>Score</th><th>Weight</th><th>Weighted</th><th>Standard</th></tr>
        </thead>
        <tbody>
          {judgment.category_scores.map((cs) => (
            <tr key={cs.category}>
              <td>{cs.category}</td>
              <td>{cs.score.toFixed(1)}</td>
              <td>{(cs.weight * 100).toFixed(0)}%</td>
              <td>{cs.weighted_score.toFixed(1)}</td>
              <td className="muted">{cs.standard_reference}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {judgment.blocking_violations.length > 0 && (
        <>
          <h5>Blocking Violations</h5>
          <ul className="violation-list">
            {judgment.blocking_violations.map((v, i) => (
              <li key={i} className="violation-item">⚠️ {v}</li>
            ))}
          </ul>
        </>
      )}

      <h5>Risk Assessment</h5>
      <p className="risk-text">{judgment.risk_assessment}</p>

      <h5>Standards Compliance</h5>
      <table className="kpi-table">
        <thead><tr><th>Clause</th><th>Compliant</th></tr></thead>
        <tbody>
          {Object.entries(judgment.standards_compliance).map(([clause, compliant]) => (
            <tr key={clause}>
              <td>{clause}</td>
              <td>{compliant ? "✅ Yes" : "❌ No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const ReportTab = ({ markdown }: { markdown: string }) => (
  <div className="kpi-section">
    <h4>Full Markdown Report</h4>
    <div className="markdown-report">
      <pre>{markdown}</pre>
    </div>
  </div>
);

// =============================================================================
// Reusable components
// =============================================================================

const MetricCard = ({
  title,
  value,
  color,
}: {
  title: string;
  value: string | number;
  color?: string;
}) => (
  <div className="metric-card glass-card">
    <div className="metric-title">{title}</div>
    <div className="metric-value" style={color ? { color } : undefined}>
      {value}
    </div>
  </div>
);

const LatencyBarChart = ({ performance }: { performance: AgentKPIReport["performance"] }) => {
  const max = performance.max_latency_ms || 1;
  const bars = [
    { label: "Avg", value: performance.avg_latency_ms },
    { label: "P50", value: performance.p50_latency_ms },
    { label: "P95", value: performance.p95_latency_ms },
    { label: "P99", value: performance.p99_latency_ms },
  ];
  return (
    <div className="latency-bars">
      {bars.map((bar) => (
        <div key={bar.label} className="latency-bar-row">
          <span className="bar-label">{bar.label}</span>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{ width: `${Math.min(100, (bar.value / max) * 100)}%` }}
            />
          </div>
          <span className="bar-value">{bar.value.toFixed(0)} ms</span>
        </div>
      ))}
    </div>
  );
};

const InsightCard = ({ title, data }: { title: string; data: StepAnalytics }) => (
  <div className="insight-card">
    <strong>{title}:</strong> {data.step_name}
    <div className="insight-details">
      Avg: {data.avg_latency_ms.toFixed(0)}ms | Max: {data.max_latency_ms.toFixed(0)}ms | 
      Min: {data.min_latency_ms.toFixed(0)}ms | Instability: {data.instability_ms.toFixed(0)}ms | 
      Success: {(data.success_rate * 100).toFixed(0)}% | Count: {data.occurrence_count}
    </div>
  </div>
);

const ToolInsightCard = ({ title, data }: { title: string; data: ToolAnalytics }) => (
  <div className="insight-card">
    <strong>{title}:</strong> {data.tool_name}
    <div className="insight-details">
      Avg: {data.avg_latency_ms.toFixed(0)}ms | Max: {data.max_latency_ms.toFixed(0)}ms | 
      Usage: {data.usage_count} | Success: {(data.success_rate * 100).toFixed(0)}%
    </div>
  </div>
);
