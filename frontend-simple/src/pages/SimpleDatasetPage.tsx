// /home/jao/Desktop/sandbox-project-vibecoded/frontend-simple/src/pages/SimpleDatasetPage.tsx
import { useCallback, useEffect, useState } from "react";
import { simpleApi } from "../api/simpleClient";
import type { SimpleDatasetInfo, WizardStep } from "../types";

interface SimpleDatasetPageProps {
  onNext: (datasetId: string, step: WizardStep) => void;
  onBack: () => void;
}

export const SimpleDatasetPage = ({ onNext, onBack }: SimpleDatasetPageProps) => {
  const [datasets, setDatasets] = useState<SimpleDatasetInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const data = await simpleApi.listDatasets();
      setDatasets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load datasets");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = useCallback(async (file: File) => {
    try {
      setUploading(true);
      setError(null);
      const dataset = await simpleApi.uploadDataset(file);
      setDatasets((prev) => [dataset, ...prev]);
      setSelectedDataset(dataset.dataset_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        const validTypes = [".csv", ".xlsx", ".xls"];
        const ext = file.name.toLowerCase().slice(file.name.lastIndexOf("."));
        if (!validTypes.includes(ext)) {
          setError("Please upload a CSV or Excel file");
          return;
        }
        handleUpload(file);
      }
    },
    [handleUpload]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files?.[0];
      if (file) {
        handleUpload(file);
      }
    },
    [handleUpload]
  );

  const formatFileSize = (kb: number) => {
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  };

  const handleContinue = () => {
    if (selectedDataset) {
      onNext(selectedDataset, "config");
    }
  };

  return (
    <main className="wizard-shell">
      <header className="wizard-header">
        <h1>Select Dataset</h1>
        <p>Upload a new dataset or select from existing ones</p>
      </header>

      <div className="wizard-content">
        <section className="upload-section glass-card">
          <h2>Upload New Dataset</h2>
          <div
            className={`upload-zone ${uploading ? "uploading" : ""}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileChange}
              id="file-upload"
              disabled={uploading}
            />
            <label htmlFor="file-upload" className="upload-label">
              {uploading ? (
                <>
                  <div className="spinner"></div>
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  <span>Drop CSV or Excel file here</span>
                  <span className="upload-hint">or click to browse</span>
                </>
              )}
            </label>
          </div>
        </section>

        <section className="datasets-section glass-card">
          <h2>Existing Datasets</h2>
          
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading datasets...</p>
            </div>
          ) : error && datasets.length === 0 ? (
            <div className="error-state">
              <p>{error}</p>
              <button className="btn btn-ghost" onClick={loadDatasets}>
                Retry
              </button>
            </div>
          ) : datasets.length === 0 ? (
            <div className="empty-state">
              <p>No datasets yet. Upload one to get started.</p>
            </div>
          ) : (
            <ul className="dataset-list">
              {datasets.map((ds) => (
                <li
                  key={ds.dataset_id}
                  className={`dataset-item ${selectedDataset === ds.dataset_id ? "selected" : ""}`}
                  onClick={() => setSelectedDataset(ds.dataset_id)}
                >
                  <div className="dataset-info">
                    <span className="dataset-name">{ds.filename}</span>
                    <span className="dataset-meta">
                      {ds.rows} rows · {ds.columns} columns · {formatFileSize(ds.file_size_kb)}
                    </span>
                  </div>
                  <div className="dataset-check">
                    {selectedDataset === ds.dataset_id && (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {error && datasets.length > 0 && (
          <div className="error-banner">
            <p>{error}</p>
          </div>
        )}
      </div>

      <footer className="wizard-footer">
        <button className="btn btn-ghost" onClick={onBack}>
          Back
        </button>
        <button
          className="btn btn-brand"
          onClick={handleContinue}
          disabled={!selectedDataset}
        >
          Continue
        </button>
      </footer>
    </main>
  );
};