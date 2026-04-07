// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step1UploadPage.test.tsx
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Step1UploadPage } from "./Step1UploadPage";
import type { DatasetRead } from "../types";

const datasetFixture: DatasetRead = {
  id: "f7fdd9dd-08fa-4d6f-a204-66af9f8f8f1e",
  name: "Credit-Risk-Q2",
  description: "Quarterly risk set",
  dataset_type: "tabular",
  status: "validated",
  file_path: "datasets/credit.csv",
  file_size_bytes: 128000,
  file_format: "csv",
  row_count: 300,
  column_count: 12,
  schema_info: {
    columns: ["age", "income", "risk_label"],
    dtypes: {
      age: "int64",
      income: "float64",
      risk_label: "int64",
    },
    nullable: {
      age: false,
      income: false,
      risk_label: false,
    },
  },
  validation_report: {
    is_valid: true,
    total_rows: 300,
    total_columns: 12,
    null_counts: {},
    null_percentages: {},
    dtypes: {
      age: "int64",
      income: "float64",
      risk_label: "int64",
    },
    duplicate_rows: 0,
    issues: [],
    warnings: [],
  },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("Step1UploadPage", () => {
  it("switches task type when user chooses regression", async () => {
    const user = userEvent.setup();
    const onTaskTypeChange = vi.fn();

    render(
      <Step1UploadPage
        datasets={[]}
        selectedDataset={null}
        loading={false}
        error={null}
        onUpload={vi.fn()}
        onSelectDataset={vi.fn()}
        onTaskTypeChange={onTaskTypeChange}
        taskType="classification"
      />
    );

    await user.click(screen.getByRole("button", { name: "Regression" }));

    expect(onTaskTypeChange).toHaveBeenCalledWith("regression");
  });

  it("shows selected dataset preview details", () => {
    render(
      <Step1UploadPage
        datasets={[datasetFixture]}
        selectedDataset={datasetFixture}
        loading={false}
        error={null}
        onUpload={vi.fn()}
        onSelectDataset={vi.fn()}
        onTaskTypeChange={vi.fn()}
        taskType="classification"
      />
    );

    expect(screen.getByText("Selected dataset preview")).toBeInTheDocument();
    expect(screen.getByText(/Rows:/)).toBeInTheDocument();
    expect(screen.getByText(/Columns:/)).toBeInTheDocument();
    expect(screen.getByText(/Quality check:/)).toBeInTheDocument();
  });

  it("submits upload form with selected file", async () => {
    const user = userEvent.setup();
    const onUpload = vi.fn().mockResolvedValue(undefined);

    render(
      <Step1UploadPage
        datasets={[]}
        selectedDataset={null}
        loading={false}
        error={null}
        onUpload={onUpload}
        onSelectDataset={vi.fn()}
        onTaskTypeChange={vi.fn()}
        taskType="classification"
      />
    );

    await user.type(screen.getByLabelText("Dataset name"), "Risk dataset");
    await user.type(screen.getByLabelText("Description"), "Q2 run");

    const file = new File(["a,b\n1,2"], "risk.csv", { type: "text/csv" });
    const fileInput = screen.getByLabelText("Data file") as HTMLInputElement;
    await user.upload(fileInput, file);

    expect(fileInput.files).toHaveLength(1);
    expect(fileInput.files?.[0]?.name).toBe("risk.csv");

    const submitButton = screen.getByRole("button", { name: "Upload and Validate" });
    expect(submitButton).toBeEnabled();

    const form = submitButton.closest("form");
    expect(form).not.toBeNull();
    fireEvent.submit(form as HTMLFormElement);

    await waitFor(() => {
      expect(onUpload).toHaveBeenCalledWith(file, "Risk dataset", "Q2 run");
    });
  });
});
