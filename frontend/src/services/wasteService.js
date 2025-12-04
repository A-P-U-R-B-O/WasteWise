import axios from 'axios';

// API Base URL - change this to your backend URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Scan waste from uploaded image file
 */
export const scanWasteImage = async (file, userId = null) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (userId) {
      formData.append('user_id', userId);
    }

    const response = await api. post('/waste/scan', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return {
      success: true,
      ... response.data,
    };
  } catch (error) {
    console.error('Scan error:', error);
    return {
      success: false,
      message: error.response?.data?.detail || error.message || 'Failed to scan image',
    };
  }
};

/**
 * Scan waste from base64 encoded image
 */
export const scanWasteBase64 = async (base64Image, userId = null, location = null) => {
  try {
    const response = await api.post('/waste/scan/base64', {
      image_base64: base64Image,
      user_id: userId,
      location: location,
    });

    return {
      success: true,
      ...response.data,
    };
  } catch (error) {
    console. error('Scan error:', error);
    return {
      success: false,
      message: error.response?.data?.detail || error.message || 'Failed to scan image',
    };
  }
};

/**
 * Get all waste categories
 */
export const getWasteCategories = async () => {
  try {
    const response = await api.get('/waste/categories');
    return response. data;
  } catch (error) {
    console.error('Error fetching categories:', error);
    throw error;
  }
};

/**
 * Get educational content for a category
 */
export const getEducationalContent = async (category) => {
  try {
    const response = await api.get(`/waste/education/${encodeURIComponent(category)}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching education content:', error);
    throw error;
  }
};

/**
 * Get scan history for a user
 */
export const getScanHistory = async (userId, limit = 20, offset = 0) => {
  try {
    const response = await api.get(`/waste/history/${userId}`, {
      params: { limit, offset },
    });
    return response.data;
  } catch (error) {
    console. error('Error fetching history:', error);
    throw error;
  }
};

/**
 * Get user statistics
 */
export const getUserStats = async (userId) => {
  try {
    const response = await api.get(`/waste/stats/${userId}`);
    return response.data;
  } catch (error) {
    console. error('Error fetching stats:', error);
    throw error;
  }
};

/**
 * Delete a scan
 */
export const deleteScan = async (scanId, userId) => {
  try {
    const response = await api.delete(`/waste/scan/${scanId}`, {
      params: { user_id: userId },
    });
    return response. data;
  } catch (error) {
    console.error('Error deleting scan:', error);
    throw error;
  }
};

export default api;
