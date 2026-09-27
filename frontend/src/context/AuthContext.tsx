import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  getCurrentUserApi,
  getAuthToken,
  loginApi,
  registerApi,
  removeAuthToken,
  updateCurrentUserApi,
} from '../services/api';
import type { User, UserUpdateRequest } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  register: (data: { name?: string; email: string; password: string }) => Promise<void>;
  logout: () => void;
  updateUser: (data: UserUpdateRequest) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(getAuthToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    const currentToken = getAuthToken();
    if (!currentToken) {
      setUser(null);
      setTokenState(null);
      setIsLoading(false);
      return;
    }

    try {
      const u = await getCurrentUserApi();
      setUser(u);
      setTokenState(currentToken);
    } catch {
      removeAuthToken();
      setUser(null);
      setTokenState(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();

    const handleUnauthorized = () => {
      setUser(null);
      setTokenState(null);
    };

    window.addEventListener('finpilot-auth-unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('finpilot-auth-unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (credentials: { email: string; password: string }) => {
    setIsLoading(true);
    try {
      const res = await loginApi(credentials);
      setUser(res.user);
      setTokenState(res.access_token);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: { name?: string; email: string; password: string }) => {
    setIsLoading(true);
    try {
      const res = await registerApi(data);
      setUser(res.user);
      setTokenState(res.access_token);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    removeAuthToken();
    setUser(null);
    setTokenState(null);
  };

  const updateUser = async (data: UserUpdateRequest) => {
    const updated = await updateCurrentUserApi(data);
    setUser(updated);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        register,
        logout,
        updateUser,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
