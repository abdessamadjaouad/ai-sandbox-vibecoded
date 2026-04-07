// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step4RunPage.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Step4RunPage } from "./Step4RunPage";
import type { ModelCatalogueEntry } from "../types";

const modelFixture: ModelCatalogueEntry = {
  name: "XGBoost Classifier",
  family: "xgboost",
  class_name: "xgboost.XGBClassifier",
  task_types: ["classification"],
  default_hyperparameters: { n_estimators: 100 },
  description: "Boosting model",
};

describe("Step4RunPage", () => {
  it("submits run payload", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <Step4RunPage
        selectedModelCount={1}
        selectedModels={[modelFixture]}
        loading={false}
        runningState="idle"
        experiment={null}
        error={null}
        defaultName="Credit benchmark"
        defaultDescription=""
        randomSeed={42}
        onSubmit={onSubmit}
      />
    );

    await user.clear(screen.getByLabelText("Experiment name"));
    await user.type(screen.getByLabelText("Experiment name"), "Risk run");
    await user.type(screen.getByLabelText("Description"), "A/B model check");

    await user.click(screen.getByRole("button", { name: "Create and Run" }));

    expect(onSubmit).toHaveBeenCalledWith({
      name: "Risk run",
      description: "A/B model check",
      randomSeed: 42,
    });
  });

  it("disables submit while running", () => {
    render(
      <Step4RunPage
        selectedModelCount={1}
        selectedModels={[modelFixture]}
        loading={false}
        runningState="polling"
        experiment={null}
        error={null}
        defaultName="Credit benchmark"
        defaultDescription=""
        randomSeed={42}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByRole("button", { name: "Re-run" })).toBeDisabled();
  });
});
