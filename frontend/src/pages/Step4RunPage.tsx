// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step4RunPage.tsx
import { FormEvent, useMemo, useState } from "react";
import type { ExperimentRead, ModelCatalogueEntry } from "../types";
import { SpinnerPanel } from "../components/SpinnerPanel";

interface Step4RunPageProps {
  selectedModelCount: number;
  selectedModels: ModelCatalogueEntry[];
  loading: boolean;
  runningState: "idle" | "creating" | "running" | "polling" | "completed" | "failed";
  experiment: ExperimentRead | null;
  error: string | null;
  defaultName: string;
  defaultDescription: string;
  randomSeed: number;
  progressMessage: string;
  onRetry: () => Promise<void>;
  onSubmit: (payload: { name: string; description: string; randomSeed: number }) => Promise<void>;
}

export const Step4RunPage = ({
  selectedModelCount,
  selectedModels,
  loading,
  runningState,
  experiment,
  error,
  defaultName,
  defaultDescription,
  randomSeed,
  progressMessage,
  onRetry,
  onSubmit,
}: Step4RunPageProps) => {
  const [name, setName] = useState(defaultName);
  const [description, setDescription] = useState(defaultDescription);
  const [seed, setSeed] = useState(randomSeed);

  // Allow launching when idle, completed, or failed (to re-run)
  const isProcessing = runningState === "creating" || runningState === "running" || runningState === "polling";
  
  const canLaunch = useMemo(() => {
    return name.trim().length > 0 && selectedModelCount > 0 && !isProcessing;
  }, [name, selectedModelCount, isProcessing]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!canLaunch) {
      return;
    }
    await onSubmit({ name: name.trim(), description: description.trim(), randomSeed: seed });
  };

  const getButtonText = () => {
    if (isProcessing) {
      return "Running...";
    }
    if (runningState === "completed") {
      return "Run Again";
    }
    if (runningState === "failed") {
      return "Retry Run";
    }
    return "Create and Run";
  };

  const getStatusClass = () => {
    switch (runningState) {
      case "completed":
        return "is-completed";
      case "failed":
        return "is-failed";
      case "running":
      case "polling":
        return "is-running";
      default:
        return "is-pending";
    }
  };

  return (
    <section className="step-content">
      <header>
        <p className="eyebrow">Step 4</p>
        <h2>Launch sandbox run</h2>
        <p>Start the experiment. We train each selected model and rank them automatically.</p>
      </header>

      <div className="grid-two">
        <form className="glass-card form-card" onSubmit={submit}>
          <h3>Run setup</h3>

          <label>
            Experiment name
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Credit Risk Benchmark" />
          </label>

          <label>
            Description
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={4}
              placeholder="Compare tabular models on current dataset version"
            />
          </label>

          <label>
            Random seed
            <input type="number" value={seed} min={0} onChange={(event) => setSeed(Number(event.target.value))} />
          </label>

          <button className="btn btn-primary" disabled={!canLaunch || loading}>
            {isProcessing && <span className="btn-spinner" />}
            {getButtonText()}
          </button>

          {runningState === "completed" && (
            <p className="form-hint success">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              Experiment completed successfully. You can run again with different settings.
            </p>
          )}
        </form>

        <article className="glass-card dataset-card">
          <h3>Run monitor</h3>

          {loading ? <SpinnerPanel text={progressMessage || "Preparing run..."} /> : null}

          {!loading && isProcessing ? (
            <SpinnerPanel text={progressMessage || "Experiment is running. Benchmarking models now..."} />
          ) : null}

          {experiment ? (
            <div className="run-details">
              <p>
                <strong>Status:</strong>{" "}
                <span className={`status-tag ${getStatusClass()}`}>{experiment.status}</span>
              </p>
              <p>
                <strong>Experiment ID:</strong>{" "}
                <code className="experiment-id">{experiment.id.slice(0, 8)}...</code>
              </p>
              <p>
                <strong>Selected models:</strong> {selectedModelCount}
              </p>
              {experiment.started_at && (
                <p>
                  <strong>Started:</strong>{" "}
                  {new Date(experiment.started_at).toLocaleString()}
                </p>
              )}
              {experiment.completed_at && (
                <p>
                  <strong>Completed:</strong>{" "}
                  {new Date(experiment.completed_at).toLocaleString()}
                </p>
              )}
            </div>
          ) : (
            !isProcessing && <p className="muted">No run started yet.</p>
          )}

          {runningState === "failed" && (
            <div className="run-error">
              <p className="run-error__message">{error || progressMessage}</p>
              <button type="button" className="btn btn-ghost" onClick={() => void onRetry()}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="23 4 23 10 17 10" />
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                </svg>
                Try again with same setup
              </button>
            </div>
          )}

          <div className="chip-grid">
            {selectedModels.map((model) => (
              <span key={model.name} className="chip is-active">
                {model.name}
              </span>
            ))}
          </div>
        </article>
      </div>

      {error && runningState !== "failed" ? (
        <p className="error-banner">Run failed: {error}. You can fix settings or retry.</p>
      ) : null}
    </section>
  );
};
