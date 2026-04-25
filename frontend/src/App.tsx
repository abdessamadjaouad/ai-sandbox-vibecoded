// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/App.tsx
import { useCallback, useEffect, useState } from "react";

import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { useApi } from "./hooks/useApi";
import { AboutPage } from "./pages/AboutPage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { Step1UploadPage } from "./pages/Step1UploadPage";
import { Step2VersionPage } from "./pages/Step2VersionPage";
import { Step3ModelPage } from "./pages/Step3ModelPage";
import { Step4RunPage } from "./pages/Step4RunPage";
import { Step5ReportPage } from "./pages/Step5ReportPage";
import { HistoryPage } from "./pages/HistoryPage";
import { AgentEvaluationPage } from "./pages/AgentEvaluationPage";
import { AgentEvaluationTesterPage } from "./pages/AgentEvaluationTesterPage";
import { useWizardStore, WIZARD_STEPS } from "./store/wizardStore";
import type {
  DatasetAutoConfigRead,
  DatasetRead,
  DatasetVersionRead,
  EvaluationReportResponse,
  ExperimentRead,
  ExperimentResultRead,
  ExperimentSummary,
  ModelCatalogueEntry,
} from "./types";

import dxcLogo from "../dxc-logo.png";

type AppView = "landing" | "wizard" | "login" | "signup" | "about" | "history" | "agent-evaluation" | "agent-tester";
type Theme = "light" | "dark";
type RunningState = "idle" | "creating" | "running" | "polling" | "completed" | "failed";

const AppContent = () => {
  // Navigation and theming
  const [view, setView] = useState<AppView>("signup");
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("ai-sandbox-theme");
      if (stored === "dark" || stored === "light") {
        return stored;
      }
    }
    return "light";
  });

  // Auth
  const { isAuthenticated, token, getAuthHeaders } = useAuth();

  // Wizard state
  const wizard = useWizardStore();

  // API hook with auth
  const api = useApi(getAuthHeaders);

  // Data state
  const [datasets, setDatasets] = useState<DatasetRead[]>([]);
  const [versions, setVersions] = useState<DatasetVersionRead[]>([]);
  const [models, setModels] = useState<ModelCatalogueEntry[]>([]);
  const [autoConfig, setAutoConfig] = useState<DatasetAutoConfigRead | null>(null);

  // Experiment state
  const [experiment, setExperiment] = useState<ExperimentRead | null>(null);
  const [summary, setSummary] = useState<ExperimentSummary | null>(null);
  const [results, setResults] = useState<ExperimentResultRead[]>([]);
  const [report, setReport] = useState<EvaluationReportResponse | null>(null);
  const [runState, setRunState] = useState<RunningState>("idle");
  const [progressMessage, setProgressMessage] = useState("");

  // URLs
  const apiBaseUrl = api.apiBaseUrl.replace("/api/v1", "");
  const apiDocsUrl = `${apiBaseUrl}/docs`;
  const mlflowUrl = `${apiBaseUrl.replace(":8000", ":5000")}`;

  // Theme effect
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("ai-sandbox-theme", theme);
  }, [theme]);

  // Toggle theme handler
  const toggleTheme = useCallback(() => {
    setTheme((current) => (current === "light" ? "dark" : "light"));
  }, []);

  // Navigation handler
  const handleNavigate = useCallback((newView: AppView) => {
    setView(newView);
  }, []);

  // Agent evaluation example generator
  const getAgentExample = useCallback((): string => {
    const example = [
      {
        run_id: "run_001",
        agent_id: "market_agent",
        agent_version: "1.0.0",
        status: "SUCCESS",
        output: { summary: "Market trends show 12% growth" },
        latency_ms: 450,
        started_at: "2026-04-24T10:00:00Z",
        completed_at: "2026-04-24T10:00:00.450Z",
        metrics: {
          technical: { cpu_time_ms: 180, memory_mb: 128, network_calls_count: 2, retry_count: 0 },
          ai: { prompt_tokens: 120, completion_tokens: 80, estimated_cost_usd: 0.0042, model_name: "gpt-4o-mini" },
        },
        steps: [
          { step_name: "validate_input", status: "SUCCESS", started_at: "2026-04-24T10:00:00Z", completed_at: "2026-04-24T10:00:00.050Z", latency_ms: 50 },
          { step_name: "generate_analysis", status: "SUCCESS", started_at: "2026-04-24T10:00:00.050Z", completed_at: "2026-04-24T10:00:00.400Z", latency_ms: 350, tool_used: "mock_llm" },
        ],
        tools: [
          { tool_name: "mock_llm", status: "SUCCESS", started_at: "2026-04-24T10:00:00.050Z", completed_at: "2026-04-24T10:00:00.400Z", latency_ms: 350 },
        ],
        error: null,
        metadata: {},
      },
      {
        run_id: "run_002",
        agent_id: "market_agent",
        agent_version: "1.0.0",
        status: "SUCCESS",
        output: { summary: "Sector analysis completed" },
        latency_ms: 1200,
        started_at: "2026-04-24T10:01:00Z",
        completed_at: "2026-04-24T10:01:01.200Z",
        metrics: {
          technical: { cpu_time_ms: 520, memory_mb: 256, network_calls_count: 3, retry_count: 1 },
          ai: { prompt_tokens: 280, completion_tokens: 150, estimated_cost_usd: 0.0095, model_name: "gpt-4" },
        },
        steps: [
          { step_name: "validate_input", status: "SUCCESS", started_at: "2026-04-24T10:01:00Z", completed_at: "2026-04-24T10:01:00.080Z", latency_ms: 80 },
          { step_name: "generate_analysis", status: "SUCCESS", started_at: "2026-04-24T10:01:00.080Z", completed_at: "2026-04-24T10:01:01.100Z", latency_ms: 1020, tool_used: "mock_llm" },
        ],
        tools: [
          { tool_name: "mock_llm", status: "SUCCESS", started_at: "2026-04-24T10:01:00.080Z", completed_at: "2026-04-24T10:01:01.100Z", latency_ms: 1020 },
        ],
        error: null,
        metadata: {},
      },
      {
        run_id: "run_003",
        agent_id: "market_agent",
        agent_version: "1.0.0",
        status: "FAILED",
        output: null,
        latency_ms: 30000,
        started_at: "2026-04-24T10:02:00Z",
        completed_at: "2026-04-24T10:02:30Z",
        metrics: {
          technical: { cpu_time_ms: 150, memory_mb: 64, network_calls_count: 0, retry_count: 0 },
          ai: { prompt_tokens: 100, completion_tokens: 0, estimated_cost_usd: 0.002, model_name: "gpt-4o-mini" },
        },
        steps: [
          { step_name: "validate_input", status: "SUCCESS", started_at: "2026-04-24T10:02:00Z", completed_at: "2026-04-24T10:02:00.060Z", latency_ms: 60 },
          { step_name: "generate_analysis", status: "FAILED", started_at: "2026-04-24T10:02:00.060Z", completed_at: "2026-04-24T10:02:30Z", latency_ms: 29940, tool_used: "mock_llm" },
        ],
        tools: [
          { tool_name: "mock_llm", status: "FAILED", started_at: "2026-04-24T10:02:00.060Z", completed_at: "2026-04-24T10:02:30Z", latency_ms: 29940, error_message: "Request timeout" },
        ],
        error: { type: "TIMEOUT", message: "Agent exceeded configured timeout", step: "generate_analysis", recoverable: true },
        metadata: {},
      },
    ];
    return JSON.stringify(example, null, 2);
  }, []);

  // Start wizard - requires authentication
  const startWizard = useCallback(() => {
    if (!isAuthenticated || !token) {
      setView("login");
      return;
    }
    setView("wizard");
    wizard.resetWizard();
    setAutoConfig(null);
    setExperiment(null);
    setSummary(null);
    setResults([]);
    setReport(null);
    setRunState("idle");
    setProgressMessage("");
  }, [wizard, isAuthenticated, token]);

  // Load datasets on mount
  useEffect(() => {
    const load = async () => {
      try {
        const list = await api.listDatasets();
        setDatasets(list);
      } catch {
        // Ignore errors on initial load
      }
    };
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load dataset versions when dataset changes
  useEffect(() => {
    if (!wizard.draft.dataset) {
      setVersions([]);
      return;
    }
    const load = async () => {
      try {
        const list = await api.listDatasetVersions(wizard.draft.dataset!.id);
        setVersions(list);
      } catch {
        // Ignore
      }
    };
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wizard.draft.dataset?.id]);

  // Load models when task type changes
  useEffect(() => {
    const load = async () => {
      try {
        const list = await api.listModels(wizard.draft.taskType);
        setModels(list);
        // Auto-select all models
        wizard.updateDraft({ selectedModels: list });
      } catch {
        // Ignore
      }
    };
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wizard.draft.taskType]);

  // Upload dataset handler
  const handleUpload = useCallback(
    async (file: File, name: string, description: string) => {
      const newDataset = await api.uploadDataset(file, name, description);
      setDatasets((prev) => [newDataset, ...prev]);

      // Auto-select the uploaded dataset
      wizard.updateDraft({ dataset: newDataset });

      // Fetch auto-config
      try {
        const config = await api.getDatasetAutoConfig(newDataset.id);
        setAutoConfig(config);
        applyAutoConfig(config);
      } catch {
        // Ignore auto-config errors
      }
    },
    [api, wizard]
  );

  // Select dataset handler
  const handleSelectDataset = useCallback(
    async (dataset: DatasetRead) => {
      wizard.updateDraft({ dataset });

      // Fetch auto-config for selected dataset
      try {
        const config = await api.getDatasetAutoConfig(dataset.id);
        setAutoConfig(config);
        applyAutoConfig(config);
      } catch {
        setAutoConfig(null);
      }
    },
    [api, wizard]
  );

  // Apply auto-config to wizard draft
  const applyAutoConfig = useCallback(
    (config: DatasetAutoConfigRead) => {
      wizard.updateDraft({
        taskType: config.task_type,
        targetColumn: config.target_column ?? "",
        selectedFeatures: config.feature_columns,
        stratifyColumn: config.stratify_column ?? "",
        experimentName: config.suggested_name ? `Benchmark: ${config.suggested_name}` : "",
      });
    },
    [wizard]
  );

  // Create dataset version handler
  const handleCreateVersion = useCallback(
    async (payload: {
      train_ratio: number;
      val_ratio: number;
      test_ratio: number;
      random_seed: number;
      stratify_column?: string;
    }) => {
      if (!wizard.draft.dataset) {
        return;
      }
      const newVersion = await api.createDatasetVersion(wizard.draft.dataset.id, payload);
      setVersions((prev) => [...prev, newVersion]);
      wizard.updateDraft({ datasetVersion: newVersion });
    },
    [api, wizard]
  );

  // Select version handler
  const handleSelectVersion = useCallback(
    (version: DatasetVersionRead) => {
      wizard.updateDraft({ datasetVersion: version });
    },
    [wizard]
  );

  // Toggle feature handler
  const handleToggleFeature = useCallback(
    (column: string) => {
      const current = wizard.draft.selectedFeatures;
      const next = current.includes(column)
        ? current.filter((c) => c !== column)
        : [...current, column];
      wizard.updateDraft({ selectedFeatures: next });
    },
    [wizard]
  );

  // Toggle model handler
  const handleToggleModel = useCallback(
    (model: ModelCatalogueEntry) => {
      const current = wizard.draft.selectedModels;
      const exists = current.some((m) => m.name === model.name);
      const next = exists
        ? current.filter((m) => m.name !== model.name)
        : [...current, model];
      wizard.updateDraft({ selectedModels: next });
    },
    [wizard]
  );

  // Advanced settings change handler
  const handleAdvancedChange = useCallback(
    (patch: {
      trainRatio?: number;
      valRatio?: number;
      testRatio?: number;
      randomSeed?: number;
      stratifyColumn?: string;
    }) => {
      wizard.updateDraft(patch);
    },
    [wizard]
  );

  // Run experiment handler
  const handleRunExperiment = useCallback(
    async (payload: { name: string; description: string; randomSeed: number }) => {
      if (!wizard.draft.dataset || !wizard.draft.datasetVersion) {
        return;
      }

      // Reset state for new run
      setExperiment(null);
      setSummary(null);
      setResults([]);
      setReport(null);
      setRunState("creating");
      setProgressMessage("Creating experiment...");

      try {
        // Create experiment
        const expPayload = {
          name: payload.name,
          description: payload.description || null,
          experiment_type: "tabular_ml" as const,
          task_type: wizard.draft.taskType,
          dataset_id: wizard.draft.dataset.id,
          dataset_version_id: wizard.draft.datasetVersion.id,
          target_column: wizard.draft.targetColumn,
          feature_columns: wizard.draft.selectedFeatures,
          models: wizard.draft.selectedModels.map((m) => ({
            name: m.name,
            family: m.family,
            class_name: m.class_name,
            hyperparameters: m.default_hyperparameters,
            enabled: true,
          })),
          random_seed: payload.randomSeed,
        };

        const createdExperiment = await api.createExperiment(expPayload);
        setExperiment(createdExperiment);

        // Run experiment
        setRunState("running");
        setProgressMessage("Training models. This may take a few minutes...");

        const ranExperiment = await api.runExperiment(createdExperiment.id);
        setExperiment(ranExperiment);

        // Poll for completion
        setRunState("polling");
        setProgressMessage("Waiting for benchmark to complete...");

        let finalExperiment = ranExperiment;
        let pollAttempts = 0;
        const maxPolls = 120; // 2 minutes max

        while (
          finalExperiment.status !== "completed" &&
          finalExperiment.status !== "failed" &&
          pollAttempts < maxPolls
        ) {
          await new Promise((resolve) => setTimeout(resolve, 1000));
          finalExperiment = await api.getExperiment(createdExperiment.id);
          setExperiment(finalExperiment);
          setProgressMessage(`Status: ${finalExperiment.status}...`);
          pollAttempts++;
        }

        if (finalExperiment.status === "completed") {
          setRunState("completed");
          setProgressMessage("Benchmark completed!");

          // Fetch results and summary
          const [expSummary, expResults] = await Promise.all([
            api.getExperimentSummary(createdExperiment.id),
            api.getExperimentResults(createdExperiment.id),
          ]);
          setSummary(expSummary);
          setResults(expResults);

          // Generate report
          try {
            const expReport = await api.generateReport(createdExperiment.id);
            setReport(expReport);
          } catch {
            // Report generation is optional
          }

          // Auto-advance to report step
          wizard.goToStep(5);
        } else {
          setRunState("failed");
          setProgressMessage(finalExperiment.error_message ?? "Experiment failed.");
        }
      } catch (err) {
        setRunState("failed");
        setProgressMessage(err instanceof Error ? err.message : "An error occurred.");
      }
    },
    [api, wizard]
  );

  // Retry handler
  const handleRetry = useCallback(async () => {
    if (!experiment) {
      return;
    }
    setRunState("running");
    setProgressMessage("Retrying experiment...");

    try {
      const ranExperiment = await api.runExperiment(experiment.id);
      setExperiment(ranExperiment);

      // Poll again
      setRunState("polling");
      let finalExperiment = ranExperiment;
      let pollAttempts = 0;

      while (
        finalExperiment.status !== "completed" &&
        finalExperiment.status !== "failed" &&
        pollAttempts < 120
      ) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        finalExperiment = await api.getExperiment(experiment.id);
        setExperiment(finalExperiment);
        setProgressMessage(`Status: ${finalExperiment.status}...`);
        pollAttempts++;
      }

      if (finalExperiment.status === "completed") {
        setRunState("completed");

        const [expSummary, expResults] = await Promise.all([
          api.getExperimentSummary(experiment.id),
          api.getExperimentResults(experiment.id),
        ]);
        setSummary(expSummary);
        setResults(expResults);

        try {
          const expReport = await api.generateReport(experiment.id);
          setReport(expReport);
        } catch {
          // Ignore
        }

        wizard.goToStep(5);
      } else {
        setRunState("failed");
        setProgressMessage(finalExperiment.error_message ?? "Retry failed.");
      }
    } catch (err) {
      setRunState("failed");
      setProgressMessage(err instanceof Error ? err.message : "Retry failed.");
    }
  }, [api, experiment, wizard]);

  // Get columns from dataset
  const columns = wizard.draft.dataset?.schema_info?.columns ?? [];

  // Render login page
  if (view === "login") {
    return (
      <div className="app-shell">
        <Navbar
          logoSrc={dxcLogo}
          theme={theme}
          onToggleTheme={toggleTheme}
          onNavigate={handleNavigate}
          currentView={view}
          apiDocsUrl={apiDocsUrl}
          mlflowUrl={mlflowUrl}
        />
        <LoginPage
          onNavigate={handleNavigate}
          onSuccess={() => handleNavigate("landing")}
        />
        <Footer onNavigate={handleNavigate} />
      </div>
    );
  }

  // Render signup page
  if (view === "signup") {
    return (
      <div className="app-shell">
        <Navbar
          logoSrc={dxcLogo}
          theme={theme}
          onToggleTheme={toggleTheme}
          onNavigate={handleNavigate}
          currentView={view}
          apiDocsUrl={apiDocsUrl}
          mlflowUrl={mlflowUrl}
        />
        <SignupPage
          onNavigate={handleNavigate}
          onSuccess={() => handleNavigate("landing")}
        />
        <Footer onNavigate={handleNavigate} />
      </div>
    );
  }

  // Render about page
  if (view === "about") {
    return (
      <div className="app-shell">
        <Navbar
          logoSrc={dxcLogo}
          theme={theme}
          onToggleTheme={toggleTheme}
          onNavigate={handleNavigate}
          currentView={view}
          apiDocsUrl={apiDocsUrl}
          mlflowUrl={mlflowUrl}
        />
        <AboutPage logoSrc={dxcLogo} />
        <Footer onNavigate={handleNavigate} />
      </div>
    );
  }

  // Render landing page
  if (view === "landing") {
    return (
      <div className="app-shell">
        <Navbar
          logoSrc={dxcLogo}
          theme={theme}
          onToggleTheme={toggleTheme}
          onNavigate={handleNavigate}
          currentView={view}
          apiDocsUrl={apiDocsUrl}
          mlflowUrl={mlflowUrl}
        />
        <LandingPage
          logoSrc={dxcLogo}
          onStartWizard={startWizard}
          onToggleTheme={toggleTheme}
          theme={theme}
          apiDocsUrl={apiDocsUrl}
          datasetsCount={datasets.length}
        />
        <Footer onNavigate={handleNavigate} />
      </div>
    );
  }

  // Render history page
  if (view === "history") {
    return (
      <div className="app-shell">
        <Navbar
          logoSrc={dxcLogo}
          theme={theme}
          onToggleTheme={toggleTheme}
          onNavigate={handleNavigate}
          currentView={view}
          apiDocsUrl={apiDocsUrl}
          mlflowUrl={mlflowUrl}
        />
        <HistoryPage
          onNavigate={handleNavigate}
          onViewReport={(experimentId) => {
            // Load the experiment and go to report step
            api.getExperiment(experimentId).then((exp) => {
              setExperiment(exp);
              api.getExperimentSummary(exp.id).then(setSummary);
              api.getExperimentResults(exp.id).then(setResults);
              api.generateReport(exp.id).then(setReport).catch(() => {});
              wizard.goToStep(5);
              setView("wizard");
            }).catch(() => {});
          }}
        />
        <Footer onNavigate={handleNavigate} />
      </div>
    );
  }

  // Render agent evaluation page
  if (view === "agent-evaluation") {
    return (
      <div className="app-shell">
        <Navbar
          logoSrc={dxcLogo}
          theme={theme}
          onToggleTheme={toggleTheme}
          onNavigate={handleNavigate}
          currentView={view}
          apiDocsUrl={apiDocsUrl}
          mlflowUrl={mlflowUrl}
        />
        <AgentEvaluationPage
          onEvaluate={async (jsonInput) => {
            const parsed = JSON.parse(jsonInput);
            const responses = Array.isArray(parsed) ? parsed : [parsed];
            return await api.evaluateAgentBatch(responses);
          }}
          onLoadExample={getAgentExample}
          loading={api.loading}
          error={api.error}
        />
        <Footer onNavigate={handleNavigate} />
      </div>
    );
  }

  // Render agent evaluation tester (demo page)
  if (view === "agent-tester") {
    return (
      <div className="app-shell">
        <Navbar
          logoSrc={dxcLogo}
          theme={theme}
          onToggleTheme={toggleTheme}
          onNavigate={handleNavigate}
          currentView={view}
          apiDocsUrl={apiDocsUrl}
          mlflowUrl={mlflowUrl}
        />
        <AgentEvaluationTesterPage apiBaseUrl={apiBaseUrl} />
        <Footer onNavigate={handleNavigate} />
      </div>
    );
  }

  // Render wizard
  return (
    <div className="app-shell">
      <Navbar
        logoSrc={dxcLogo}
        theme={theme}
        onToggleTheme={toggleTheme}
        onNavigate={handleNavigate}
        currentView={view}
        apiDocsUrl={apiDocsUrl}
        mlflowUrl={mlflowUrl}
      />
      <main className="wizard-shell">
        <header className="wizard-header glass-card">
          <div className="brand-inline" onClick={() => handleNavigate("landing")} role="button" tabIndex={0}>
            <img src={dxcLogo} alt="DXC logo" className="brand-inline__logo" />
            <div>
              <p className="eyebrow">AI Sandbox</p>
              <strong>Benchmark Wizard</strong>
            </div>
          </div>

          <nav className="wizard-steps" aria-label="Wizard progress">
            {WIZARD_STEPS.map((stepDef) => {
              const isActive = wizard.step === stepDef.id;
              const isCompleted = wizard.step > stepDef.id;
              return (
                <button
                  type="button"
                  key={stepDef.id}
                  className={`wizard-step ${isActive ? "is-active" : ""} ${isCompleted ? "is-completed" : ""}`}
                  onClick={() => wizard.goToStep(stepDef.id)}
                  disabled={stepDef.id > wizard.step + 1}
                >
                  <span className="wizard-step__num">{stepDef.id}</span>
                  <span className="wizard-step__label">{stepDef.title}</span>
                </button>
              );
            })}
          </nav>

          <div className="wizard-header__actions">
            <button type="button" className="btn btn-ghost" onClick={() => handleNavigate("landing")}>
              Exit
            </button>
          </div>
        </header>

        <div className="wizard-body">
          {wizard.step === 1 && (
            <Step1UploadPage
              datasets={datasets}
              selectedDataset={wizard.draft.dataset}
              loading={api.loading}
              error={api.error}
              autoTaskType={autoConfig?.task_type ?? null}
              onUpload={handleUpload}
              onSelectDataset={handleSelectDataset}
            />
          )}

          {wizard.step === 2 && (
            <Step2VersionPage
              dataset={wizard.draft.dataset}
              versions={versions}
              selectedVersion={wizard.draft.datasetVersion}
              columns={columns}
              taskType={wizard.draft.taskType as "classification" | "regression"}
              loading={api.loading}
              error={api.error}
              trainRatio={wizard.draft.trainRatio}
              valRatio={wizard.draft.valRatio}
              testRatio={wizard.draft.testRatio}
              randomSeed={wizard.draft.randomSeed}
              stratifyColumn={wizard.draft.stratifyColumn}
              onAdvancedChange={handleAdvancedChange}
              onCreateVersion={handleCreateVersion}
              onSelectVersion={handleSelectVersion}
            />
          )}

          {wizard.step === 3 && (
            <Step3ModelPage
              columns={columns}
              taskType={wizard.draft.taskType as "classification" | "regression"}
              autoConfigConfidence={autoConfig?.confidence ?? null}
              autoConfigRationale={autoConfig?.rationale ?? null}
              targetColumn={wizard.draft.targetColumn}
              selectedFeatures={wizard.draft.selectedFeatures}
              models={models}
              selectedModels={wizard.draft.selectedModels}
              loading={api.loading}
              error={api.error}
              onTargetColumnChange={(value) => wizard.updateDraft({ targetColumn: value })}
              onToggleFeature={handleToggleFeature}
              onToggleModel={handleToggleModel}
            />
          )}

          {wizard.step === 4 && (
            <Step4RunPage
              selectedModelCount={wizard.draft.selectedModels.length}
              selectedModels={wizard.draft.selectedModels}
              loading={api.loading}
              runningState={runState}
              experiment={experiment}
              error={runState === "failed" ? progressMessage : api.error}
              defaultName={wizard.draft.experimentName}
              defaultDescription={wizard.draft.experimentDescription}
              randomSeed={wizard.draft.randomSeed}
              progressMessage={progressMessage}
              onRetry={handleRetry}
              onSubmit={handleRunExperiment}
            />
          )}

          {wizard.step === 5 && (
            <Step5ReportPage
              summary={summary}
              report={report}
              results={results}
              loading={api.loading}
              error={api.error}
              taskType={wizard.draft.taskType as "classification" | "regression"}
            />
          )}
        </div>

        <footer className="wizard-footer glass-card">
          <button
            type="button"
            className="btn btn-ghost"
            disabled={!wizard.canGoBack}
            onClick={wizard.previousStep}
          >
            Back
          </button>

          <div className="wizard-progress">
            <div className="wizard-progress__bar" style={{ width: `${wizard.progress}%` }} />
          </div>

          <button
            type="button"
            className="btn btn-primary"
            disabled={!wizard.canGoForward || (wizard.step === 4 && runState !== "completed")}
            onClick={wizard.nextStep}
          >
            {wizard.step === WIZARD_STEPS.length ? "Finish" : "Continue"}
          </button>
        </footer>
      </main>
      <Footer onNavigate={handleNavigate} />
    </div>
  );
};

export const App = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};
