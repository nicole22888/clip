import axios from 'axios';

// Set up unified absolute base routes configuration parameters
const apiClient = axios.create({
    baseURL: '/',
    timeout: 600000 // Extended timeout to safely handle heavy multi-gigabyte video packet uploads
});

export const videoService = {
    uploadVideo: async (fileList, prompt, voiceText, voiceActor) => {
        const formData = new FormData();
        
        // Explicitly check and attach the raw file binary handle cleanly
        if (fileList && fileList.length > 0) {
            formData.append('video', fileList[0]);
        }
        
        formData.append('prompt', prompt);
        formData.append('voice_text', voiceText);
        formData.append('voice_actor', voiceActor);

        // CRITICAL FIX: Explicitly bind the multipart/form-data boundary headers 
        // to force the browser to upload raw video packets instead of empty text fields!
        const response = await apiClient.post('/api/video/process', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    },

    checkPipelineStatus: async (taskId) => {
        const response = await apiClient.get(`/api/video/status/${taskId}`);
        return response.data;
    },

    requestFinalExport: async (originalVideoPath, blueprint) => {
        const response = await apiClient.post('/api/export/render', {
            original_video_path: originalVideoPath,
            blueprint: blueprint
        });
        return response.data;
    },

    checkExportStatus: async (taskId) => {
        const response = await apiClient.get(`/api/export/status/${taskId}`);
        return response.data;
    }
};
