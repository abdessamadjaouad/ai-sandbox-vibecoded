// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/AboutPage.tsx

interface AboutPageProps {
  logoSrc: string;
}

export const AboutPage = ({ logoSrc }: AboutPageProps) => {
  return (
    <main className="about-shell">
      <section className="about-hero">
        <div className="about-hero__content">
          <p className="eyebrow">About DXC Technology</p>
          <h1>
            Driving <span className="text-gradient">Digital Transformation</span> Worldwide
          </h1>
          <p className="about-hero__lead">
            DXC Technology helps global companies run their mission-critical systems and operations while modernizing IT, optimizing data architectures, and ensuring security and scalability across public, private, and hybrid clouds.
          </p>
        </div>
      </section>

      <section className="about-section">
        <div className="about-grid">
          <article className="about-card glass-card">
            <div className="about-card__icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10" />
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            </div>
            <h3>Global Presence</h3>
            <p>
              With operations in over 70 countries and a workforce of approximately 130,000 employees, DXC Technology serves nearly 6,000 customers including most of the Fortune 500.
            </p>
          </article>

          <article className="about-card glass-card">
            <div className="about-card__icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <h3>Technology Leadership</h3>
            <p>
              DXC brings together deep industry expertise and technology capabilities to help clients harness the power of innovation. Our partnerships with leading technology companies enable us to deliver cutting-edge solutions.
            </p>
          </article>

          <article className="about-card glass-card">
            <div className="about-card__icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
            </div>
            <h3>Our People</h3>
            <p>
              Our diverse team of technologists, strategists, and industry specialists work together to solve the most complex challenges facing enterprises today, delivering measurable results.
            </p>
          </article>

          <article className="about-card glass-card">
            <div className="about-card__icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h3>Commitment to Excellence</h3>
            <p>
              We are committed to delivering excellence in everything we do, from the quality of our technology solutions to the sustainability of our business practices and corporate responsibility.
            </p>
          </article>
        </div>
      </section>

      <section className="about-section about-mission">
        <div className="about-mission__content glass-card">
          <h2>Our Mission</h2>
          <blockquote className="about-quote">
            "To help our customers thrive on change by delivering the technology and innovation they need to modernize and grow their businesses."
          </blockquote>
        </div>
      </section>

      <section className="about-section about-project-section">
        <header className="about-section__header">
          <h2>AI Sandbox Project</h2>
          <p className="about-section__subtitle">A collaboration between DXC Technology and ENSAM Casablanca</p>
        </header>

        <div className="about-project">
          <div className="about-project__header">
            <div className="about-project__logo">
              <img src={logoSrc} alt="DXC Technology" />
            </div>
            <div className="about-project__badge">
              <span className="text-brand">PFE Project</span>
            </div>
          </div>
          
          <div className="about-project__body">
            <p className="about-project__intro">
              The AI Sandbox is an enterprise-grade platform developed as a capstone project (PFE) in partnership between DXC Technology and ENSAM Casablanca. It provides a modular, governed environment for testing, comparing, validating, and benchmarking AI models before production integration.
            </p>
            
            <div className="about-project__capabilities">
              <h4>Key Capabilities</h4>
              <div className="capability-grid">
                <div className="capability-item">
                  <span className="capability-icon">📊</span>
                  <div>
                    <strong>Tabular ML</strong>
                    <p>Credit risk scoring, fraud detection with XGBoost, LightGBM, CatBoost</p>
                  </div>
                </div>
                <div className="capability-item">
                  <span className="capability-icon">📝</span>
                  <div>
                    <strong>NLP/LLM</strong>
                    <p>Document classification, summarization, sentiment analysis</p>
                  </div>
                </div>
                <div className="capability-item">
                  <span className="capability-icon">🔍</span>
                  <div>
                    <strong>RAG</strong>
                    <p>Q&amp;A on corporate corpus with retrieval-augmented generation</p>
                  </div>
                </div>
                <div className="capability-item">
                  <span className="capability-icon">🤖</span>
                  <div>
                    <strong>Agent Evaluation</strong>
                    <p>Benchmark agentic AI systems with comprehensive KPIs</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="about-project__sectors">
              <h4>Target Sectors</h4>
              <div className="sector-tags">
                <span className="sector-tag">Finance</span>
                <span className="sector-tag">Banking</span>
                <span className="sector-tag">Insurance</span>
                <span className="sector-tag">Public Sector</span>
              </div>
              <p className="sector-description">
                The platform is designed for regulated sectors where governance, compliance, and reproducibility are paramount.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="about-section about-stats">
        <div className="about-stats__grid">
          <div className="about-stat">
            <span className="about-stat__value">70+</span>
            <span className="about-stat__label">Countries</span>
          </div>
          <div className="about-stat">
            <span className="about-stat__value">130K+</span>
            <span className="about-stat__label">Employees</span>
          </div>
          <div className="about-stat">
            <span className="about-stat__value">6,000</span>
            <span className="about-stat__label">Customers</span>
          </div>
          <div className="about-stat">
            <span className="about-stat__value">$14B+</span>
            <span className="about-stat__label">Annual Revenue</span>
          </div>
        </div>
      </section>

      <section className="about-section about-cta">
        <div className="about-cta__content glass-card">
          <h2>Ready to Transform Your AI Operations?</h2>
          <p>
            Discover how the AI Sandbox can help your organization benchmark and validate AI models with enterprise-grade governance.
          </p>
          <div className="about-cta__actions">
            <a href="https://dxc.com" target="_blank" rel="noopener noreferrer" className="btn btn-primary">
              Visit DXC.com
            </a>
            <a href="https://dxc.com/us/en/about-us/contact-us" target="_blank" rel="noopener noreferrer" className="btn btn-ghost">
              Contact Us
            </a>
          </div>
        </div>
      </section>
    </main>
  );
};
