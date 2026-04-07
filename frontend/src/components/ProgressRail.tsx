// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/components/ProgressRail.tsx
import { WIZARD_STEPS } from "../store/wizardStore";

interface ProgressRailProps {
  currentStep: number;
  progress: number;
  onStepClick: (step: number) => void;
}

export const ProgressRail = ({ currentStep, progress, onStepClick }: ProgressRailProps) => {
  return (
    <aside className="progress-rail" aria-label="Wizard progress">
      <div className="progress-rail__header">
        <p className="eyebrow">Sandbox Journey</p>
        <h1>AI Sandbox Wizard</h1>
        <p>Step-by-step guidance for non-technical teams.</p>
      </div>

      <div className="progress-meter" aria-hidden>
        <div className="progress-meter__value" style={{ width: `${progress}%` }} />
      </div>

      <ol className="step-list">
        {WIZARD_STEPS.map((step) => {
          const isActive = step.id === currentStep;
          const isCompleted = step.id < currentStep;

          return (
            <li key={step.id}>
              <button
                type="button"
                className={`step-pill ${isActive ? "is-active" : ""} ${isCompleted ? "is-complete" : ""}`}
                onClick={() => onStepClick(step.id)}
              >
                <span className="step-pill__index">{step.id}</span>
                <span>
                  <strong>{step.title}</strong>
                  <small>{step.subtitle}</small>
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </aside>
  );
};
