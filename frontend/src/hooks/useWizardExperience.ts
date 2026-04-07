// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/hooks/useWizardExperience.ts
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useWizardStore } from "../store/wizardStore";
import type {
  DatasetAutoConfigRead,
  DatasetRead,
  DatasetVersionRead,
  EvaluationReportResponse,
  ExperimentRead,
  ExperimentResultRead,
  ExperimentSummary,
  ModelCatalogueEntry,
  TaskType,
} from "../types";
import { useApi } from "./useApi";

const RUN_STATUS_MESSAGE: Record<string, string> = {
  idle: "Ready to launch benchmark.",
  creating: "Creating experiment configuration...",
  running: "Experiment started. Preparing data...",
  polling: "Benchmark in progress. Training and evaluating selected models...",
  completed: "Benchmark completed successfully.",
  failed: "Benchmark failed. Review the message and retry.",
  pending: "Waiting in queue...",
  validating: "Validating inputs...",
  preparing: "Preparing dataset and model setup...",
  evaluating: "Computing metrics and ranking models...",
  cancelled: "Run cancelled.",
};

const toUiTaskType = (taskType: DatasetAutoConfigRead["task_type"]): TaskType =>
  taskType === "regression" ? "regression" : "classification";

export const useWizardExperience = () => {
  const store = useWizardStore();
  const {
    apiBaseUrl,
    loading,
    error,
    uploadDataset,
    listDatasets,
    listDatasetVersions,
    getDatasetAutoConfig,
    createDatasetVersion,
    listModels,
    createExperiment,
    runExperiment,
    getExperiment,
    getExperimentSummary,
    getExperimentResults,
    generateReport,
  } = useApi();

  const [view, setView] = useState<"landing" | "wizard">("landing");
  const [theme, setTheme] = useState<"light" | "dark">("light");

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
  const [autoConfig, setAutoConfig] = useState<DatasetAutoConfigRead | null>(null);

  const pollingRef = useRef<number | null>(null);
  const lastRunPayloadRef = useRef<{ name: string; description: string; randomSeed: number } | null>(null);

  const columns = useMemo(() => store.draft.dataset?.schema_info?.columns ?? [], [store.draft.dataset]);
  const taskType = store.draft.taskType === "regression" ? "regression" : "classification";

  const applyAutoConfig = useCallback(
    (config: DatasetAutoConfigRead, availableColumns: string[], availableModels: ModelCatalogueEntry[]) => {
      const normalizedTaskType = toUiTaskType(config.task_type);
      const resolvedTarget =
        config.target_column && availableColumns.includes(config.target_column) ? config.target_column : "";
      const resolvedFeatures = config.feature_columns.length
        ? config.feature_columns.filter((entry) => availableColumns.includes(entry) && entry !== resolvedTarget)
        : availableColumns.filter((entry) => entry !== resolvedTarget);

      const filteredModels = availableModels.filter((model) => model.task_types.includes(normalizedTaskType));
      const defaultSelectedModels = filteredModels.slice(0, Math.min(5, filteredModels.length));

      store.updateDraft({
        taskType: normalizedTaskType,
        targetColumn: resolvedTarget,
        selectedFeatures: resolvedFeatures,
        selectedModels: defaultSelectedModels,
        experimentName: `${config.suggested_name} Benchmark`,
        experimentDescription: `Automated benchmark for ${config.suggested_name}`,
        stratifyColumn: config.stratify_column ?? "",
      });
    },
    [store]
  );

  const clearPoll = () => {
    if (pollingRef.current) {
      window.clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const refreshDatasets = useCallback(async () => {
    const items = await listDatasets();
    setDatasets(items);
  }, [listDatasets]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    void (async () => {
      try {
        await refreshDatasets();
      } catch {
        // handled by hook error state
      }
    })();
  }, [refreshDatasets]);

  useEffect(() => {
    if (!store.draft.dataset) {
      setVersions([]);
      setAutoConfig(null);
      return;
    }

    void (async () => {
      try {
        const [nextVersions, detectedConfig] = await Promise.all([
          listDatasetVersions(store.draft.dataset!.id),
          getDatasetAutoConfig(store.draft.dataset!.id),
        ]);

        setVersions(nextVersions);
        setAutoConfig(detectedConfig);

        const candidateModels = await listModels(toUiTaskType(detectedConfig.task_type));
        setModels(candidateModels);

        const availableColumns = store.draft.dataset?.schema_info?.columns ?? [];
        applyAutoConfig(detectedConfig, availableColumns, candidateModels);
      } catch {
        // handled by hook error state
      }
    })();
  }, [store.draft.dataset?.id]);

  useEffect(() => {
    return () => {
      clearPoll();
    };
  }, []);

  const handleDatasetUpload = async (file: File, name: string, description: string) => {
    const uploaded = await uploadDataset(file, name, description);
    const [nextDatasets, detectedConfig] = await Promise.all([refreshDatasets(), getDatasetAutoConfig(uploaded.id)]);
    setDatasets(nextDatasets ?? datasets);
    setAutoConfig(detectedConfig);

    const detectedTask = toUiTaskType(detectedConfig.task_type);
    const candidateModels = await listModels(detectedTask);
    setModels(candidateModels);

    store.updateDraft({
      dataset: uploaded,
      datasetVersion: null,
      taskType: detectedTask,
      targetColumn: detectedConfig.target_column ?? "",
      selectedFeatures: detectedConfig.feature_columns,
      selectedModels: candidateModels.slice(0, Math.min(candidateModels.length, 5)),
      experimentName: `${detectedConfig.suggested_name} Benchmark`,
      experimentDescription: `Automated benchmark for ${detectedConfig.suggested_name}`,
      stratifyColumn: detectedConfig.stratify_column ?? "",
    });
  };

  const handleCreateVersion = async () => {
    if (!store.draft.dataset) {
      return;
    }

    const payload = {
      train_ratio: store.draft.trainRatio,
      val_ratio: store.draft.valRatio,
      test_ratio: store.draft.testRatio,
      random_seed: store.draft.randomSeed,
      stratify_column: store.draft.stratifyColumn || undefined,
    };

    const version = await createDatasetVersion(store.draft.dataset.id, payload);
    const nextVersions = await listDatasetVersions(store.draft.dataset.id);
    setVersions(nextVersions);
    store.updateDraft({ datasetVersion: version });
  };

  const pollExperimentUntilDone = (experimentId: string) => {
    clearPoll();
    setRunState("polling");

    pollingRef.current = window.setInterval(async () => {
      try {
        const latest = await getExperiment(experimentId);
        setExperiment(latest);

        if (latest.status === "completed" || latest.status === "failed") {
          clearPoll();

          const [nextSummary, nextResults] = await Promise.all([
            getExperimentSummary(experimentId),
            getExperimentResults(experimentId),
          ]);

          setSummary(nextSummary);
          setResults(nextResults);

          if (latest.status === "completed") {
            const nextReport = await generateReport(experimentId);
            setReport(nextReport);
            setRunState("completed");
            store.goToStep(5);
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
    if (!store.draft.dataset || !store.draft.datasetVersion || !store.draft.targetColumn || store.draft.selectedFeatures.length === 0) {
      return;
    }

    setRunState("creating");

    const created = await createExperiment({
      name: payload.name,
      description: payload.description || null,
      experiment_type: "tabular_ml",
      task_type: store.draft.taskType,
      dataset_id: store.draft.dataset.id,
      dataset_version_id: store.draft.datasetVersion.id,
      target_column: store.draft.targetColumn,
      feature_columns: store.draft.selectedFeatures,
      models: store.draft.selectedModels.map((model) => ({
        name: model.name,
        family: model.family,
        class_name: model.class_name,
        hyperparameters: model.default_hyperparameters,
        enabled: true,
      })),
      random_seed: payload.randomSeed,
    });

    setExperiment(created);
    setRunState("running");

    const started = await runExperiment(created.id);
    setExperiment(started);
    lastRunPayloadRef.current = payload;

    pollExperimentUntilDone(started.id);
  };

  return {
    apiBaseUrl,
    loading,
    error,
    view,
    setView,
    theme,
    toggleTheme: () => setTheme((current) => (current === "light" ? "dark" : "light")),
    datasets,
    versions,
    models,
    experiment,
    summary,
    results,
    report,
    runState,
    autoConfig,
    columns,
    taskType,
    progressMessage: experiment?.status ? RUN_STATUS_MESSAGE[experiment.status] ?? RUN_STATUS_MESSAGE[runState] : RUN_STATUS_MESSAGE[runState],
    handleDatasetUpload,
    handleCreateVersion,
    handleCreateAndRun,
    handleRetryRun: async () => {
      if (!lastRunPayloadRef.current) {
        return;
      }
      await handleCreateAndRun(lastRunPayloadRef.current);
    },
    refreshDatasets,
    ...store,
  };
};
