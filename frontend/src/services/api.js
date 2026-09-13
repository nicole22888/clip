import axios from 'axios';

const apiClient = axios.create({
    baseURL: '/',
    timeout: 600000
});

export const videoService = {
    uploadVideo: async (fileList, prompt, voiceText, voiceActor) => {
        const formData = new FormData();

        // DEFENSIVE CHECK: Accept a File, FileList, or File[] without serializing the wrapper.
        let videoFile = null;

        if (fileList instanceof File) {
            videoFile = fileList;
        } else if (fileList && fileList.length > 0) {
            videoFile = fileList[0];
        }

        if (!videoFile) {
            throw new Error('No video file was selected.');
        }

        formData.append('video', videoFile);
        
        formData.append('prompt', prompt);
        formData.append('voice_text', voiceText);
        formData.append('voice_actor', voiceActor);

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
