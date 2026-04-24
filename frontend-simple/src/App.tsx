// /home/jao/Desktop/sandbox-project-vibecoded/frontend-simple/src/App.tsx
import { useCallback, useState } from "react";
import {
  SimpleHomePage,
  SimpleDatasetPage,
  SimpleConfigPage,
  SimpleRunPage,
  SimpleResultsPage,
} from "./pages";
import type { SimpleRunConfig, SimpleRunResult } from "./types";

type View = "home" | "dataset" | "config" | "run" | "results";

function App() {
  const [view, setView] = useState<View>("home");
  const [datasetId, setDatasetId] = useState<string>("");
  const [config, setConfig] = useState<SimpleRunConfig | null>(null);
  const [result, setResult] = useState<SimpleRunResult | null>(null);

  const handleStartBenchmark = useCallback(() => {
    setView("dataset");
  }, []);

  const handleDatasetSelect = useCallback((id: string) => {
    setDatasetId(id);
    setView("config");
  }, []);

  const handleConfigComplete = useCallback((cfg: SimpleRunConfig) => {
    setConfig(cfg);
    setView("run");
  }, []);

  const handleRunComplete = useCallback((res: SimpleRunResult) => {
    setResult(res);
    setView("results");
  }, []);

  const handleNewBenchmark = useCallback(() => {
    setView("home");
    setDatasetId("");
    setConfig(null);
    setResult(null);
  }, []);

  const handleBack = useCallback(() => {
    switch (view) {
      case "dataset":
        setView("home");
        break;
      case "config":
        setView("dataset");
        break;
      case "run":
        setView("config");
        break;
      case "results":
        setView("config");
        break;
    }
  }, [view]);

  return (
    <div className="app-shell">
      {view !== "home" && (
        <header className="simple-navbar">
          <div className="simple-navbar-content">
            <h1 className="simple-navbar-title">AI Sandbox</h1>
            <div className="simple-navbar-steps">
              <span className={`step ${view === "dataset" ? "active" : ""}`}>1. Select Dataset</span>
              <span className="step-separator">›</span>
              <span className={`step ${view === "config" ? "active" : ""}`}>2. Configure</span>
              <span className="step-separator">›</span>
              <span className={`step ${view === "run" ? "active" : ""}`}>3. Run</span>
              <span className="step-separator">›</span>
              <span className={`step ${view === "results" ? "active" : ""}`}>4. Results</span>
            </div>
          </div>
        </header>
      )}

      {view === "home" && <SimpleHomePage onStartBenchmark={handleStartBenchmark} />}
      {view === "dataset" && (
        <SimpleDatasetPage
          onNext={handleDatasetSelect}
          onBack={handleBack}
        />
      )}
      {view === "config" && datasetId && (
        <SimpleConfigPage
          datasetId={datasetId}
          onNext={handleConfigComplete}
          onBack={handleBack}
        />
      )}
      {view === "run" && config && (
        <SimpleRunPage
          config={config}
          onComplete={handleRunComplete}
          onBack={handleBack}
        />
      )}
      {view === "results" && result && (
        <SimpleResultsPage
          result={result}
          onNewBenchmark={handleNewBenchmark}
          onBack={handleBack}
        />
      )}
    </div>
  );
}

export default App;