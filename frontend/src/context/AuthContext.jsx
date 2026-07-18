import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { getMe, login as loginRequest, register as registerRequest } from '../api/authApi.js';

const AuthContext = createContext(null);
const TOKEN_KEY = 'furicare_access_token';
const USER_KEY = 'furicare_user';

function readStoredUser() {
  try {
    const value = localStorage.getItem(USER_KEY);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '');
  const [user, setUser] = useState(readStoredUser);
  const [initializing, setInitializing] = useState(Boolean(token));

  const persistSession = useCallback((data) => {
    localStorage.setItem(TOKEN_KEY, data.accessToken);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    setToken(data.accessToken);
    setUser(data.user);
  }, []);

  const clearSession = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken('');
    setUser(null);
  }, []);

  useEffect(() => {
    let ignore = false;

    if (!token) {
      setInitializing(false);
      return () => {
        ignore = true;
      };
    }

    getMe(token)
      .then((data) => {
        if (ignore) return;
        localStorage.setItem(USER_KEY, JSON.stringify(data.user));
        setUser(data.user);
      })
      .catch(() => {
        if (!ignore) clearSession();
      })
      .finally(() => {
        if (!ignore) setInitializing(false);
      });

    return () => {
      ignore = true;
    };
  }, [clearSession, token]);

  const login = useCallback(
    async (input) => {
      const data = await loginRequest(input);
      persistSession(data);
      return data.user;
    },
    [persistSession],
  );

  const register = useCallback(
    async (input) => {
      const data = await registerRequest(input);
      persistSession(data);
      return data.user;
    },
    [persistSession],
  );

  const value = useMemo(
    () => ({
      token,
      user,
      initializing,
      isAuthenticated: Boolean(token && user),
      login,
      register,
      logout: clearSession,
    }),
    [clearSession, initializing, login, register, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return value;
}
