// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step3ModelPage.tsx
import type { ModelCatalogueEntry } from "../types";
import { SpinnerPanel } from "../components/SpinnerPanel";

interface Step3ModelPageProps {
  columns: string[];
  targetColumn: string;
  selectedFeatures: string[];
  models: ModelCatalogueEntry[];
  selectedModels: ModelCatalogueEntry[];
  loading: boolean;
  error: string | null;
  onTargetColumnChange: (value: string) => void;
  onToggleFeature: (value: string) => void;
  onToggleModel: (model: ModelCatalogueEntry) => void;
}

export const Step3ModelPage = ({
  columns,
  targetColumn,
  selectedFeatures,
  models,
  selectedModels,
  loading,
  error,
  onTargetColumnChange,
  onToggleFeature,
  onToggleModel,
}: Step3ModelPageProps) => {
  return (
    <section className="step-content">
      <header>
        <p className="eyebrow">Step 3</p>
        <h2>Choose target, features, and models</h2>
        <p>Pick what to predict and which models to benchmark side-by-side.</p>
      </header>

      <div className="grid-two">
        <article className="glass-card form-card">
          <h3>Prediction setup</h3>

          <label>
            Target column
            <select value={targetColumn} onChange={(event) => onTargetColumnChange(event.target.value)}>
              <option value="">Select target column</option>
              {columns.map((column) => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </label>

          <fieldset>
            <legend>Feature columns</legend>
            <div className="chip-grid">
              {columns
                .filter((column) => column !== targetColumn)
                .map((column) => {
                  const selected = selectedFeatures.includes(column);
                  return (
                    <button
                      type="button"
                      key={column}
                      className={`chip ${selected ? "is-active" : ""}`}
                      onClick={() => onToggleFeature(column)}
                    >
                      {column}
                    </button>
                  );
                })}
            </div>
          </fieldset>
        </article>

        <article className="glass-card dataset-card">
          <h3>Model catalogue</h3>

          {loading ? <SpinnerPanel text="Loading model catalogue..." /> : null}

          <div className="model-list">
            {!loading &&
              models.map((model) => {
                const selected = selectedModels.some((entry) => entry.name === model.name);
                return (
                  <label key={model.name} className={`model-list__item ${selected ? "is-selected" : ""}`}>
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => onToggleModel(model)}
                      aria-label={`Toggle ${model.name}`}
                    />
                    <div>
                      <strong>{model.name}</strong>
                      <small>{model.description}</small>
                    </div>
                    <em>{model.family}</em>
                  </label>
                );
              })}
          </div>
        </article>
      </div>

      {error ? <p className="error-banner">{error}</p> : null}
    </section>
  );
};
