// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/pages/LoginPage.tsx
import { FormEvent, useState } from "react";
import { useAuth } from "../context/AuthContext";

interface LoginPageProps {
  onNavigate: (view: "landing" | "signup") => void;
  onSuccess: () => void;
}

export const LoginPage = ({ onNavigate, onSuccess }: LoginPageProps) => {
  const { login, loading, error, clearError } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!username.trim()) {
      setLocalError("Username is required");
      return;
    }
    if (!password) {
      setLocalError("Password is required");
      return;
    }

    try {
      await login(username.trim(), password);
      onSuccess();
    } catch {
      // Error is handled by AuthContext
    }
  };

  const displayError = localError || error;

  return (
    <main className="auth-shell">
      <div className="auth-container">
        <div className="auth-form-side">
          <div className="auth-card">
            <header className="auth-header">
              <h1 className="auth-title">Welcome Back</h1>
              <p className="auth-subtitle">Sign in to access AI Sandbox</p>
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

              <div className="auth-field">
                <label htmlFor="username">Username</label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username *"
                  autoComplete="username"
                />
              </div>

              <div className="auth-field">
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password *"
                  autoComplete="current-password"
                />
              </div>

              <div className="auth-options">
                <label className="auth-checkbox">
                  <input 
                    type="checkbox" 
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  <span>Remember me</span>
                </label>
                <button type="button" className="auth-link">
                  Forgot password?
                </button>
              </div>

              <button type="submit" className="btn btn-primary auth-submit" disabled={loading}>
                {loading ? (
                  <>
                    <span className="auth-spinner" />
                    Signing in...
                  </>
                ) : (
                  "Sign In"
                )}
              </button>
            </form>

            <footer className="auth-footer">
              <p>
                Don't have an account?{" "}
                <button type="button" className="auth-link" onClick={() => onNavigate("signup")}>
                  Sign up
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
