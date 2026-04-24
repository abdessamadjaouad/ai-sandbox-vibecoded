// /home/jao/Desktop/sandbox-project-vibecoded/frontend-simple/src/pages/SimpleRunPage.tsx
import { useCallback, useEffect, useRef, useState } from "react";
import { simpleApi } from "../api/simpleClient";
import type { SimpleRunConfig, SimpleRunResult } from "../types";

interface SimpleRunPageProps {
  config: SimpleRunConfig;
  onComplete: (result: SimpleRunResult) => void;
  onBack: () => void;
}

export const SimpleRunPage = ({ config, onComplete, onBack }: SimpleRunPageProps) => {
  const [progress, setProgress] = useState<string>("Initializing...");
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(true);
  const [isStopping, setIsStopping] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    runBenchmark();
  }, []);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const addLog = useCallback((message: string) => {
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`]);
  }, []);

  const runBenchmark = async () => {
    try {
      setIsRunning(true);
      addLog("Starting benchmark...");

      await simpleApi.runBenchmarkStream(config, (data) => {
        if (data.event === "training_progress") {
          setProgress(`Training: ${data.message}`);
          addLog(`Training model: ${data.message}`);
        } else if (data.event === "post_processing") {
          setProgress(data.step || "Processing...");
          addLog(data.step || "Processing...");
        } else if (data.event === "result") {
          addLog("Benchmark complete!");
          setProgress("Complete");
          onComplete(data.data as SimpleRunResult);
        } else if (data.event === "error") {
          throw new Error(data.message || "Benchmark failed");
        } else if (data.event === "training_stopped") {
          addLog("Training stopped by user");
          setIsRunning(false);
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark failed");
      setIsRunning(false);
    }
  };

  const handleStop = useCallback(async () => {
    try {
      setIsStopping(true);
      addLog("Requesting stop...");
      await simpleApi.stopRun();
    } catch (err) {
      addLog("Failed to request stop");
    } finally {
      setIsStopping(false);
    }
  }, [addLog]);

  const getStepProgress = () => {
    if (progress.includes("Training:")) return 30;
    if (progress.includes("Scoring")) return 60;
    if (progress.includes("Report")) return 80;
    if (progress === "Complete") return 100;
    return 10;
  };

  return (
    <main className="wizard-shell">
      <header className="wizard-header">
        <h1>Running Benchmark</h1>
        <p>Your models are being trained and evaluated</p>
      </header>

      <div className="wizard-content">
        <section className="run-section glass-card">
          <div className="progress-header">
            <div className="progress-status">
              {error ? (
                <span className="status-error">Error</span>
              ) : isRunning ? (
                <span className="status-running">Running</span>
              ) : (
                <span className="status-stopped">Stopped</span>
              )}
            </div>
            <span className="progress-message">{progress}</span>
          </div>

          <div className="progress-bar-container">
            <div
              className="progress-bar"
              style={{ width: `${getStepProgress()}%` }}
            ></div>
          </div>

          {isRunning && !error && (
            <button
              className="btn btn-ghost stop-btn"
              onClick={handleStop}
              disabled={isStopping}
            >
              {isStopping ? "Stopping..." : "Stop"}
            </button>
          )}
        </section>

        <section className="logs-section glass-card">
          <h2>Logs</h2>
          <div className="logs-container">
            {logs.map((log, i) => (
              <div key={i} className="log-line">
                {log}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </section>

        {error && (
          <div className="error-banner">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        )}
      </div>

      <footer className="wizard-footer">
        <button className="btn btn-ghost" onClick={onBack} disabled={isRunning}>
          Back
        </button>
        {error && (
          <button
            className="btn btn-brand"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        )}
      </footer>
    </main>
  );
};