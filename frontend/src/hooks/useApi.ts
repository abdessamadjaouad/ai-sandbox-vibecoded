// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/hooks/useApi.ts
import { useCallback, useMemo, useState } from "react";
import type {
  DatasetAutoConfigRead,
  DatasetListResponse,
  DatasetRead,
  DatasetVersionRead,
  EvaluationReportResponse,
  ExperimentCreatePayload,
  ExperimentRead,
  ExperimentResultRead,
  ExperimentSummary,
  ModelCatalogueEntry,
  TaskType,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const data = (await response.json()) as { detail?: string };
      if (typeof data.detail === "string") {
        message = data.detail;
      }
    } catch {
      // no-op
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const withLoading = useCallback(async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      return await fn();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unexpected error";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadDataset = useCallback(
    async (file: File, name: string, description: string): Promise<DatasetRead> =>
      withLoading(async () => {
        const formData = new FormData();
        formData.append("file", file);
        if (name.trim()) {
          formData.append("name", name);
        }
        if (description.trim()) {
          formData.append("description", description.trim());
        }

        const response = await fetch(`${API_BASE_URL}/datasets`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const data = (await response.json()) as { detail?: string };
          throw new ApiError(data.detail ?? "Failed to upload dataset", response.status);
        }

        return (await response.json()) as DatasetRead;
      }),
    [withLoading]
  );

  const getDatasetAutoConfig = useCallback(
    async (datasetId: string): Promise<DatasetAutoConfigRead> =>
      withLoading(async () => requestJson<DatasetAutoConfigRead>(`${API_BASE_URL}/datasets/${datasetId}/autoconfig`)),
    [withLoading]
  );

  const listDatasets = useCallback(
    async (): Promise<DatasetRead[]> =>
      withLoading(async () => {
        const data = await requestJson<DatasetListResponse>(`${API_BASE_URL}/datasets?page=1&page_size=100`);
        return data.items;
      }),
    [withLoading]
  );

  const listDatasetVersions = useCallback(
    async (datasetId: string): Promise<DatasetVersionRead[]> =>
      withLoading(async () => requestJson<DatasetVersionRead[]>(`${API_BASE_URL}/datasets/${datasetId}/versions`)),
    [withLoading]
  );

  const createDatasetVersion = useCallback(
    async (
      datasetId: string,
      payload: {
        train_ratio: number;
        val_ratio: number;
        test_ratio: number;
        random_seed: number;
        stratify_column?: string;
      }
    ): Promise<DatasetVersionRead> =>
      withLoading(async () =>
        requestJson<DatasetVersionRead>(`${API_BASE_URL}/datasets/${datasetId}/versions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
      ),
    [withLoading]
  );

  const listModels = useCallback(
    async (taskType: TaskType): Promise<ModelCatalogueEntry[]> =>
      withLoading(async () =>
        requestJson<ModelCatalogueEntry[]>(`${API_BASE_URL}/experiments/catalogue/models?task_type=${taskType}`)
      ),
    [withLoading]
  );

  const createExperiment = useCallback(
    async (payload: ExperimentCreatePayload): Promise<ExperimentRead> =>
      withLoading(async () =>
        requestJson<ExperimentRead>(`${API_BASE_URL}/experiments`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
      ),
    [withLoading]
  );

  const runExperiment = useCallback(
    async (experimentId: string): Promise<ExperimentRead> =>
      withLoading(async () =>
        requestJson<ExperimentRead>(`${API_BASE_URL}/experiments/${experimentId}/run`, {
          method: "POST",
        })
      ),
    [withLoading]
  );

  const getExperiment = useCallback(
    async (experimentId: string): Promise<ExperimentRead> =>
      withLoading(async () => requestJson<ExperimentRead>(`${API_BASE_URL}/experiments/${experimentId}`)),
    [withLoading]
  );

  const getExperimentSummary = useCallback(
    async (experimentId: string): Promise<ExperimentSummary> =>
      withLoading(async () => requestJson<ExperimentSummary>(`${API_BASE_URL}/experiments/${experimentId}/summary`)),
    [withLoading]
  );

  const getExperimentResults = useCallback(
    async (experimentId: string): Promise<ExperimentResultRead[]> =>
      withLoading(async () => requestJson<ExperimentResultRead[]>(`${API_BASE_URL}/experiments/${experimentId}/results`)),
    [withLoading]
  );

  const generateReport = useCallback(
    async (experimentId: string): Promise<EvaluationReportResponse> =>
      withLoading(async () =>
        requestJson<EvaluationReportResponse>(`${API_BASE_URL}/evaluation/report/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ experiment_id: experimentId }),
        })
      ),
    [withLoading]
  );

  return useMemo(
    () => ({
      apiBaseUrl: API_BASE_URL,
      loading,
      error,
      clearError: () => setError(null),
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
    }),
    [
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
    ]
  );
};
