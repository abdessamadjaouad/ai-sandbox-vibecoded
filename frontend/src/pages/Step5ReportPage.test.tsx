// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step5ReportPage.test.tsx
import { render, screen } from "@testing-library/react";

import { Step5ReportPage } from "./Step5ReportPage";

describe("Step5ReportPage", () => {
  it("renders score chart and report actions", () => {
    render(
      <Step5ReportPage
        loading={false}
        error={null}
        summary={{
          experiment_id: "exp-1",
          experiment_name: "Risk benchmark",
          status: "completed",
          total_models: 2,
          successful_models: 2,
          failed_models: 0,
          best_model_name: "Model A",
          best_model_score: 0.91,
          recommendation: "Model A is recommended",
          duration_seconds: 30,
        }}
        report={{
          experiment_id: "exp-1",
          experiment_name: "Risk benchmark",
          markdown_content: "# Report\n\n- hello",
          summary: "summary",
          recommendation: "Model A",
          best_model: "Model A",
          best_score: 0.91,
        }}
        results={[
          {
            id: "r1",
            experiment_id: "exp-1",
            model_name: "Model A",
            model_family: "sklearn",
            model_config: {},
            hyperparameters: null,
            metrics: { accuracy: 0.9 },
            global_score: 0.91,
            rank: 1,
            training_duration_seconds: 2,
            inference_latency_ms: 10,
            artefact_path: null,
            mlflow_run_id: null,
            error_message: null,
            created_at: "2026-01-01T00:00:00Z",
          },
        ]}
      />
    );

    expect(screen.getByText("Global score comparison")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download Markdown" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download PDF" })).toBeInTheDocument();
  });
});
