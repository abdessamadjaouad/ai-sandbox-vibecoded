// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/Step3ModelPage.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Step3ModelPage } from "./Step3ModelPage";
import type { ModelCatalogueEntry } from "../types";

const modelFixture: ModelCatalogueEntry = {
  name: "Random Forest Classifier",
  family: "sklearn",
  class_name: "sklearn.ensemble.RandomForestClassifier",
  task_types: ["classification"],
  default_hyperparameters: { n_estimators: 100 },
  description: "Tree ensemble",
};

describe("Step3ModelPage", () => {
  it("calls target change callback when selecting target column", async () => {
    const user = userEvent.setup();
    const onTargetColumnChange = vi.fn();

    render(
      <Step3ModelPage
        columns={["age", "income", "target"]}
        taskType="classification"
        autoConfigConfidence="high"
        autoConfigRationale="Detected target column automatically."
        targetColumn=""
        selectedFeatures={[]}
        models={[modelFixture]}
        selectedModels={[]}
        loading={false}
        error={null}
        onTargetColumnChange={onTargetColumnChange}
        onToggleFeature={vi.fn()}
        onToggleModel={vi.fn()}
      />
    );

    await user.selectOptions(screen.getByLabelText("Target column"), "target");

    expect(onTargetColumnChange).toHaveBeenCalledWith("target");
  });

  it("calls model toggle callback", async () => {
    const user = userEvent.setup();
    const onToggleModel = vi.fn();

    render(
      <Step3ModelPage
        columns={["age", "income", "target"]}
        taskType="classification"
        autoConfigConfidence="high"
        autoConfigRationale="Detected target column automatically."
        targetColumn="target"
        selectedFeatures={["age", "income"]}
        models={[modelFixture]}
        selectedModels={[]}
        loading={false}
        error={null}
        onTargetColumnChange={vi.fn()}
        onToggleFeature={vi.fn()}
        onToggleModel={onToggleModel}
      />
    );

    await user.click(screen.getByRole("checkbox", { name: "Toggle Random Forest Classifier" }));

    expect(onToggleModel).toHaveBeenCalledWith(modelFixture);
  });
});
