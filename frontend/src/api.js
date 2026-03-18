const API_BASE_URL = 'http://localhost:8000/api/v1/teacher';

export const apiClient = {
  uploadFile: async (file, audience) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_audience_level', audience);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  },

  getDocuments: async () => {
    const response = await fetch(`${API_BASE_URL}/documents`);
    return response.json();
  },

  extractDocument: async (documentId) => {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    return response.json();
  },

  analyzeDocument: async (documentId) => {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    return response.json();
  },

  generateQuestions: async (documentId, config) => {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/generate-questions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return response.json();
  },

  exportQuiz: async (documentId, format = 'moodle') => {
    const response = await fetch(`${API_BASE_URL}/exports/${documentId}/${format}`);
    if (!response.ok) throw new Error('Export failed');
    return response.blob();
  }
};
