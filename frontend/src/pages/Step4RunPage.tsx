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

  const canLaunch = useMemo(() => {
    return name.trim().length > 0 && selectedModelCount > 0 && runningState !== "running" && runningState !== "polling";
  }, [name, selectedModelCount, runningState]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!canLaunch) {
      return;
    }
    await onSubmit({ name: name.trim(), description: description.trim(), randomSeed: seed });
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
            {runningState === "idle" ? "Create and Run" : "Re-run"}
          </button>
        </form>

        <article className="glass-card dataset-card">
          <h3>Run monitor</h3>

          {loading ? <SpinnerPanel text={progressMessage || "Preparing run..."} /> : null}

          {!loading && (runningState === "running" || runningState === "polling") ? (
            <SpinnerPanel text={progressMessage || "Experiment is running. Benchmarking models now..."} />
          ) : null}

          {experiment ? (
            <div className="run-details">
              <p>
                <strong>Status:</strong> <span className={`status-tag is-${experiment.status}`}>{experiment.status}</span>
              </p>
              <p>
                <strong>Experiment ID:</strong> {experiment.id}
              </p>
              <p>
                <strong>Selected models:</strong> {selectedModelCount}
              </p>
            </div>
          ) : (
            <p className="muted">No run started yet.</p>
          )}

          {runningState === "failed" ? (
            <button type="button" className="btn btn-ghost" onClick={() => void onRetry()}>
              Try again with same setup
            </button>
          ) : null}

          <div className="chip-grid">
            {selectedModels.map((model) => (
              <span key={model.name} className="chip is-active">
                {model.name}
              </span>
            ))}
          </div>
        </article>
      </div>

      {error ? <p className="error-banner">Run failed: {error}. You can fix settings or retry.</p> : null}
    </section>
  );
};
