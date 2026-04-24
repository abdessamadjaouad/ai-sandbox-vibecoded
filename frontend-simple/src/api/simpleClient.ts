// /home/jao/Desktop/sandbox-project-vibecoded/frontend-simple/src/api/simpleClient.ts
import type {
  SimpleDatasetInfo,
  SuggestionResponse,
  SimpleRunConfig,
  SimpleRunResult,
} from "../types";

const API_BASE_URL = import.meta.env.DEV 
  ? "http://localhost:8000/api" 
  : "/api";

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

export const simpleApi = {
  async healthCheck(): Promise<{ status: string; app_name: string; version: string }> {
    return requestJson(`${API_BASE_URL}/health`);
  },

  async uploadDataset(file: File): Promise<SimpleDatasetInfo> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const data = (await response.json()) as { detail?: string };
      throw new ApiError(data.detail ?? "Upload failed", response.status);
    }
    return (await response.json()) as SimpleDatasetInfo;
  },

  async listDatasets(): Promise<SimpleDatasetInfo[]> {
    return requestJson<SimpleDatasetInfo[]>(`${API_BASE_URL}/datasets`);
  },

  async suggestConfig(datasetId: string): Promise<SuggestionResponse> {
    return requestJson<SuggestionResponse>(
      `${API_BASE_URL}/dataset/${datasetId}/suggest`
    );
  },

  async runBenchmark(config: SimpleRunConfig): Promise<SimpleRunResult> {
    return requestJson<SimpleRunResult>(`${API_BASE_URL}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
  },

  async runBenchmarkStream(
    config: SimpleRunConfig,
    onProgress: (data: { event: string; message?: string; step?: string; data?: unknown }) => void
  ): Promise<SimpleRunResult> {
    const response = await fetch(`${API_BASE_URL}/run/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const data = (await response.json()) as { detail?: string };
      throw new ApiError(data.detail ?? "Run failed", response.status);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new ApiError("No response body", 500);
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const jsonStr = line.slice(6);
          try {
            const data = JSON.parse(jsonStr);
            onProgress(data);
            if (data.event === "result") {
              return data.data as SimpleRunResult;
            }
            if (data.event === "error") {
              throw new ApiError(data.message ?? "Run failed", 500);
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }

    throw new ApiError("No result received", 500);
  },

  async getRunState(): Promise<{ is_training: boolean; stop_requested: boolean }> {
    return requestJson(`${API_BASE_URL}/run/state`);
  },

  async stopRun(): Promise<{ status: string; message: string }> {
    return requestJson(`${API_BASE_URL}/run/stop`, { method: "POST" });
  },

  async getResults(runId: string): Promise<SimpleRunResult> {
    return requestJson<SimpleRunResult>(`${API_BASE_URL}/results/${runId}`);
  },

  async getReportContent(runId: string): Promise<{ run_id: string; content: string; filename: string }> {
    return requestJson(`${API_BASE_URL}/report/${runId}/content`);
  },

  getReportDownloadUrl(runId: string): string {
    return `${API_BASE_URL}/report/${runId}`;
  },
};