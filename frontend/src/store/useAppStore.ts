import { create } from 'zustand';

interface AppState {
  // Navigation / UI State
  activePanel: 'sources' | 'viewer' | 'generator';
  isProcessing: boolean;
  
  // Data State
  documents: any[];
  currentSourceId: string | null;
  extractedText: string;
  sourceAnalysis: any | null;
  quizResult: any | null;

  // Actions
  setActivePanel: (panel: 'sources' | 'viewer' | 'generator') => void;
  setProcessing: (status: boolean) => void;
  setDocuments: (docs: any[]) => void;
  setCurrentSourceId: (id: string | null) => void;
  setExtractedText: (text: string) => void;
  setSourceAnalysis: (analysis: any) => void;
  setQuizResult: (quiz: any) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activePanel: 'sources',
  isProcessing: false,
  
  documents: [],
  currentSourceId: null,
  extractedText: '',
  sourceAnalysis: null,
  quizResult: null,

  setActivePanel: (panel) => set({ activePanel: panel }),
  setProcessing: (status) => set({ isProcessing: status }),
  setDocuments: (docs) => set({ documents: docs }),
  setCurrentSourceId: (id) => set({ currentSourceId: id }),
  setExtractedText: (text) => set({ extractedText: text }),
  setSourceAnalysis: (analysis) => set({ sourceAnalysis: analysis }),
  setQuizResult: (quiz) => set({ quizResult: quiz }),
}));
