// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/hooks/useApi.test.tsx
import { renderHook } from "@testing-library/react";
import { act } from "react";

import { useApi } from "./useApi";

describe("useApi", () => {
  it("lists datasets with mocked API response", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          items: [
            {
              id: "dataset-1",
              name: "Risk dataset",
              description: null,
              dataset_type: "tabular",
              status: "validated",
              file_path: "datasets/risk.csv",
              file_size_bytes: 100,
              file_format: "csv",
              row_count: 10,
              column_count: 3,
              schema_info: { columns: ["a", "b", "target"] },
              validation_report: {
                is_valid: true,
                total_rows: 10,
                total_columns: 3,
                null_counts: {},
                null_percentages: {},
                dtypes: {},
                duplicate_rows: 0,
                issues: [],
                warnings: [],
              },
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
            },
          ],
          total: 1,
          page: 1,
          page_size: 100,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    const { result } = renderHook(() => useApi());

    let datasets: Awaited<ReturnType<typeof result.current.listDatasets>> = [];
    await act(async () => {
      datasets = await result.current.listDatasets();
    });

    expect(datasets).toHaveLength(1);
    expect(datasets[0].name).toBe("Risk dataset");
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/api/v1/datasets?page=1&page_size=100", undefined);

    fetchMock.mockRestore();
  });

  it("surfaces api error detail", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Dataset not found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      })
    );

    const { result } = renderHook(() => useApi());

    await act(async () => {
      await expect(result.current.listDatasetVersions("missing-id")).rejects.toThrow("Dataset not found");
    });

    fetchMock.mockRestore();
  });

  it("fetches dataset autoconfig", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          dataset_id: "dataset-1",
          suggested_name: "Risk dataset",
          task_type: "classification",
          target_column: "target",
          feature_columns: ["a", "b"],
          stratify_column: "target",
          confidence: "high",
          rationale: "Detected by target name",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    const { result } = renderHook(() => useApi());

    await act(async () => {
      const data = await result.current.getDatasetAutoConfig("dataset-1");
      expect(data.task_type).toBe("classification");
      expect(data.target_column).toBe("target");
    });

    fetchMock.mockRestore();
  });
});
