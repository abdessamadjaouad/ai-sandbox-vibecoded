// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/store/wizardStore.ts
import { useMemo, useState } from "react";
import type { WizardDraft } from "../types";

export interface WizardStep {
  id: number;
  title: string;
  subtitle: string;
}

export const WIZARD_STEPS: WizardStep[] = [
  {
    id: 1,
    title: "Upload Data",
    subtitle: "Add one dataset and let the app detect setup.",
  },
  {
    id: 2,
    title: "Create Split",
    subtitle: "Use recommended split or open advanced settings.",
  },
  {
    id: 3,
    title: "Review Models",
    subtitle: "Models are auto-selected; deselect if needed.",
  },
  {
    id: 4,
    title: "Run Benchmark",
    subtitle: "Launch and track status in real time.",
  },
  {
    id: 5,
    title: "Dashboard & Report",
    subtitle: "Compare scores and download report files.",
  },
];

export const createDefaultDraft = (): WizardDraft => ({
  taskType: "classification",
  dataset: null,
  datasetVersion: null,
  targetColumn: "",
  selectedFeatures: [],
  selectedModels: [],
  experimentName: "",
  experimentDescription: "",
  randomSeed: 42,
  trainRatio: 0.7,
  valRatio: 0.15,
  testRatio: 0.15,
  stratifyColumn: "",
});

export const useWizardStore = () => {
  const [step, setStep] = useState(1);
  const [draft, setDraft] = useState<WizardDraft>(createDefaultDraft());

  const canGoBack = step > 1;
  const canGoForward = step < WIZARD_STEPS.length;

  const progress = useMemo(() => (step / WIZARD_STEPS.length) * 100, [step]);

  const updateDraft = (patch: Partial<WizardDraft>) => {
    setDraft((current) => ({ ...current, ...patch }));
  };

  const goToStep = (nextStep: number) => {
    if (nextStep < 1 || nextStep > WIZARD_STEPS.length) {
      return;
    }
    setStep(nextStep);
  };

  const nextStep = () => {
    setStep((current) => Math.min(current + 1, WIZARD_STEPS.length));
  };

  const previousStep = () => {
    setStep((current) => Math.max(current - 1, 1));
  };

  const resetWizard = () => {
    setStep(1);
    setDraft(createDefaultDraft());
  };

  return {
    step,
    draft,
    progress,
    canGoBack,
    canGoForward,
    goToStep,
    nextStep,
    previousStep,
    updateDraft,
    resetWizard,
  };
};
