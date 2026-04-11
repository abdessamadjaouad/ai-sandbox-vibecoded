// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step5ReportPage.tsx
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import { useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { EvaluationReportResponse, ExperimentResultRead, ExperimentSummary } from "../types";

interface Step5ReportPageProps {
  summary: ExperimentSummary | null;
  report: EvaluationReportResponse | null;
  results: ExperimentResultRead[];
  loading: boolean;
  error: string | null;
  taskType?: "classification" | "regression";
}

// Classification metrics to look for
const CLASSIFICATION_METRICS = [
  { key: "accuracy", label: "Accuracy" },
  { key: "balanced_accuracy", label: "Balanced Acc" },
  { key: "precision", label: "Precision" },
  { key: "recall", label: "Recall" },
  { key: "f1", label: "F1 Score" },
  { key: "f1_score", label: "F1 Score" },
  { key: "roc_auc", label: "AUC-ROC" },
  { key: "auc", label: "AUC" },
];

// Regression metrics to look for
const REGRESSION_METRICS = [
  { key: "mae", label: "MAE" },
  { key: "mean_absolute_error", label: "MAE" },
  { key: "mse", label: "MSE" },
  { key: "mean_squared_error", label: "MSE" },
  { key: "rmse", label: "RMSE" },
  { key: "root_mean_squared_error", label: "RMSE" },
  { key: "r2", label: "R²" },
  { key: "r2_score", label: "R²" },
  { key: "mape", label: "MAPE" },
];

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

// Detect which metrics are available across results
const detectAvailableMetrics = (
  results: ExperimentResultRead[],
  taskType: "classification" | "regression"
): { key: string; label: string }[] => {
  const metricsList = taskType === "classification" ? CLASSIFICATION_METRICS : REGRESSION_METRICS;
  const available: { key: string; label: string }[] = [];
  const seenLabels = new Set<string>();

  for (const metric of metricsList) {
    for (const result of results) {
      const value = result.metrics[metric.key];
      if (typeof value === "number" && Number.isFinite(value) && !seenLabels.has(metric.label)) {
        available.push(metric);
        seenLabels.add(metric.label);
        break;
      }
    }
  }

  return available;
};

export const Step5ReportPage = ({
  summary,
  report,
  results,
  loading,
  error,
  taskType = "classification",
}: Step5ReportPageProps) => {
  const [reportExpanded, setReportExpanded] = useState(true);
  const [visibleMetrics, setVisibleMetrics] = useState<Set<string>>(new Set(["accuracy", "f1", "precision", "recall", "mae", "rmse", "r2"]));
  const [pdfGenerating, setPdfGenerating] = useState(false);
  const markdownRef = useRef<HTMLDivElement>(null);

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

  const availableMetrics = useMemo(
    () => detectAvailableMetrics(results, taskType),
    [results, taskType]
  );

  const toggleMetric = (key: string) => {
    setVisibleMetrics((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

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

  const downloadPdf = async () => {
    if (!report || !markdownRef.current) {
      return;
    }

    setPdfGenerating(true);

    try {
      const element = markdownRef.current;
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: "#ffffff",
      });

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
      });

      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 10;
      const contentWidth = pageWidth - margin * 2;
      
      const imgWidth = contentWidth;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      let heightLeft = imgHeight;
      let position = margin;
      let page = 1;

      // Add title
      pdf.setFontSize(16);
      pdf.setFont("helvetica", "bold");
      pdf.text(`AI Sandbox Report - ${report.experiment_name}`, margin, margin + 5);
      position = margin + 15;

      // Add image with pagination
      while (heightLeft > 0) {
        if (page > 1) {
          pdf.addPage();
          position = margin;
        }

        const availableHeight = pageHeight - position - margin;
        // currentHeight could be used for partial image rendering in future
        void Math.min(heightLeft, availableHeight);
        
        pdf.addImage(
          imgData,
          "PNG",
          margin,
          position,
          imgWidth,
          imgHeight,
          undefined,
          "FAST",
          0
        );

        heightLeft -= availableHeight;
        page++;
      }

      pdf.save(`${report.experiment_name.replace(/\s+/g, "-").toLowerCase()}-report.pdf`);
    } catch (err) {
      console.error("PDF generation failed:", err);
      // Fallback to text-based PDF
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
    } finally {
      setPdfGenerating(false);
    }
  };

  return (
    <section className="step-content step-content--report">
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
        <article className="glass-card report-callout report-callout--branded">
          <p className="eyebrow">Recommendation</p>
          <h3>{summary.recommendation ?? "Recommendation not available yet."}</h3>
          <p className="report-callout__details">
            Best model: <strong className="text-brand">{summary.best_model_name ?? "N/A"}</strong>
            {" · "}
            Score: <strong className="text-brand">{formatMetric(summary.best_model_score)}</strong>
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
            {rankedResults.map((result, index) => {
              const score = result.global_score ?? 0;
              const width = Math.max(4, (score / maxScore) * 100);
              const isBest = index === 0;
              return (
                <div key={result.id} className={`score-bar-row ${isBest ? "is-best" : ""}`} role="listitem">
                  <div className="score-bar-meta">
                    <strong className={isBest ? "text-brand" : ""}>{result.model_name}</strong>
                    <span className={isBest ? "text-brand" : ""}>{formatMetric(result.global_score)}</span>
                  </div>
                  <div className="score-bar-track">
                    <div className={`score-bar-fill ${isBest ? "is-best" : ""}`} style={{ width: `${width}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="glass-card table-card">
        <div className="table-card__header">
          <h3>Model ranking</h3>
          {availableMetrics.length > 0 && (
            <div className="metric-toggles">
              <span className="metric-toggles__label">Show metrics:</span>
              {availableMetrics.map((metric) => (
                <button
                  key={metric.key}
                  type="button"
                  className={`chip ${visibleMetrics.has(metric.key) ? "is-active" : ""}`}
                  onClick={() => toggleMetric(metric.key)}
                >
                  {metric.label}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Model</th>
                <th>Global Score</th>
                {availableMetrics
                  .filter((m) => visibleMetrics.has(m.key))
                  .map((metric) => (
                    <th key={metric.key}>{metric.label}</th>
                  ))}
                <th>Latency (ms)</th>
                <th>Training (s)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr>
                  <td colSpan={7 + availableMetrics.filter((m) => visibleMetrics.has(m.key)).length} className="muted">
                    No results yet.
                  </td>
                </tr>
              ) : (
                rankedResults.map((result, index) => {
                  const isBest = index === 0;
                  return (
                    <tr key={result.id} className={isBest ? "is-best" : ""}>
                      <td>
                        {isBest ? (
                          <span className="rank-badge is-best">1</span>
                        ) : (
                          <span className="rank-badge">{result.rank ?? "-"}</span>
                        )}
                      </td>
                      <td className={isBest ? "text-brand font-semibold" : ""}>{result.model_name}</td>
                      <td className={isBest ? "text-brand font-semibold" : ""}>{formatMetric(result.global_score)}</td>
                      {availableMetrics
                        .filter((m) => visibleMetrics.has(m.key))
                        .map((metric) => (
                          <td key={metric.key}>{formatMetric(getNumericMetric(result, [metric.key]))}</td>
                        ))}
                      <td>{formatMetric(result.inference_latency_ms)}</td>
                      <td>{formatMetric(result.training_duration_seconds)}</td>
                      <td>
                        <span className={`status-tag ${result.error_message ? "is-failed" : "is-completed"}`}>
                          {result.error_message ? "failed" : "ok"}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {report ? (
        <article className="glass-card markdown-card markdown-card--full">
          <div className="report-tools">
            <button
              type="button"
              className="report-toggle"
              onClick={() => setReportExpanded(!reportExpanded)}
              aria-expanded={reportExpanded}
            >
              <svg
                className={`report-toggle__icon ${reportExpanded ? "is-expanded" : ""}`}
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
              <h3>Detailed Report</h3>
            </button>
            <div className="report-tools__actions">
              <button type="button" className="btn btn-ghost" onClick={downloadMarkdown}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Markdown
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => void downloadPdf()}
                disabled={pdfGenerating}
              >
                {pdfGenerating ? (
                  <>
                    <span className="btn-spinner" />
                    Generating...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                      <polyline points="10 9 9 9 8 9" />
                    </svg>
                    PDF
                  </>
                )}
              </button>
            </div>
          </div>
          <div
            className={`markdown-render-wrapper ${reportExpanded ? "is-expanded" : "is-collapsed"}`}
          >
            <div ref={markdownRef} className="markdown-render">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.markdown_content}</ReactMarkdown>
            </div>
          </div>
        </article>
      ) : null}

      {error ? <p className="error-banner">{error}</p> : null}
    </section>
  );
};
