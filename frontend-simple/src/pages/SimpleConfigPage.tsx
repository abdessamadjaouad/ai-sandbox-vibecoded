// /home/jao/Desktop/sandbox-project-vibecoded/frontend-simple/src/pages/SimpleConfigPage.tsx
import { useCallback, useEffect, useState } from "react";
import { simpleApi } from "../api/simpleClient";
import type { SimpleDatasetInfo, SimpleRunConfig, TaskType } from "../types";

interface SimpleConfigPageProps {
  datasetId: string;
  onNext: (config: SimpleRunConfig) => void;
  onBack: () => void;
}

export const SimpleConfigPage = ({ datasetId, onNext, onBack }: SimpleConfigPageProps) => {
  const [dataset, setDataset] = useState<SimpleDatasetInfo | null>(null);
  const [loading, setLoading] = useState(true);
  
  const [targetColumn, setTargetColumn] = useState("");
  const [taskType, setTaskType] = useState<TaskType>("regression");
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [testSize, setTestSize] = useState(0.2);
  const [randomState, setRandomState] = useState(42);
  const [latencyThreshold, setLatencyThreshold] = useState<number | "">("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Weights
  const [weightPerf, setWeightPerf] = useState(0.4);
  const [weightRobust, setWeightRobust] = useState(0.2);
  const [weightLat, setWeightLat] = useState(0.2);
  const [weightSize, setWeightSize] = useState(0.2);

  useEffect(() => {
    loadDataset();
  }, [datasetId]);

  const loadDataset = async () => {
    try {
      setLoading(true);
      const datasets = await simpleApi.listDatasets();
      const ds = datasets.find((d) => d.dataset_id === datasetId);
      if (!ds) {
        setError("Dataset not found");
        return;
      }
      setDataset(ds);

      // Get suggestion
      try {
        const sugg = await simpleApi.suggestConfig(datasetId);
        setTargetColumn(sugg.target_column);
        setTaskType(sugg.task_type as TaskType);
      } catch {
        // Use defaults if suggestion fails
        if (ds.column_names.length > 0) {
          setTargetColumn(ds.column_names[ds.column_names.length - 1]);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dataset");
    } finally {
      setLoading(false);
    }
  };

  // Update available models when task type changes
  useEffect(() => {
    const models = taskType === "classification"
      ? ["logistic_regression", "random_forest", "xgboost", "lightgbm", "extra_trees", "knn"]
      : ["linear_regression", "random_forest", "xgboost", "lightgbm", "extra_trees"];
    setSelectedModels(models);
  }, [taskType]);

  const toggleModel = (model: string) => {
    setSelectedModels((prev) =>
      prev.includes(model) ? prev.filter((m) => m !== model) : [...prev, model]
    );
  };

  const selectAllModels = () => {
    const models = taskType === "classification"
      ? ["logistic_regression", "random_forest", "xgboost", "lightgbm", "extra_trees", "knn"]
      : ["linear_regression", "random_forest", "xgboost", "lightgbm", "extra_trees"];
    setSelectedModels(models);
  };

  const deselectAllModels = () => {
    setSelectedModels([]);
  };

  const handleSubmit = useCallback(() => {
    if (!targetColumn) {
      setError("Please select a target column");
      return;
    }
    if (selectedModels.length === 0) {
      setError("Please select at least one model");
      return;
    }
    if (Math.abs((weightPerf + weightRobust + weightLat + weightSize) - 1) > 0.01) {
      setError("Weights must sum to 1.0");
      return;
    }

    const config: SimpleRunConfig = {
      task_type: taskType,
      target_column: targetColumn,
      dataset_id: datasetId,
      description: description || undefined,
      models: selectedModels,
      test_size: testSize,
      random_state: randomState,
      weight_performance: weightPerf,
      weight_robustness: weightRobust,
      weight_latency: weightLat,
      weight_size: weightSize,
      latency_threshold_s: latencyThreshold === "" ? null : latencyThreshold,
    };

    onNext(config);
  }, [targetColumn, taskType, datasetId, description, selectedModels, testSize, randomState, weightPerf, weightRobust, weightLat, weightSize, latencyThreshold, onNext]);

  if (loading) {
    return (
      <main className="wizard-shell">
        <div className="loading-state">
          <div className="spinner-large"></div>
          <p>Loading configuration...</p>
        </div>
      </main>
    );
  }

  const models = taskType === "classification"
    ? ["logistic_regression", "random_forest", "xgboost", "lightgbm", "extra_trees", "knn"]
    : ["linear_regression", "random_forest", "xgboost", "lightgbm", "extra_trees"];

  return (
    <main className="wizard-shell">
      <header className="wizard-header">
        <h1>Configure Benchmark</h1>
        <p>Select target column, task type, and models</p>
      </header>

      <div className="wizard-content config-content">
        {error && (
          <div className="error-banner">
            <p>{error}</p>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        <section className="config-section glass-card">
          <h2>Task Settings</h2>
          
          <div className="form-row">
            <div className="form-field">
              <label>Target Column *</label>
              <select
                value={targetColumn}
                onChange={(e) => setTargetColumn(e.target.value)}
              >
                <option value="">Select column...</option>
                {dataset?.column_names.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>Task Type *</label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value as TaskType)}
              >
                <option value="regression">Regression</option>
                <option value="classification">Classification</option>
              </select>
            </div>
          </div>

          <div className="form-field">
            <label>Description (optional)</label>
            <input
              type="text"
              placeholder="e.g., Predict house prices"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </section>

        <section className="config-section glass-card">
          <div className="section-header">
            <h2>Models</h2>
            <div className="section-actions">
              <button className="btn btn-ghost btn-sm" onClick={selectAllModels}>
                Select All ({models.length})
              </button>
              <button className="btn btn-ghost btn-sm" onClick={deselectAllModels}>
                Deselect All
              </button>
            </div>
          </div>
          
          <div className="models-grid">
            {models.map((model) => (
              <label key={model} className="model-checkbox">
                <input
                  type="checkbox"
                  checked={selectedModels.includes(model)}
                  onChange={() => toggleModel(model)}
                />
                <span className="model-name">{model.replace(/_/g, " ")}</span>
              </label>
            ))}
          </div>
        </section>

        <section className="config-section glass-card">
          <h2>Data Split</h2>
          
          <div className="form-row">
            <div className="form-field">
              <label>Test Size</label>
              <div className="input-with-unit">
                <input
                  type="number"
                  min={0.05}
                  max={0.5}
                  step={0.05}
                  value={testSize}
                  onChange={(e) => setTestSize(parseFloat(e.target.value))}
                />
                <span className="unit">{Math.round(testSize * 100)}%</span>
              </div>
            </div>

            <div className="form-field">
              <label>Random State</label>
              <input
                type="number"
                min={0}
                value={randomState}
                onChange={(e) => setRandomState(parseInt(e.target.value))}
              />
            </div>
          </div>
        </section>

        <section className="config-section glass-card">
          <h2>Scoring Weights (must sum to 1.0)</h2>
          <div className="weights-grid">
            <div className="weight-field">
              <label>Performance</label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.1}
                value={weightPerf}
                onChange={(e) => setWeightPerf(parseFloat(e.target.value))}
              />
              <span className="weight-value">{weightPerf.toFixed(1)}</span>
            </div>
            <div className="weight-field">
              <label>Robustness</label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.1}
                value={weightRobust}
                onChange={(e) => setWeightRobust(parseFloat(e.target.value))}
              />
              <span className="weight-value">{weightRobust.toFixed(1)}</span>
            </div>
            <div className="weight-field">
              <label>Latency</label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.1}
                value={weightLat}
                onChange={(e) => setWeightLat(parseFloat(e.target.value))}
              />
              <span className="weight-value">{weightLat.toFixed(1)}</span>
            </div>
            <div className="weight-field">
              <label>Size</label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.1}
                value={weightSize}
                onChange={(e) => setWeightSize(parseFloat(e.target.value))}
              />
              <span className="weight-value">{weightSize.toFixed(1)}</span>
            </div>
          </div>
          <p className="weights-total">
            Total: <strong>{(weightPerf + weightRobust + weightLat + weightSize).toFixed(1)}</strong>
          </p>
        </section>

        <section className="config-section glass-card">
          <h2>Advanced Options</h2>
          <div className="form-field">
            <label>Latency Threshold (seconds, optional)</label>
            <input
              type="number"
              placeholder="No limit"
              min={0.1}
              step={0.1}
              value={latencyThreshold}
              onChange={(e) => setLatencyThreshold(e.target.value === "" ? "" : parseFloat(e.target.value))}
            />
            <span className="field-hint">Models exceeding this will be excluded</span>
          </div>
        </section>
      </div>

      <footer className="wizard-footer">
        <button className="btn btn-ghost" onClick={onBack}>
          Back
        </button>
        <button className="btn btn-brand" onClick={handleSubmit}>
          Run Benchmark
        </button>
      </footer>
    </main>
  );
};