import { create } from 'zustand';

interface AuthState {
  token: string | null;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: typeof window !== 'undefined' ? localStorage.getItem('quiz_token') : null,
  setToken: (token) => {
    if (token) {
      localStorage.setItem('quiz_token', token);
      document.cookie = `quiz_token=${token}; path=/; max-age=604800; SameSite=Lax`;
    } else {
      localStorage.removeItem('quiz_token');
      document.cookie = 'quiz_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    }
    set({ token });
  },
  logout: () => {
    localStorage.removeItem('quiz_token');
    document.cookie = 'quiz_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    set({ token: null });
    window.location.href = '/login';
  }
}));
