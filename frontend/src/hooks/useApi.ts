// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/hooks/useApi.ts
import { useCallback, useMemo, useState } from "react";
import type {
  AgentBatchEvaluationResponse,
  AgentRunResponseV1,
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

const API_BASE_URL = import.meta.env.DEV ? "http://localhost:8000/api/v1" : "/api/v1";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

type AuthHeadersGetter = () => HeadersInit;

async function requestJson<T>(url: string, init?: RequestInit, authHeaders?: HeadersInit): Promise<T> {
  const headers: HeadersInit = {
    ...authHeaders,
    ...init?.headers,
  };
  const response = await fetch(url, { ...init, headers });

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

export const useApi = (getAuthHeaders?: AuthHeadersGetter) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const authHeaders = getAuthHeaders ? getAuthHeaders() : {};

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

  const listExperiments = useCallback(
    async (page: number = 1, pageSize: number = 20): Promise<{ items: ExperimentRead[]; total: number; page: number; page_size: number }> =>
      withLoading(async () =>
        requestJson<{ items: ExperimentRead[]; total: number; page: number; page_size: number }>(
          `${API_BASE_URL}/experiments?page=${page}&page_size=${pageSize}`,
          {},
          authHeaders
        )
      ),
    [withLoading, authHeaders]
  );

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
          headers: authHeaders,
        });

        if (!response.ok) {
          const data = (await response.json()) as { detail?: string };
          throw new ApiError(data.detail ?? "Failed to upload dataset", response.status);
        }

        return (await response.json()) as DatasetRead;
      }),
    [withLoading, authHeaders]
  );

  const getDatasetAutoConfig = useCallback(
    async (datasetId: string): Promise<DatasetAutoConfigRead> =>
      withLoading(async () => requestJson<DatasetAutoConfigRead>(`${API_BASE_URL}/datasets/${datasetId}/autoconfig`, {}, authHeaders)),
    [withLoading, authHeaders]
  );

  const listDatasets = useCallback(
    async (): Promise<DatasetRead[]> =>
      withLoading(async () => {
        const data = await requestJson<DatasetListResponse>(`${API_BASE_URL}/datasets?page=1&page_size=100`, {}, authHeaders);
        return data.items;
      }),
    [withLoading, authHeaders]
  );

  const listDatasetVersions = useCallback(
    async (datasetId: string): Promise<DatasetVersionRead[]> =>
      withLoading(async () => requestJson<DatasetVersionRead[]>(`${API_BASE_URL}/datasets/${datasetId}/versions`, {}, authHeaders)),
    [withLoading, authHeaders]
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
        requestJson<DatasetVersionRead>(
          `${API_BASE_URL}/datasets/${datasetId}/versions`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders },
            body: JSON.stringify(payload),
          },
          authHeaders
        )
      ),
    [withLoading, authHeaders]
  );

  const listModels = useCallback(
    async (taskType: TaskType): Promise<ModelCatalogueEntry[]> =>
      withLoading(async () =>
        requestJson<ModelCatalogueEntry[]>(`${API_BASE_URL}/experiments/catalogue/models?task_type=${taskType}`, {}, authHeaders)
      ),
    [withLoading, authHeaders]
  );

  const createExperiment = useCallback(
    async (payload: ExperimentCreatePayload): Promise<ExperimentRead> =>
      withLoading(async () =>
        requestJson<ExperimentRead>(
          `${API_BASE_URL}/experiments`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders },
            body: JSON.stringify(payload),
          },
          authHeaders
        )
      ),
    [withLoading, authHeaders]
  );

  const runExperiment = useCallback(
    async (experimentId: string): Promise<ExperimentRead> =>
      withLoading(async () =>
        requestJson<ExperimentRead>(`${API_BASE_URL}/experiments/${experimentId}/run`, { method: "POST" }, authHeaders)
      ),
    [withLoading, authHeaders]
  );

  const getExperiment = useCallback(
    async (experimentId: string): Promise<ExperimentRead> =>
      withLoading(async () => requestJson<ExperimentRead>(`${API_BASE_URL}/experiments/${experimentId}`, {}, authHeaders)),
    [withLoading, authHeaders]
  );

  const getExperimentSummary = useCallback(
    async (experimentId: string): Promise<ExperimentSummary> =>
      withLoading(async () => requestJson<ExperimentSummary>(`${API_BASE_URL}/experiments/${experimentId}/summary`, {}, authHeaders)),
    [withLoading, authHeaders]
  );

  const getExperimentResults = useCallback(
    async (experimentId: string): Promise<ExperimentResultRead[]> =>
      withLoading(async () => requestJson<ExperimentResultRead[]>(`${API_BASE_URL}/experiments/${experimentId}/results`, {}, authHeaders)),
    [withLoading, authHeaders]
  );

  const generateReport = useCallback(
    async (experimentId: string): Promise<EvaluationReportResponse> =>
      withLoading(async () =>
        requestJson<EvaluationReportResponse>(
          `${API_BASE_URL}/evaluation/report/generate`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders },
            body: JSON.stringify({ experiment_id: experimentId }),
          },
          authHeaders
        )
      ),
    [withLoading, authHeaders]
  );

  // Agent Evaluation endpoints
  const evaluateAgentBatch = useCallback(
    async (responses: AgentRunResponseV1[]): Promise<AgentBatchEvaluationResponse> =>
      withLoading(async () =>
        requestJson<AgentBatchEvaluationResponse>(
          `${API_BASE_URL}/evaluation/agent/batch`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders },
            body: JSON.stringify({ responses }),
          },
          authHeaders
        )
      ),
    [withLoading, authHeaders]
  );

  const evaluateAgentSingle = useCallback(
    async (response: AgentRunResponseV1): Promise<AgentBatchEvaluationResponse> =>
      withLoading(async () =>
        requestJson<AgentBatchEvaluationResponse>(
          `${API_BASE_URL}/evaluation/agent/submit`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders },
            body: JSON.stringify(response),
          },
          authHeaders
        )
      ),
    [withLoading, authHeaders]
  );

  const getAgentEvaluationReport = useCallback(
    async (evalId: string, format: "json" | "markdown" = "json"): Promise<AgentBatchEvaluationResponse | string> =>
      withLoading(async () => {
        const url = `${API_BASE_URL}/evaluation/agent/${evalId}/report?format=${format}`;
        if (format === "markdown") {
          const res = await fetch(url, { headers: authHeaders });
          if (!res.ok) throw new ApiError("Failed to fetch report", res.status);
          return await res.text();
        }
        return requestJson<AgentBatchEvaluationResponse>(url, {}, authHeaders);
      }),
    [withLoading, authHeaders]
  );

  const getAgentApiContract = useCallback(
    async (): Promise<Record<string, unknown>> =>
      withLoading(async () => requestJson<Record<string, unknown>>(`${API_BASE_URL}/evaluation/agent/contract`, {}, authHeaders)),
    [withLoading, authHeaders]
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
      listExperiments,
      evaluateAgentBatch,
      evaluateAgentSingle,
      getAgentEvaluationReport,
      getAgentApiContract,
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
      listExperiments,
      evaluateAgentBatch,
      evaluateAgentSingle,
      getAgentEvaluationReport,
      getAgentApiContract,
    ]
  );
};
