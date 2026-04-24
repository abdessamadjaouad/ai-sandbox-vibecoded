// /home/jao/Desktop/sandbox-project-vibecoded/frontend-simple/src/pages/SimpleResultsPage.tsx
import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { simpleApi } from "../api/simpleClient";
import type { SimpleRunResult } from "../types";

interface SimpleResultsPageProps {
  result: SimpleRunResult;
  onNewBenchmark: () => void;
  onBack: () => void;
}

export const SimpleResultsPage = ({ result, onNewBenchmark, onBack }: SimpleResultsPageProps) => {
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [showReport, setShowReport] = useState(false);

  useEffect(() => {
    loadReport();
  }, [result.run_id]);

  const loadReport = async () => {
    try {
      const report = await simpleApi.getReportContent(result.run_id);
      setReportContent(report.content);
    } catch (err) {
      console.error("Failed to load report", err);
    }
  };

  const handleDownloadReport = useCallback(() => {
    const url = simpleApi.getReportDownloadUrl(result.run_id);
    const a = document.createElement("a");
    a.href = url;
    a.download = `benchmark-${result.run_id}.md`;
    a.click();
  }, [result.run_id]);

  const handleDownloadPdf = useCallback(async () => {
    try {
      const { jsPDF } = await import("jspdf");
      const content = reportContent || "";
      const doc = new jsPDF();
      const lines = doc.splitTextToSize(content, 180);
      let y = 10;
      for (const line of lines) {
        if (y > 280) {
          doc.addPage();
          y = 10;
        }
        doc.text(line, 10, y);
        y += 6;
      }
      doc.save(`benchmark-${result.run_id}.pdf`);
    } catch (err) {
      console.error("PDF generation failed", err);
    }
  }, [reportContent, result.run_id]);

  const topModels = result.model_results.slice(0, 3);

  return (
    <main className="wizard-shell">
      <header className="wizard-header">
        <h1>Benchmark Complete</h1>
        <p>Run ID: {result.run_id}</p>
      </header>

      <div className="wizard-content">
        {showReport && reportContent ? (
          <section className="report-section glass-card">
            <div className="report-toolbar">
              <button className="btn btn-ghost" onClick={() => setShowReport(false)}>
                ← Back to Results
              </button>
              <button className="btn btn-ghost" onClick={handleDownloadReport}>
                Download Markdown
              </button>
              <button className="btn btn-ghost" onClick={handleDownloadPdf}>
                Download PDF
              </button>
            </div>
            <div className="report-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {reportContent}
              </ReactMarkdown>
            </div>
          </section>
        ) : (
          <>
            <section className="results-summary glass-card">
              <div className="best-model-card">
                <h2>Best Model</h2>
                <div className="best-model-name">{result.best_model}</div>
                <p className="best-model-task">
                  {result.task_type} · Target: {result.target_column}
                </p>
              </div>

              <div className="results-actions">
                <button className="btn btn-brand" onClick={() => setShowReport(true)}>
                  View Full Report
                </button>
                <button className="btn btn-ghost" onClick={handleDownloadReport}>
                  Download Report
                </button>
              </div>
            </section>

            <section className="rankings-section glass-card">
              <h2>Model Rankings</h2>
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Model</th>
                    <th>Global Score</th>
                    <th>Key Metrics</th>
                    <th>Training Time</th>
                  </tr>
                </thead>
                <tbody>
                  {result.model_results.map((model, idx) => (
                    <tr key={idx} className={idx < 3 ? "top-ranked" : ""}>
                      <td>
                        <span className={`rank rank-${idx + 1}`}>{model.rank ?? idx + 1}</span>
                      </td>
                      <td className="model-name">{model.model_name.replace(/_/g, " ")}</td>
                      <td className="score">
                        {model.global_score?.toFixed(3) ?? "-"}
                      </td>
                      <td className="metrics">
                        {Object.entries(model.metrics)
                          .slice(0, 3)
                          .map(([k, v]) => (
                            <span key={k} className="metric-tag">
                              {k}: {typeof v === "number" ? v.toFixed(3) : v}
                            </span>
                          ))}
                      </td>
                      <td className="time">
                        {(model.training_time_ms / 1000).toFixed(2)}s
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="top-models-section">
              <h2>Top 3 Models</h2>
              <div className="top-models-grid">
                {topModels.map((model, idx) => (
                  <div
                    key={idx}
                    className={`top-model-card glass-card ${idx === 0 ? "gold" : idx === 1 ? "silver" : "bronze"}`}
                  >
                    <div className="top-model-rank">
                      {idx === 0 ? "🥇" : idx === 1 ? "🥈" : "🥉"}
                    </div>
                    <h3>{model.model_name.replace(/_/g, " ")}</h3>
                    <div className="top-model-score">
                      {model.global_score?.toFixed(3) ?? "-"}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </div>

      <footer className="wizard-footer">
        <button className="btn btn-ghost" onClick={onBack}>
          Configure New Run
        </button>
        <button className="btn btn-brand" onClick={onNewBenchmark}>
          Start New Benchmark
        </button>
      </footer>
    </main>
  );
};