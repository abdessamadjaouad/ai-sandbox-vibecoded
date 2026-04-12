// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/HistoryPage.tsx
import { useCallback, useEffect, useState } from "react";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../context/AuthContext";
import type { ExperimentRead, ExperimentSummary, ExperimentResultRead } from "../types";

interface HistoryPageProps {
  onNavigate: (view: "landing" | "wizard" | "login" | "signup" | "about" | "history") => void;
  onViewReport: (experimentId: string) => void;
}

export const HistoryPage = ({ onNavigate, onViewReport }: HistoryPageProps) => {
  const { getAuthHeaders, isAuthenticated } = useAuth();
  const api = useApi(getAuthHeaders);
  const [experiments, setExperiments] = useState<ExperimentRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedExp, setSelectedExp] = useState<ExperimentRead | null>(null);
  const [expSummary, setExpSummary] = useState<ExperimentSummary | null>(null);
  const [expResults, setExpResults] = useState<ExperimentResultRead[]>([]);
  const [detailsLoading, setDetailsLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      onNavigate("login");
      return;
    }
    loadExperiments();
  }, [isAuthenticated, onNavigate]);

  const loadExperiments = async () => {
    try {
      setLoading(true);
      const data = await api.listExperiments(1, 50);
      setExperiments(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load experiments");
    } finally {
      setLoading(false);
    }
  };

  const loadExperimentDetails = async (exp: ExperimentRead) => {
    try {
      setDetailsLoading(true);
      setSelectedExp(exp);
      const [summary, results] = await Promise.all([
        api.getExperimentSummary(exp.id),
        api.getExperimentResults(exp.id),
      ]);
      setExpSummary(summary);
      setExpResults(results);
    } catch (err) {
      console.error("Failed to load experiment details", err);
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleViewReport = useCallback((exp: ExperimentRead) => {
    onViewReport(exp.id);
  }, [onViewReport]);

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "var(--color-success)";
      case "failed":
        return "var(--color-error)";
      case "running":
      case "pending":
        return "var(--color-warning)";
      default:
        return "var(--color-text-secondary)";
    }
  };

  if (loading) {
    return (
      <main className="history-shell">
        <div className="glass-card" style={{ textAlign: "center", padding: "3rem" }}>
          <p>Loading your experiments...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="history-shell">
      <header className="history-header">
        <h1>Your Experiment History</h1>
        <p>View and manage your past benchmark runs</p>
      </header>

      {error && (
        <div className="glass-card" style={{ padding: "1rem", marginBottom: "1rem", borderLeft: "3px solid var(--color-error)" }}>
          <p style={{ color: "var(--color-error)" }}>{error}</p>
        </div>
      )}

      <div className="history-content">
        <section className="experiments-list glass-card">
          <h2>Experiments</h2>
          {experiments.length === 0 ? (
            <p className="empty-state">No experiments yet. Start a new benchmark to see it here.</p>
          ) : (
            <ul className="experiment-items">
              {experiments.map((exp) => (
                <li key={exp.id} className={`experiment-item ${selectedExp?.id === exp.id ? "selected" : ""}`}>
                  <button type="button" className="experiment-item__button" onClick={() => loadExperimentDetails(exp)}>
                    <div className="experiment-item__info">
                      <strong>{exp.name}</strong>
                      <span className="experiment-item__meta">
                        {formatDate(exp.created_at)} · {exp.experiment_type.replace("_", " ")}
                      </span>
                    </div>
                    <span className="experiment-item__status" style={{ color: getStatusColor(exp.status) }}>
                      {exp.status}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="experiment-details glass-card">
          {detailsLoading ? (
            <div style={{ textAlign: "center", padding: "2rem" }}>
              <p>Loading details...</p>
            </div>
          ) : selectedExp ? (
            <>
              <div className="details-header">
                <h2>{selectedExp.name}</h2>
                {selectedExp.description && <p className="description">{selectedExp.description}</p>}
              </div>

              {expSummary && (
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="label">Status</span>
                    <span className="value" style={{ color: getStatusColor(expSummary.status) }}>{expSummary.status}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Total Models</span>
                    <span className="value">{expSummary.total_models}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Successful</span>
                    <span className="value">{expSummary.successful_models}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Failed</span>
                    <span className="value">{expSummary.failed_models}</span>
                  </div>
                  {expSummary.best_model_name && (
                    <div className="summary-item">
                      <span className="label">Best Model</span>
                      <span className="value">{expSummary.best_model_name}</span>
                    </div>
                  )}
                  {expSummary.best_model_score && (
                    <div className="summary-item">
                      <span className="label">Best Score</span>
                      <span className="value">{expSummary.best_model_score.toFixed(3)}</span>
                    </div>
                  )}
                  {expSummary.duration_seconds && (
                    <div className="summary-item">
                      <span className="label">Duration</span>
                      <span className="value">{Math.round(expSummary.duration_seconds)}s</span>
                    </div>
                  )}
                </div>
              )}

              {expResults.length > 0 && (
                <div className="results-table-container">
                  <h3>Model Results</h3>
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Model</th>
                        <th>Global Score</th>
                        <th>Training Time</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {expResults.map((result) => (
                        <tr key={result.id}>
                          <td>{result.rank ?? "-"}</td>
                          <td>{result.model_name}</td>
                          <td>{result.global_score?.toFixed(3) ?? "-"}</td>
                          <td>{result.training_duration_seconds ? `${result.training_duration_seconds.toFixed(1)}s` : "-"}</td>
                          <td style={{ color: result.error_message ? "var(--color-error)" : "var(--color-success)" }}>
                            {result.error_message ? "Failed" : "Success"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {expSummary?.recommendation && (
                <div className="recommendation-box">
                  <h3>Recommendation</h3>
                  <p>{expSummary.recommendation}</p>
                </div>
              )}

              <div className="details-actions">
                <button type="button" className="btn btn-brand" onClick={() => handleViewReport(selectedExp)}>
                  View Full Report
                </button>
              </div>
            </>
          ) : (
            <p className="empty-state">Select an experiment to view details</p>
          )}
        </section>
      </div>
    </main>
  );
};