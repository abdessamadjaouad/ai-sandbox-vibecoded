// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/components/Navbar.tsx
import { useState } from "react";
import { useAuth } from "../context/AuthContext";

interface NavbarProps {
  logoSrc: string;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onNavigate: (view: "landing" | "wizard" | "login" | "signup" | "about" | "history") => void;
  currentView: string;
  apiDocsUrl: string;
  mlflowUrl: string;
}

export const Navbar = ({
  logoSrc,
  theme,
  onToggleTheme,
  onNavigate,
  currentView,
  apiDocsUrl,
  mlflowUrl,
}: NavbarProps) => {
  const { isAuthenticated, user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    onNavigate("landing");
  };

  const navLinks = [
    { label: "Home", view: "landing" as const },
    { label: "About Us", view: "about" as const },
    ...(isAuthenticated ? [{ label: "My Experiments", view: "history" as const }] : []),
    { label: "API Docs", href: apiDocsUrl, external: true },
    { label: "MLflow", href: mlflowUrl, external: true },
  ];

  return (
    <nav className={`navbar ${mobileMenuOpen ? "is-mobile-open" : ""}`}>
      <div className="navbar__left">
        <div className="navbar__brand" onClick={() => onNavigate("landing")} role="button" tabIndex={0}>
          <img src={logoSrc} alt="DXC" className="navbar__logo" />
          <div className="navbar__brand-text">
            <span className="navbar__brand-name">AI Sandbox</span>
            <span className="navbar__brand-tagline">Enterprise Benchmark Studio</span>
          </div>
        </div>
      </div>

      <div className="navbar__center">
        <ul className="navbar__links">
          {navLinks.map((link) =>
            link.external ? (
              <li key={link.label}>
                <a href={link.href} target="_blank" rel="noopener noreferrer" className="navbar__link">
                  {link.label}
                </a>
              </li>
            ) : (
              <li key={link.label}>
                <button
                  className={`navbar__link ${currentView === link.view ? "is-active" : ""}`}
                  onClick={() => {
                    if (link.view) {
                      onNavigate(link.view);
                      setMobileMenuOpen(false);
                    }
                  }}
                >
                  {link.label}
                </button>
              </li>
            )
          )}
        </ul>
      </div>

      <div className="navbar__right">
        <button
          className="navbar__theme-toggle"
          onClick={onToggleTheme}
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
        >
          {theme === "light" ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          )}
        </button>

        {isAuthenticated ? (
          <div className="navbar__user">
            <span className="navbar__user-name">{user?.full_name || user?.username}</span>
            <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
              Logout
            </button>
          </div>
        ) : (
          <div className="navbar__auth">
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => {
                onNavigate("login");
                setMobileMenuOpen(false);
              }}
            >
              Login
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => {
                onNavigate("signup");
                setMobileMenuOpen(false);
              }}
            >
              Sign Up
            </button>
          </div>
        )}

        <button
          className="navbar__mobile-toggle"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
          aria-expanded={mobileMenuOpen}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {mobileMenuOpen ? (
              <>
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </>
            ) : (
              <>
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            )}
          </svg>
        </button>
      </div>
    </nav>
  );
};
