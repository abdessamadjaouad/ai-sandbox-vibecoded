// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/components/ActionBar.tsx
interface ActionBarProps {
  canGoBack: boolean;
  canGoForward: boolean;
  backLabel?: string;
  nextLabel?: string;
  onBack: () => void;
  onNext: () => void;
  disabled?: boolean;
}

export const ActionBar = ({
  canGoBack,
  canGoForward,
  backLabel = "Back",
  nextLabel = "Continue",
  onBack,
  onNext,
  disabled = false,
}: ActionBarProps) => {
  return (
    <footer className="action-bar">
      <button type="button" className="btn btn-ghost" disabled={!canGoBack || disabled} onClick={onBack}>
        {backLabel}
      </button>

      <button type="button" className="btn btn-primary" disabled={!canGoForward || disabled} onClick={onNext}>
        {nextLabel}
      </button>
    </footer>
  );
};
