// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/LandingPage.tsx

interface LandingPageProps {
  logoSrc: string;
  onStartWizard: () => void;
  onToggleTheme: () => void;
  theme: "light" | "dark";
  apiDocsUrl: string;
  datasetsCount: number;
}

export const LandingPage = ({
  logoSrc: _logoSrc,
  onStartWizard,
  onToggleTheme: _onToggleTheme,
  theme: _theme,
  apiDocsUrl: _apiDocsUrl,
  datasetsCount,
}: LandingPageProps) => {
  // Props prefixed with _ are passed for future use (navbar handles these now)
  void _logoSrc;
  void _onToggleTheme;
  void _theme;
  void _apiDocsUrl;
  return (
    <main className="landing-shell">
      {/* Hero Section */}
      <section className="hero glass-card">
        <p className="eyebrow">Enterprise AI Benchmark Studio</p>
        <h1>
          Benchmark AI models in minutes,{" "}
          <span className="text-gradient">with governance built in.</span>
        </h1>
        <p>
          AI Sandbox helps teams compare ML, NLP, LLM, RAG, and agentic systems before production deployment. 
          Built for regulated environments like banking, insurance, and public sector. 
          Designed for non-technical users through a guided step-by-step workflow.
        </p>
        <div className="hero__actions">
          <button type="button" className="btn btn-brand btn-lg" onClick={onStartWizard}>
            Start Benchmark Wizard
          </button>
          <a
            className="btn btn-ghost btn-lg"
            href="https://dxc.com"
            target="_blank"
            rel="noreferrer"
          >
            Learn About DXC
          </a>
        </div>
        <p className="hero__meta">
          <strong>{datasetsCount}</strong> dataset{datasetsCount === 1 ? "" : "s"} ready for benchmarking
          {datasetsCount === 0 && " — upload your first dataset to get started"}
        </p>
      </section>

      {/* Feature Cards */}
      <section className="landing-grid">
        <article className="glass-card feature-card">
          <h3>What AI Sandbox Provides</h3>
          <ul>
            <li>Automatic dataset validation, split versioning, and reproducible experiment runs</li>
            <li>Model catalogue with ranked benchmarks and configurable weighted scoring</li>
            <li>Real-time progress tracking, transparent error handling, and one-click retry</li>
            <li>Executive-ready reports in Markdown and PDF export formats</li>
          </ul>
        </article>

        <article className="glass-card feature-card">
          <h3>Built for Regulated Industries</h3>
          <ul>
            <li>Banking and finance teams validating credit scoring and fraud detection models</li>
            <li>Insurance teams with strict compliance and auditability requirements</li>
            <li>Public sector organizations needing transparent AI governance</li>
            <li>Business users who need clear recommendations without technical jargon</li>
          </ul>
        </article>

        <article className="glass-card feature-card">
          <h3>Comprehensive Evaluation</h3>
          <ul>
            <li>Tabular ML: accuracy, precision, recall, F1, latency, and cost metrics</li>
            <li>NLP and LLM: quality scores, hallucination detection, semantic similarity</li>
            <li>RAG pipelines: faithfulness, context adherence, retrieval quality</li>
            <li>Agent evaluation: task success, tool usage accuracy, step efficiency</li>
          </ul>
        </article>
      </section>
    </main>
  );
};
