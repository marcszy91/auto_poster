import { create } from 'zustand';
import { authApi, type UserResponse } from '../services/api';

interface AuthState {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  // Actions
  setUser: (user: UserResponse | null) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  setUser: (user) =>
    set({
      user,
      isAuthenticated: !!user,
      isLoading: false,
    }),

  login: async (email, password) => {
    try {
      await authApi.login({ email, password });

      // After login, fetch user data
      const user = await authApi.me();
      set({
        user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      throw error;
    }
  },

  register: async (email, password) => {
    try {
      const user = await authApi.register({ email, password });

      // After registration, user is created but needs to verify email
      // We still consider them "logged in" but with is_verified: false
      set({
        user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  checkAuth: async () => {
    try {
      set({ isLoading: true });
      const user = await authApi.me();
      set({
        user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },
}));
