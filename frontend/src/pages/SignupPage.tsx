// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/SignupPage.tsx
import { FormEvent, useState } from "react";
import { useAuth } from "../context/AuthContext";

interface SignupPageProps {
  onNavigate: (view: "landing" | "login") => void;
  onSuccess: () => void;
}

export const SignupPage = ({ onNavigate, onSuccess }: SignupPageProps) => {
  const { register, loading, error, clearError, successMessage, clearSuccess } = useAuth();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();
    clearSuccess();

    if (!email.trim()) {
      setLocalError("Email is required");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setLocalError("Please enter a valid email address");
      return;
    }
    if (!username.trim()) {
      setLocalError("Username is required");
      return;
    }
    if (username.trim().length < 3) {
      setLocalError("Username must be at least 3 characters");
      return;
    }
    if (!password) {
      setLocalError("Password is required");
      return;
    }
    if (password.length < 8) {
      setLocalError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirmPassword) {
      setLocalError("Passwords do not match");
      return;
    }
    if (!acceptTerms) {
      setLocalError("You must accept the terms and conditions");
      return;
    }

    try {
      await register(email.trim(), username.trim(), password, fullName.trim() || undefined);
      onSuccess();
    } catch {
      // Error is handled by AuthContext
    }
  };

  const displayError = localError || error;

  // If success message, show it and don't show form
  if (successMessage) {
    return (
      <main className="auth-shell">
        <div className="auth-container">
          <div className="auth-form-side">
            <div className="auth-card">
              <div className="auth-success">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
                <h2>Welcome!</h2>
                <p>{successMessage}</p>
                <button type="button" className="btn btn-primary" onClick={onSuccess}>
                  Continue to Dashboard
                </button>
              </div>
            </div>
          </div>
          <div className="auth-decoration">
            <div className="auth-decoration__content">
              <h2>AI Sandbox</h2>
              <p>Enterprise-grade AI benchmarking platform for comparing ML, NLP, LLM, RAG, and agentic systems.</p>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="auth-shell">
      <div className="auth-container">
        <div className="auth-form-side">
          <div className="auth-card">
            <header className="auth-header">
              <h1 className="auth-title">Create Account</h1>
              <p className="auth-subtitle">Join AI Sandbox to start benchmarking</p>
            </header>

            <form className="auth-form" onSubmit={handleSubmit}>
              {displayError && (
                <div className="auth-error">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <span>{displayError}</span>
                </div>
              )}

              <div className="auth-row">
                <div className="auth-field">
                  <label htmlFor="fullName">Full Name</label>
                  <input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="John Doe"
                    autoComplete="name"
                  />
                </div>

                <div className="auth-field">
                  <label htmlFor="username">Username *</label>
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter username *"
                    autoComplete="username"
                    required
                  />
                </div>
              </div>

              <div className="auth-field">
                <label htmlFor="email">Email *</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="john@company.com *"
                  autoComplete="email"
                  required
                />
              </div>

              <div className="auth-row">
                <div className="auth-field">
                  <label htmlFor="password">Password *</label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min. 8 characters *"
                    autoComplete="new-password"
                    required
                  />
                </div>

                <div className="auth-field">
                  <label htmlFor="confirmPassword">Confirm *</label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm password *"
                    autoComplete="new-password"
                    required
                  />
                </div>
              </div>

              <div className="auth-terms">
                <label className="auth-checkbox">
                  <input
                    type="checkbox"
                    checked={acceptTerms}
                    onChange={(e) => setAcceptTerms(e.target.checked)}
                  />
                  <span>
                    I agree to the{" "}
                    <a href="#" className="auth-link-inline">
                      Terms of Service
                    </a>{" "}
                    and{" "}
                    <a href="#" className="auth-link-inline">
                      Privacy Policy
                    </a>
                  </span>
                </label>
              </div>

              <button type="submit" className="btn btn-primary auth-submit" disabled={loading}>
                {loading ? (
                  <>
                    <span className="auth-spinner" />
                    Creating account...
                  </>
                ) : (
                  "Create Account"
                )}
              </button>
            </form>

            <footer className="auth-footer">
              <p>
                Already have an account?{" "}
                <button type="button" className="auth-link" onClick={() => onNavigate("login")}>
                  Sign in
                </button>
              </p>
            </footer>
          </div>
        </div>

        <div className="auth-decoration">
          <div className="auth-decoration__content">
            <h2>AI Sandbox</h2>
            <p>Enterprise-grade AI benchmarking platform for comparing ML, NLP, LLM, RAG, and agentic systems.</p>
            <ul className="auth-features">
              <li>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>Multi-model comparison</span>
              </li>
              <li>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>Automated benchmarking</span>
              </li>
              <li>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>Detailed reports & analytics</span>
              </li>
              <li>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>Enterprise governance</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  );
};
