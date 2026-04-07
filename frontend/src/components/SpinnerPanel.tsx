// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/components/SpinnerPanel.tsx
interface SpinnerPanelProps {
  text: string;
}

export const SpinnerPanel = ({ text }: SpinnerPanelProps) => {
  return (
    <div className="spinner-panel" role="status" aria-live="polite">
      <div className="spinner" />
      <p>{text}</p>
    </div>
  );
};
