// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/HistoryPage.tsx
import { useCallback, useEffect, useMemo, useState } from "react";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../context/AuthContext";
import type { ExperimentRead, ExperimentSummary } from "../types";

interface HistoryPageProps {
  onNavigate: (view: "landing" | "wizard" | "login" | "signup" | "about" | "history") => void;
  onViewReport: (experimentId: string) => void;
}

type ExperimentType = "all" | "tabular_ml" | "nlp" | "llm" | "rag" | "agent";
type SortOption = "newest" | "oldest" | "name" | "status";

export const HistoryPage = ({ onNavigate, onViewReport }: HistoryPageProps) => {
  const { getAuthHeaders, isAuthenticated } = useAuth();
  const api = useApi(getAuthHeaders);
  
  const [experiments, setExperiments] = useState<ExperimentRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<ExperimentType>("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");
  
  const [selectedExp, setSelectedExp] = useState<ExperimentRead | null>(null);
  const [expSummary, setExpSummary] = useState<ExperimentSummary | null>(null);
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
      const data = await api.listExperiments(1, 100);
      setExperiments(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load experiments");
    } finally {
      setLoading(false);
    }
  };

  const filteredExperiments = useMemo(() => {
    let filtered = [...experiments];
    
    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(exp => 
        exp.name.toLowerCase().includes(query) ||
        exp.description?.toLowerCase().includes(query)
      );
    }
    
    // Filter by type
    if (typeFilter !== "all") {
      filtered = filtered.filter(exp => exp.experiment_type === typeFilter);
    }
    
    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "newest":
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case "oldest":
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case "name":
          return a.name.localeCompare(b.name);
        case "status":
          return a.status.localeCompare(b.status);
        default:
          return 0;
      }
    });
    
    return filtered;
  }, [experiments, searchQuery, typeFilter, sortBy]);

  const loadExperimentDetails = async (exp: ExperimentRead) => {
    try {
      setDetailsLoading(true);
      setSelectedExp(exp);
      const summary = await api.getExperimentSummary(exp.id);
      setExpSummary(summary);
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

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "tabular_ml": return "Tabular ML";
      case "nlp": return "NLP";
      case "llm": return "LLM";
      case "rag": return "RAG";
      case "agent": return "Agent";
      default: return type;
    }
  };

  if (loading) {
    return (
      <main className="history-shell">
        <div className="history-loading">
          <div className="spinner-large"></div>
          <p>Loading your experiments...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="history-shell">
      <header className="history-header glass-card">
        <div className="history-header__content">
          <div className="history-header__title">
            <h1>My Experiments</h1>
            <p>Manage your benchmark runs</p>
          </div>
          <div className="history-header__stats">
            <div className="stat-item">
              <span className="stat-value">{experiments.length}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{experiments.filter(e => e.status === "completed").length}</span>
              <span className="stat-label">Completed</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{experiments.filter(e => e.status === "failed").length}</span>
              <span className="stat-label">Failed</span>
            </div>
          </div>
        </div>
      </header>

      {error && (
        <div className="history-error glass-card">
          <p>{error}</p>
          <button onClick={loadExperiments}>Retry</button>
        </div>
      )}

      <div className="history-toolbar glass-card">
        <div className="search-box">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search experiments..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="filter-group">
          <select 
            value={typeFilter} 
            onChange={(e) => setTypeFilter(e.target.value as ExperimentType)}
            className="filter-select"
          >
            <option value="all">All Types</option>
            <option value="tabular_ml">Tabular ML</option>
            <option value="nlp">NLP</option>
            <option value="llm">LLM</option>
            <option value="rag">RAG</option>
            <option value="agent">Agent</option>
          </select>
          
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="filter-select"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="name">Name (A-Z)</option>
            <option value="status">Status</option>
          </select>
        </div>
      </div>

      <div className="history-content">
        <section className="experiments-list">
          {filteredExperiments.length === 0 ? (
            <div className="empty-state glass-card">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
              <h3>No experiments found</h3>
              <p>
                {searchQuery || typeFilter !== "all" 
                  ? "Try adjusting your search or filters" 
                  : "Start your first benchmark from the wizard"}
              </p>
              {(searchQuery || typeFilter !== "all") && (
                <button 
                  className="btn btn-ghost"
                  onClick={() => { setSearchQuery(""); setTypeFilter("all"); }}
                >
                  Clear Filters
                </button>
              )}
            </div>
          ) : (
            <div className="experiments-grid">
              {filteredExperiments.map((exp) => (
                <article 
                  key={exp.id} 
                  className={`experiment-card glass-card ${selectedExp?.id === exp.id ? "selected" : ""}`}
                  onClick={() => loadExperimentDetails(exp)}
                >
                  <div className="experiment-card__header">
                    <span className="experiment-card__type">{getTypeLabel(exp.experiment_type)}</span>
                    <span className="experiment-card__status" style={{ color: getStatusColor(exp.status) }}>
                      {exp.status}
                    </span>
                  </div>
                  <h3 className="experiment-card__title">{exp.name}</h3>
                  <p className="experiment-card__date">{formatDate(exp.created_at)}</p>
                  {exp.task_type && (
                    <span className="experiment-card__task">{exp.task_type}</span>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="experiment-details glass-card">
          {detailsLoading ? (
            <div className="details-loading">
              <div className="spinner"></div>
              <p>Loading details...</p>
            </div>
          ) : selectedExp ? (
            <div className="details-content">
              <div className="details-header">
                <span className="details-type">{getTypeLabel(selectedExp.experiment_type)}</span>
                <h2>{selectedExp.name}</h2>
                {selectedExp.description && <p>{selectedExp.description}</p>}
                <p className="details-date">Created: {formatDate(selectedExp.created_at)}</p>
              </div>

              {expSummary && (
                <div className="details-stats">
                  <div className="stat-card">
                    <span className="stat-label">Status</span>
                    <span className="stat-value" style={{ color: getStatusColor(expSummary.status) }}>
                      {expSummary.status}
                    </span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">Models</span>
                    <span className="stat-value">{expSummary.total_models}</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">Success</span>
                    <span className="stat-value stat-success">{expSummary.successful_models}</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">Failed</span>
                    <span className="stat-value stat-error">{expSummary.failed_models}</span>
                  </div>
                  {expSummary.best_model_name && (
                    <div className="stat-card stat-highlight">
                      <span className="stat-label">Best Model</span>
                      <span className="stat-value">{expSummary.best_model_name}</span>
                      <span className="stat-score">{expSummary.best_model_score?.toFixed(3)}</span>
                    </div>
                  )}
                </div>
              )}

              {expSummary?.recommendation && (
                <div className="recommendation-box">
                  <h4>Recommendation</h4>
                  <p>{expSummary.recommendation}</p>
                </div>
              )}

              <div className="details-actions">
                <button className="btn btn-brand" onClick={() => handleViewReport(selectedExp)}>
                  View Full Report
                </button>
              </div>
            </div>
          ) : (
            <div className="details-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <p>Select an experiment to view details</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
};