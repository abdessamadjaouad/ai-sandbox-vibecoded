// /home/jao/Desktop/sandbox-project-vibecoded/frontend-simple/src/pages/SimpleHomePage.tsx
// Note: Logo should be copied or referenced from parent

interface SimpleHomePageProps {
  onStartBenchmark: () => void;
}

export const SimpleHomePage = ({ onStartBenchmark }: SimpleHomePageProps) => {
  return (
    <main className="landing-shell">
      <div className="landing-hero">
        <div className="hero-content">
          <h1 className="hero-title">AI Sandbox</h1>
          <p className="hero-subtitle">Enterprise-grade AI benchmarking platform</p>
          <p className="hero-description">
            Compare machine learning models, evaluate performance, and generate detailed reports.
            Supports classification and regression tasks with automatic model selection.
          </p>
          <button className="btn btn-brand btn-large" onClick={onStartBenchmark}>
            Start Benchmark
          </button>
        </div>
        
        <div className="hero-features">
          <div className="feature-card">
            <div className="feature-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
            </div>
            <h3>Multiple Models</h3>
            <p>Compare Logistic Regression, Random Forest, XGBoost, LightGBM, and more</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 20V10" />
                <path d="M18 20V4" />
                <path d="M6 20v-4" />
              </svg>
            </div>
            <h3>Weighted Scoring</h3>
            <p>Balance performance, robustness, latency, and model size</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <h3>Detailed Reports</h3>
            <p>Export comprehensive markdown reports with visualizations</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
            </div>
            <h3>Real-time Progress</h3>
            <p>Watch training progress with streaming updates</p>
          </div>
        </div>
      </div>
      
      <div className="landing-stats">
        <div className="stat">
          <span className="stat-value">6+</span>
          <span className="stat-label">Models</span>
        </div>
        <div className="stat">
          <span className="stat-value">2</span>
          <span className="stat-label">Task Types</span>
        </div>
        <div className="stat">
          <span className="stat-value">CSV/Excel</span>
          <span className="stat-label">Formats</span>
        </div>
        <div className="stat">
          <span className="stat-value">MLflow</span>
          <span className="stat-label">Tracking</span>
        </div>
      </div>
      
      <div className="landing-footer">
        <p>Powered by DXC Technology · ML Benchmarking Platform</p>
      </div>
    </main>
  );
};