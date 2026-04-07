// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step2VersionPage.tsx
import { useMemo } from "react";
import type { DatasetRead, DatasetVersionRead } from "../types";
import { SpinnerPanel } from "../components/SpinnerPanel";

interface Step2VersionPageProps {
  dataset: DatasetRead | null;
  versions: DatasetVersionRead[];
  selectedVersion: DatasetVersionRead | null;
  columns: string[];
  taskType: "classification" | "regression";
  loading: boolean;
  error: string | null;
  trainRatio: number;
  valRatio: number;
  testRatio: number;
  randomSeed: number;
  stratifyColumn: string;
  onAdvancedChange: (patch: {
    trainRatio?: number;
    valRatio?: number;
    testRatio?: number;
    randomSeed?: number;
    stratifyColumn?: string;
  }) => void;
  onCreateVersion: (payload: {
    train_ratio: number;
    val_ratio: number;
    test_ratio: number;
    random_seed: number;
    stratify_column?: string;
  }) => Promise<void>;
  onSelectVersion: (version: DatasetVersionRead) => void;
}

export const Step2VersionPage = ({
  dataset,
  versions,
  selectedVersion,
  columns,
  taskType,
  loading,
  error,
  trainRatio,
  valRatio,
  testRatio,
  randomSeed,
  stratifyColumn,
  onAdvancedChange,
  onCreateVersion,
  onSelectVersion,
}: Step2VersionPageProps) => {
  const total = useMemo(() => Number((trainRatio + valRatio + testRatio).toFixed(2)), [trainRatio, valRatio, testRatio]);

  const create = async () => {
    if (!dataset) {
      return;
    }

    await onCreateVersion({
      train_ratio: trainRatio,
      val_ratio: valRatio,
      test_ratio: testRatio,
      random_seed: randomSeed,
      stratify_column: stratifyColumn || undefined,
    });
  };

  if (!dataset) {
    return (
      <section className="step-content">
        <header>
          <p className="eyebrow">Step 2</p>
          <h2>Create dataset version</h2>
          <p>Pick a dataset first.</p>
        </header>
      </section>
    );
  }

  return (
    <section className="step-content">
      <header>
        <p className="eyebrow">Step 2</p>
        <h2>Create benchmark-ready split</h2>
        <p>
          Use the recommended split to continue fast. Open advanced settings only if you want to tune technical options.
        </p>
      </header>

      <div className="grid-two">
        <article className="glass-card form-card">
          <h3>Recommended configuration</h3>
          <p className="muted">
            Task type: <strong>{taskType}</strong> · Train {Math.round(trainRatio * 100)}% · Validation {Math.round(valRatio * 100)}%
            {", "}
            Test {Math.round(testRatio * 100)}%
          </p>

          <button className="btn btn-primary" disabled={loading || total !== 1} onClick={create}>
            Create Recommended Split
          </button>

          <details className="advanced-panel">
            <summary>Advanced settings</summary>

            <label>
              Train ratio ({Math.round(trainRatio * 100)}%)
              <input
                type="range"
                min={0.5}
                max={0.9}
                step={0.05}
                value={trainRatio}
                onChange={(event) => onAdvancedChange({ trainRatio: Number(event.target.value) })}
              />
            </label>

            <label>
              Validation ratio ({Math.round(valRatio * 100)}%)
              <input
                type="range"
                min={0}
                max={0.4}
                step={0.05}
                value={valRatio}
                onChange={(event) => onAdvancedChange({ valRatio: Number(event.target.value) })}
              />
            </label>

            <label>
              Test ratio ({Math.round(testRatio * 100)}%)
              <input
                type="range"
                min={0}
                max={0.4}
                step={0.05}
                value={testRatio}
                onChange={(event) => onAdvancedChange({ testRatio: Number(event.target.value) })}
              />
            </label>

            <label>
              Random seed
              <input
                type="number"
                value={randomSeed}
                min={0}
                onChange={(event) => onAdvancedChange({ randomSeed: Number(event.target.value) })}
              />
            </label>

            <label>
              Stratify column (optional)
              <select
                value={stratifyColumn}
                onChange={(event) => onAdvancedChange({ stratifyColumn: event.target.value })}
              >
                <option value="">None</option>
                {columns.map((column) => (
                  <option key={column} value={column}>
                    {column}
                  </option>
                ))}
              </select>
            </label>
          </details>

          <p className={total === 1 ? "muted" : "error-banner"}>Total ratio: {total} (must be 1.0)</p>
        </article>

        <article className="glass-card dataset-card">
          <h3>Existing versions</h3>

          {loading ? <SpinnerPanel text="Preparing dataset versions..." /> : null}

          {!loading && versions.length === 0 ? <p className="muted">No versions yet. Create one now.</p> : null}

          <div className="dataset-list">
            {versions.map((version) => {
              const active = selectedVersion?.id === version.id;
              return (
                <button
                  type="button"
                  key={version.id}
                  className={`dataset-list__item ${active ? "is-active" : ""}`}
                  onClick={() => onSelectVersion(version)}
                >
                  <span>
                    <strong>Version {version.version}</strong>
                    <small>
                      train {version.train_rows} · val {version.val_rows ?? 0} · test {version.test_rows ?? 0}
                    </small>
                  </span>
                  <em className="status-tag is-validated">ready</em>
                </button>
              );
            })}
          </div>
        </article>
      </div>

      {error ? <p className="error-banner">{error}</p> : null}
    </section>
  );
};
