// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step1UploadPage.tsx
import { FormEvent, useMemo, useState } from "react";
import type { DatasetRead } from "../types";
import { SpinnerPanel } from "../components/SpinnerPanel";

interface Step1UploadPageProps {
  datasets: DatasetRead[];
  selectedDataset: DatasetRead | null;
  loading: boolean;
  error: string | null;
  onUpload: (file: File, name: string, description: string) => Promise<void>;
  onSelectDataset: (dataset: DatasetRead) => void;
  onTaskTypeChange: (task: "classification" | "regression") => void;
  taskType: "classification" | "regression";
}

export const Step1UploadPage = ({
  datasets,
  selectedDataset,
  loading,
  error,
  onUpload,
  onSelectDataset,
  onTaskTypeChange,
  taskType,
}: Step1UploadPageProps) => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const selectedPreview = useMemo(() => {
    if (!selectedDataset) {
      return null;
    }

    return {
      columns: selectedDataset.column_count ?? 0,
      rows: selectedDataset.row_count ?? 0,
      quality: selectedDataset.validation_report?.is_valid ? "Ready" : "Needs attention",
    };
  }, [selectedDataset]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!file || !name.trim()) {
      return;
    }
    await onUpload(file, name.trim(), description.trim());
    setName("");
    setDescription("");
    setFile(null);
  };

  return (
    <section className="step-content">
      <header>
        <p className="eyebrow">Step 1</p>
        <h2>Upload your dataset</h2>
        <p>
          Add a CSV, JSON, Parquet, or Excel file. We will validate quality automatically before moving to modeling.
        </p>
      </header>

      <div className="task-toggle" role="radiogroup" aria-label="Task type">
        <button
          type="button"
          className={`task-toggle__item ${taskType === "classification" ? "is-active" : ""}`}
          onClick={() => onTaskTypeChange("classification")}
        >
          Classification
        </button>
        <button
          type="button"
          className={`task-toggle__item ${taskType === "regression" ? "is-active" : ""}`}
          onClick={() => onTaskTypeChange("regression")}
        >
          Regression
        </button>
      </div>

      <div className="grid-two">
        <form className="glass-card form-card" onSubmit={submit}>
          <h3>New upload</h3>

          <label>
            Dataset name
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Credit Risk - Q2"
              required
            />
          </label>

          <label>
            Description
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Explain what this dataset is used for"
              rows={4}
            />
          </label>

          <label>
            Data file
            <input
              type="file"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              accept=".csv,.json,.jsonl,.parquet,.xlsx,.xls"
              required
            />
          </label>

          <button className="btn btn-primary" disabled={loading || !file || !name.trim()}>
            Upload and Validate
          </button>
        </form>

        <div className="glass-card dataset-card">
          <h3>Available datasets</h3>

          {loading ? <SpinnerPanel text="Loading datasets..." /> : null}

          {!loading && datasets.length === 0 ? <p className="muted">No datasets yet. Upload your first file.</p> : null}

          <div className="dataset-list">
            {datasets.map((dataset) => {
              const active = selectedDataset?.id === dataset.id;
              return (
                <button
                  type="button"
                  key={dataset.id}
                  className={`dataset-list__item ${active ? "is-active" : ""}`}
                  onClick={() => onSelectDataset(dataset)}
                >
                  <span>
                    <strong>{dataset.name}</strong>
                    <small>
                      {dataset.row_count ?? 0} rows · {dataset.column_count ?? 0} columns
                    </small>
                  </span>
                  <em className={`status-tag is-${dataset.status}`}>{dataset.status}</em>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {selectedPreview ? (
        <article className="glass-card preview-card">
          <h3>Selected dataset preview</h3>
          <ul>
            <li>
              <strong>Rows:</strong> {selectedPreview.rows}
            </li>
            <li>
              <strong>Columns:</strong> {selectedPreview.columns}
            </li>
            <li>
              <strong>Quality check:</strong> {selectedPreview.quality}
            </li>
          </ul>
        </article>
      ) : null}

      {error ? <p className="error-banner">{error}</p> : null}
    </section>
  );
};
