// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step5ReportPage.tsx
import jsPDF from "jspdf";
import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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

const getNumericMetric = (result: ExperimentResultRead, keys: string[]): number | null => {
  for (const key of keys) {
    const value = result.metrics[key];
    if (typeof value === "number" && Number.isFinite(value)) {
      return value;
    }
  }
  return null;
};

export const Step5ReportPage = ({ summary, report, results, loading, error }: Step5ReportPageProps) => {
  const rankedResults = useMemo(
    () => [...results].sort((a, b) => (a.rank ?? Number.POSITIVE_INFINITY) - (b.rank ?? Number.POSITIVE_INFINITY)),
    [results]
  );

  const maxScore = useMemo(() => {
    const scores = rankedResults
      .map((entry) => entry.global_score)
      .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
    if (scores.length === 0) {
      return 1;
    }
    return Math.max(...scores, 1);
  }, [rankedResults]);

  const downloadMarkdown = () => {
    if (!report) {
      return;
    }
    const blob = new Blob([report.markdown_content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${report.experiment_name.replace(/\s+/g, "-").toLowerCase()}-report.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const downloadPdf = () => {
    if (!report) {
      return;
    }
    const pdf = new jsPDF({ unit: "pt", format: "a4" });
    pdf.setFont("helvetica", "bold");
    pdf.setFontSize(16);
    pdf.text(`AI Sandbox Report - ${report.experiment_name}`, 40, 50);
    pdf.setFont("helvetica", "normal");
    pdf.setFontSize(10);

    const lines = pdf.splitTextToSize(report.markdown_content, 510);
    let y = 80;
    for (const line of lines) {
      if (y > 790) {
        pdf.addPage();
        y = 40;
      }
      pdf.text(line, 40, y);
      y += 14;
    }

    pdf.save(`${report.experiment_name.replace(/\s+/g, "-").toLowerCase()}-report.pdf`);
  };

  return (
    <section className="step-content">
      <header>
        <p className="eyebrow">Step 5</p>
        <h2>Benchmark dashboard and report</h2>
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

      <div className="glass-card chart-card">
        <h3>Global score comparison</h3>
        {rankedResults.length === 0 ? (
          <p className="muted">No model score available yet.</p>
        ) : (
          <div className="score-bars" role="list" aria-label="Model scores">
            {rankedResults.map((result) => {
              const score = result.global_score ?? 0;
              const width = Math.max(4, (score / maxScore) * 100);
              return (
                <div key={result.id} className="score-bar-row" role="listitem">
                  <div className="score-bar-meta">
                    <strong>{result.model_name}</strong>
                    <span>{formatMetric(result.global_score)}</span>
                  </div>
                  <div className="score-bar-track">
                    <div className="score-bar-fill" style={{ width: `${width}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="glass-card table-card">
        <h3>Model ranking</h3>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Model</th>
              <th>Global score</th>
              <th>Accuracy</th>
              <th>Latency (ms)</th>
              <th>Training (s)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {results.length === 0 ? (
              <tr>
                <td colSpan={7} className="muted">
                  No results yet.
                </td>
              </tr>
            ) : (
              rankedResults.map((result) => (
                <tr key={result.id}>
                  <td>{result.rank ?? "-"}</td>
                  <td>{result.model_name}</td>
                  <td>{formatMetric(result.global_score)}</td>
                  <td>{formatMetric(getNumericMetric(result, ["accuracy", "balanced_accuracy", "f1"]))}</td>
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
        <article className="glass-card markdown-card">
          <div className="report-tools">
            <h3>Rendered report</h3>
            <div className="report-tools__actions">
              <button type="button" className="btn btn-ghost" onClick={downloadMarkdown}>
                Download Markdown
              </button>
              <button type="button" className="btn btn-primary" onClick={downloadPdf}>
                Download PDF
              </button>
            </div>
          </div>
          <div className="markdown-render">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.markdown_content}</ReactMarkdown>
          </div>
        </article>
      ) : null}

      {error ? <p className="error-banner">{error}</p> : null}
    </section>
  );
};
