// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step5ReportPage.tsx
import type { EvaluationReportResponse, ExperimentResultRead, ExperimentSummary } from "../types";

interface Step5ReportPageProps {
  summary: ExperimentSummary | null;
  report: EvaluationReportResponse | null;
  results: ExperimentResultRead[];
  loading: boolean;
  error: string | null;
}

const formatMetric = (value: number | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return value.toFixed(4);
};

export const Step5ReportPage = ({ summary, report, results, loading, error }: Step5ReportPageProps) => {
  return (
    <section className="step-content">
      <header>
        <p className="eyebrow">Step 5</p>
        <h2>Decision report</h2>
        <p>Understand which model is recommended and why in plain language.</p>
      </header>

      {loading ? (
        <article className="glass-card preview-card">
          <p className="muted">Generating report...</p>
        </article>
      ) : null}

      {summary ? (
        <article className="glass-card report-callout">
          <p className="eyebrow">Recommendation</p>
          <h3>{summary.recommendation ?? "Recommendation not available yet."}</h3>
          <p>
            Best model: <strong>{summary.best_model_name ?? "N/A"}</strong>
            {" · "}
            Score: <strong>{formatMetric(summary.best_model_score)}</strong>
          </p>
        </article>
      ) : (
        !loading && <p className="muted">Run an experiment to see your recommendation.</p>
      )}

      <div className="glass-card table-card">
        <h3>Model ranking</h3>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Model</th>
              <th>Global score</th>
              <th>Latency (ms)</th>
              <th>Training (s)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {results.length === 0 ? (
              <tr>
                <td colSpan={6} className="muted">
                  No results yet.
                </td>
              </tr>
            ) : (
              results.map((result) => (
                <tr key={result.id}>
                  <td>{result.rank ?? "-"}</td>
                  <td>{result.model_name}</td>
                  <td>{formatMetric(result.global_score)}</td>
                  <td>{formatMetric(result.inference_latency_ms)}</td>
                  <td>{formatMetric(result.training_duration_seconds)}</td>
                  <td>
                    <span className={`status-tag ${result.error_message ? "is-failed" : "is-completed"}`}>
                      {result.error_message ? "failed" : "ok"}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {report ? (
        <details className="glass-card markdown-card">
          <summary>Open raw markdown report</summary>
          <pre>{report.markdown_content}</pre>
        </details>
      ) : null}

      {error ? <p className="error-banner">{error}</p> : null}
    </section>
  );
};
