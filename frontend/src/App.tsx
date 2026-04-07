// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/App.tsx
import { useEffect, useMemo, useRef, useState } from "react";
import { ActionBar } from "./components/ActionBar";
import { ProgressRail } from "./components/ProgressRail";
import { useApi } from "./hooks/useApi";
import { Step1UploadPage } from "./pages/Step1UploadPage";
import { Step2VersionPage } from "./pages/Step2VersionPage";
import { Step3ModelPage } from "./pages/Step3ModelPage";
import { Step4RunPage } from "./pages/Step4RunPage";
import { Step5ReportPage } from "./pages/Step5ReportPage";
import { WIZARD_STEPS, useWizardStore } from "./store/wizardStore";
import type {
  DatasetRead,
  DatasetVersionRead,
  EvaluationReportResponse,
  ExperimentRead,
  ExperimentResultRead,
  ExperimentSummary,
  ModelCatalogueEntry,
  TaskType,
} from "./types";

export const App = () => {
  const {
    step,
    draft,
    progress,
    canGoBack,
    canGoForward,
    previousStep,
    goToStep,
    updateDraft,
  } = useWizardStore();
  const api = useApi();

  const [datasets, setDatasets] = useState<DatasetRead[]>([]);
  const [versions, setVersions] = useState<DatasetVersionRead[]>([]);
  const [models, setModels] = useState<ModelCatalogueEntry[]>([]);
  const [experiment, setExperiment] = useState<ExperimentRead | null>(null);
  const [summary, setSummary] = useState<ExperimentSummary | null>(null);
  const [results, setResults] = useState<ExperimentResultRead[]>([]);
  const [report, setReport] = useState<EvaluationReportResponse | null>(null);
  const [runState, setRunState] = useState<"idle" | "creating" | "running" | "polling" | "completed" | "failed">(
    "idle"
  );

  const pollingRef = useRef<number | null>(null);

  const columns = useMemo(() => draft.dataset?.schema_info?.columns ?? [], [draft.dataset]);

  const clearPoll = () => {
    if (pollingRef.current) {
      window.clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => {
    void (async () => {
      try {
        const items = await api.listDatasets();
        setDatasets(items);
      } catch {
        // handled by hook error
      }
    })();
  }, []);

  useEffect(() => {
    if (!draft.dataset) {
      setVersions([]);
      return;
    }

    void (async () => {
      try {
        const nextVersions = await api.listDatasetVersions(draft.dataset!.id);
        setVersions(nextVersions);
      } catch {
        // handled by hook error
      }
    })();
  }, [draft.dataset?.id]);

  useEffect(() => {
    void (async () => {
      try {
        const nextModels = await api.listModels(draft.taskType);
        setModels(nextModels);
      } catch {
        // handled by hook error
      }
    })();
  }, [draft.taskType]);

  useEffect(() => {
    return () => {
      clearPoll();
    };
  }, []);

  const handleDatasetUpload = async (file: File, name: string, description: string) => {
    const uploaded = await api.uploadDataset(file, name, description);
    const nextDatasets = await api.listDatasets();
    setDatasets(nextDatasets);
    updateDraft({ dataset: uploaded, datasetVersion: null, targetColumn: "", selectedFeatures: [] });
  };

  const handleCreateVersion = async (payload: {
    train_ratio: number;
    val_ratio: number;
    test_ratio: number;
    random_seed: number;
    stratify_column?: string;
  }) => {
    if (!draft.dataset) {
      return;
    }

    const version = await api.createDatasetVersion(draft.dataset.id, payload);
    const nextVersions = await api.listDatasetVersions(draft.dataset.id);
    setVersions(nextVersions);
    updateDraft({ datasetVersion: version });
  };

  const handleToggleFeature = (feature: string) => {
    if (draft.selectedFeatures.includes(feature)) {
      updateDraft({ selectedFeatures: draft.selectedFeatures.filter((f) => f !== feature) });
      return;
    }

    updateDraft({ selectedFeatures: [...draft.selectedFeatures, feature] });
  };

  const handleToggleModel = (model: ModelCatalogueEntry) => {
    const exists = draft.selectedModels.some((entry) => entry.name === model.name);
    if (exists) {
      updateDraft({ selectedModels: draft.selectedModels.filter((entry) => entry.name !== model.name) });
      return;
    }

    updateDraft({ selectedModels: [...draft.selectedModels, model] });
  };

  const enforceStepGuards = (next: number): number => {
    if (next > 1 && !draft.dataset) {
      return 1;
    }

    if (next > 2 && !draft.datasetVersion) {
      return 2;
    }

    if (next > 3 && (!draft.targetColumn || draft.selectedFeatures.length === 0 || draft.selectedModels.length === 0)) {
      return 3;
    }

    if (next > 4 && !experiment) {
      return 4;
    }

    return next;
  };

  const navigateNext = () => {
    const target = enforceStepGuards(step + 1);
    goToStep(target);
  };

  const navigateBack = () => {
    previousStep();
  };

  const navigateTo = (next: number) => {
    const guarded = enforceStepGuards(next);
    goToStep(guarded);
  };

  const pollExperimentUntilDone = (experimentId: string) => {
    clearPoll();
    setRunState("polling");

    pollingRef.current = window.setInterval(async () => {
      try {
        const latest = await api.getExperiment(experimentId);
        setExperiment(latest);

        if (latest.status === "completed" || latest.status === "failed") {
          clearPoll();

          const [nextSummary, nextResults] = await Promise.all([
            api.getExperimentSummary(experimentId),
            api.getExperimentResults(experimentId),
          ]);

          setSummary(nextSummary);
          setResults(nextResults);

          if (latest.status === "completed") {
            const nextReport = await api.generateReport(experimentId);
            setReport(nextReport);
            setRunState("completed");
            goToStep(5);
          } else {
            setRunState("failed");
          }
        }
      } catch {
        clearPoll();
        setRunState("failed");
      }
    }, 2500);
  };

  const handleCreateAndRun = async (payload: { name: string; description: string; randomSeed: number }) => {
    if (!draft.dataset || !draft.datasetVersion || !draft.targetColumn || draft.selectedFeatures.length === 0) {
      return;
    }

    setRunState("creating");

    const modelsPayload = draft.selectedModels.map((model) => ({
      name: model.name,
      family: model.family,
      class_name: model.class_name,
      hyperparameters: model.default_hyperparameters,
      enabled: true,
    }));

    const created = await api.createExperiment({
      name: payload.name,
      description: payload.description || null,
      experiment_type: "tabular_ml",
      task_type: draft.taskType,
      dataset_id: draft.dataset.id,
      dataset_version_id: draft.datasetVersion.id,
      target_column: draft.targetColumn,
      feature_columns: draft.selectedFeatures,
      models: modelsPayload,
      random_seed: payload.randomSeed,
    });

    setExperiment(created);
    setRunState("running");

    const started = await api.runExperiment(created.id);
    setExperiment(started);

    pollExperimentUntilDone(started.id);
  };

  const currentStepTitle = WIZARD_STEPS.find((entry) => entry.id === step)?.title ?? "Wizard";

  return (
    <div className="app-shell">
      <ProgressRail currentStep={step} progress={progress} onStepClick={navigateTo} />

      <main className="workspace">
        <div className="workspace__header">
          <div>
            <p className="eyebrow">Decision Assistant</p>
            <h2>{currentStepTitle}</h2>
          </div>
          <a href={`${api.apiBaseUrl.replace("/api/v1", "")}/docs`} target="_blank" rel="noreferrer">
            API Docs
          </a>
        </div>

        {step === 1 ? (
          <Step1UploadPage
            datasets={datasets}
            selectedDataset={draft.dataset}
            loading={api.loading}
            error={api.error}
            onUpload={handleDatasetUpload}
            onSelectDataset={(dataset) => updateDraft({ dataset, datasetVersion: null, targetColumn: "", selectedFeatures: [] })}
            onTaskTypeChange={(task) => updateDraft({ taskType: task as TaskType })}
            taskType={draft.taskType as "classification" | "regression"}
          />
        ) : null}

        {step === 2 ? (
          <Step2VersionPage
            dataset={draft.dataset}
            versions={versions}
            selectedVersion={draft.datasetVersion}
            columns={columns}
            loading={api.loading}
            error={api.error}
            onCreateVersion={handleCreateVersion}
            onSelectVersion={(version) => updateDraft({ datasetVersion: version })}
          />
        ) : null}

        {step === 3 ? (
          <Step3ModelPage
            columns={columns}
            targetColumn={draft.targetColumn}
            selectedFeatures={draft.selectedFeatures}
            models={models}
            selectedModels={draft.selectedModels}
            loading={api.loading}
            error={api.error}
            onTargetColumnChange={(value) =>
              updateDraft({
                targetColumn: value,
                selectedFeatures: draft.selectedFeatures.filter((entry) => entry !== value),
              })
            }
            onToggleFeature={handleToggleFeature}
            onToggleModel={handleToggleModel}
          />
        ) : null}

        {step === 4 ? (
          <Step4RunPage
            selectedModelCount={draft.selectedModels.length}
            selectedModels={draft.selectedModels}
            loading={api.loading}
            runningState={runState}
            experiment={experiment}
            error={api.error}
            defaultName={draft.experimentName || `${draft.dataset?.name ?? "Dataset"} Benchmark`}
            defaultDescription={draft.experimentDescription}
            randomSeed={draft.randomSeed}
            onSubmit={async ({ name, description, randomSeed }) => {
              updateDraft({
                experimentName: name,
                experimentDescription: description,
                randomSeed,
              });
              await handleCreateAndRun({ name, description, randomSeed });
            }}
          />
        ) : null}

        {step === 5 ? (
          <Step5ReportPage summary={summary} report={report} results={results} loading={api.loading} error={api.error} />
        ) : null}

        <ActionBar
          canGoBack={canGoBack}
          canGoForward={canGoForward}
          onBack={navigateBack}
          onNext={navigateNext}
          disabled={api.loading || runState === "polling"}
          nextLabel={step === 5 ? "Done" : "Continue"}
        />
      </main>
    </div>
  );
};
