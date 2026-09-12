import axios from 'axios';

// Dynamically target the backend port setup
const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const videoService = {
  /**
   * Uploads a raw video file with a prompt to initiate the pipeline assembly line.
   */
  uploadVideo: async (file, prompt) => {
    const formData = new FormData();
    formData.append('video', file);
    formData.append('prompt', prompt);

    const response = await axios.post(`${API_BASE_URL}/video/process`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Polls the current state of a pipeline processing chain.
   */
  checkPipelineStatus: async (taskId) => {
    const response = await api.get(`/video/status/${taskId}`);
    return response.data;
  },

  /**
   * Triggers the final high-quality crop rendering process using updated coordinates.
   */
  requestFinalExport: async (originalVideoPath, blueprint) => {
    const response = await api.get(`${API_BASE_URL}/export/render`, {
      original_video_path: originalVideoPath,
      blueprint: blueprint,
    });
    return response.data;
  },

  /**
   * Tracks final output asset generation.
   */
  checkExportStatus: async (taskId) => {
    const response = await api.get(`${API_BASE_URL}/export/status/${taskId}`);
    return response.data;
  }
};

export default api;
