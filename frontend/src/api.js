const API_BASE_URL = 'http://localhost:8000/api/v1/teacher';

export const apiClient = {
  uploadFile: async (file, audience) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_audience_level', audience);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  },

  getDocuments: async () => {
    // This endpoint remains to be confirmed if we want a list
    // For now, we interact with specific document IDs
  },

  analyzeDocument: async (documentId) => {
    const response = await fetch(`${API_BASE_URL}/analyze/${documentId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    return response.json();
  },

  generateQuestions: async (documentId, config) => {
    const response = await fetch(`${API_BASE_URL}/generate-questions/${documentId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return response.json();
  },

  exportQuiz: async (documentId, format = 'moodle') => {
    const response = await fetch(`${API_BASE_URL}/export/${documentId}?format=${format}`);
    return response.json();
  }
};
