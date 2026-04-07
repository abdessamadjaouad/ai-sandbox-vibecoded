// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step2VersionPage.tsx
import { useMemo, useState } from "react";
import type { DatasetRead, DatasetVersionRead } from "../types";
import { SpinnerPanel } from "../components/SpinnerPanel";

interface Step2VersionPageProps {
  dataset: DatasetRead | null;
  versions: DatasetVersionRead[];
  selectedVersion: DatasetVersionRead | null;
  columns: string[];
  loading: boolean;
  error: string | null;
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
  loading,
  error,
  onCreateVersion,
  onSelectVersion,
}: Step2VersionPageProps) => {
  const [train, setTrain] = useState(0.7);
  const [val, setVal] = useState(0.15);
  const [test, setTest] = useState(0.15);
  const [seed, setSeed] = useState(42);
  const [stratify, setStratify] = useState("");

  const total = useMemo(() => Number((train + val + test).toFixed(2)), [train, val, test]);

  const create = async () => {
    if (!dataset) {
      return;
    }

    await onCreateVersion({
      train_ratio: train,
      val_ratio: val,
      test_ratio: test,
      random_seed: seed,
      stratify_column: stratify || undefined,
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
        <h2>Prepare training split</h2>
        <p>Define train/validation/test ratios once. Every model will be compared on the same split.</p>
      </header>

      <div className="grid-two">
        <article className="glass-card form-card">
          <h3>Split configuration</h3>

          <label>
            Train ratio ({Math.round(train * 100)}%)
            <input
              type="range"
              min={0.5}
              max={0.9}
              step={0.05}
              value={train}
              onChange={(event) => setTrain(Number(event.target.value))}
            />
          </label>

          <label>
            Validation ratio ({Math.round(val * 100)}%)
            <input
              type="range"
              min={0}
              max={0.4}
              step={0.05}
              value={val}
              onChange={(event) => setVal(Number(event.target.value))}
            />
          </label>

          <label>
            Test ratio ({Math.round(test * 100)}%)
            <input
              type="range"
              min={0}
              max={0.4}
              step={0.05}
              value={test}
              onChange={(event) => setTest(Number(event.target.value))}
            />
          </label>

          <label>
            Random seed
            <input type="number" value={seed} min={0} onChange={(event) => setSeed(Number(event.target.value))} />
          </label>

          <label>
            Stratify column (optional)
            <select value={stratify} onChange={(event) => setStratify(event.target.value)}>
              <option value="">None</option>
              {columns.map((column) => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </label>

          <p className={total === 1 ? "muted" : "error-banner"}>Total ratio: {total} (must be 1.0)</p>

          <button className="btn btn-primary" disabled={loading || total !== 1} onClick={create}>
            Create Version
          </button>
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
