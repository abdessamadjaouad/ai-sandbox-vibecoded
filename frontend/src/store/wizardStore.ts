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
    subtitle: "Bring your file and run quality checks.",
  },
  {
    id: 2,
    title: "Prepare Split",
    subtitle: "Create train/validation/test sets automatically.",
  },
  {
    id: 3,
    title: "Choose Models",
    subtitle: "Pick the engines we compare for you.",
  },
  {
    id: 4,
    title: "Run Sandbox",
    subtitle: "Launch experiment and watch progress.",
  },
  {
    id: 5,
    title: "Decision Report",
    subtitle: "Read recommendation and model ranking.",
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
