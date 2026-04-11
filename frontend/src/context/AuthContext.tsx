// /home/jao/Desktop/sandbox-project-vibecoded/frontend/src/context/AuthContext.tsx
import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const getStoredAuth = (): { token: string | null; user: User | null } => {
  if (typeof window === "undefined") {
    return { token: null, user: null };
  }
  const token = localStorage.getItem("ai-sandbox-token");
  const userJson = localStorage.getItem("ai-sandbox-user");
  let user: User | null = null;
  if (userJson) {
    try {
      user = JSON.parse(userJson);
    } catch {
      // Invalid JSON
    }
  }
  return { token, user };
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<AuthState>(() => {
    const { token, user } = getStoredAuth();
    return {
      isAuthenticated: !!token && !!user,
      user,
      token,
      loading: !!token, // If we have a token, we need to verify it
    };
  });
  const [error, setError] = useState<string | null>(null);

  // Verify token on mount
  useEffect(() => {
    const verifyToken = async () => {
      const { token } = getStoredAuth();
      if (!token) {
        setState((prev) => ({ ...prev, loading: false }));
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const user = await response.json();
          localStorage.setItem("ai-sandbox-user", JSON.stringify(user));
          setState({
            isAuthenticated: true,
            user,
            token,
            loading: false,
          });
        } else {
          // Token invalid, clear storage
          localStorage.removeItem("ai-sandbox-token");
          localStorage.removeItem("ai-sandbox-user");
          setState({
            isAuthenticated: false,
            user: null,
            token: null,
            loading: false,
          });
        }
      } catch {
        setState((prev) => ({ ...prev, loading: false }));
      }
    };

    void verifyToken();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setError(null);
    setState((prev) => ({ ...prev, loading: true }));

    try {
      // Login uses form-urlencoded
      const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ username, password }),
      });

      if (!loginResponse.ok) {
        const errorData = await loginResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || "Invalid credentials");
      }

      const { access_token } = await loginResponse.json();

      // Fetch user details
      const meResponse = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${access_token}`,
        },
      });

      if (!meResponse.ok) {
        throw new Error("Failed to fetch user details");
      }

      const user = await meResponse.json();

      // Store in localStorage
      localStorage.setItem("ai-sandbox-token", access_token);
      localStorage.setItem("ai-sandbox-user", JSON.stringify(user));

      setState({
        isAuthenticated: true,
        user,
        token: access_token,
        loading: false,
      });
    } catch (err) {
      setState((prev) => ({ ...prev, loading: false }));
      setError(err instanceof Error ? err.message : "Login failed");
      throw err;
    }
  }, []);

  const register = useCallback(
    async (email: string, username: string, password: string, fullName?: string) => {
      setError(null);
      setState((prev) => ({ ...prev, loading: true }));

      try {
        const registerResponse = await fetch(`${API_BASE_URL}/auth/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            username,
            password,
            full_name: fullName || null,
          }),
        });

        if (!registerResponse.ok) {
          const errorData = await registerResponse.json().catch(() => ({}));
          const detail = errorData.detail;
          if (typeof detail === "string") {
            throw new Error(detail);
          } else if (Array.isArray(detail) && detail.length > 0) {
            throw new Error(detail[0].msg || "Registration failed");
          }
          throw new Error("Registration failed");
        }

        // Auto-login after registration
        await login(username, password);
      } catch (err) {
        setState((prev) => ({ ...prev, loading: false }));
        setError(err instanceof Error ? err.message : "Registration failed");
        throw err;
      }
    },
    [login]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("ai-sandbox-token");
    localStorage.removeItem("ai-sandbox-user");
    setState({
      isAuthenticated: false,
      user: null,
      token: null,
      loading: false,
    });
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        register,
        logout,
        error,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
