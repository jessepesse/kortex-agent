/**
 * API Service - Axios client for backend communication
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const unwrapData = (response, fallback = {}) => response.data?.data ?? fallback;

/**
 * Send a chat message to AI
 */
export const sendMessage = async (message, history = [], model = null, provider = null, chatId = null, files = [], reasoningConfig = null, webSearchEnabled = false, forceSearchModel = null) => {
  // If web search is enabled, use the websearch endpoint
  if (webSearchEnabled) {
    const payload = { 
      message, 
      history,
      reasoning_enabled: reasoningConfig?.enabled || false
    };
    if (model) payload.model = model;
    if (provider) payload.provider = provider;
    if (chatId) payload.chat_id = chatId;
    if (forceSearchModel) payload.force_model = forceSearchModel;
    
    const response = await api.post('/api/chat/websearch', payload);
    return unwrapData(response, {});
  }
  
  // Standard chat endpoint
  const payload = { message, history };
  if (model) payload.model = model;
  if (provider) payload.provider = provider;
  if (chatId) payload.chat_id = chatId;
  if (reasoningConfig) payload.openrouter_reasoning_config = reasoningConfig;

  // Process files if provided
  if (files && files.length > 0) {
    const processedFiles = await Promise.all(files.map(async (fileObj) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const base64 = e.target.result.split(',')[1]; // Remove data:image/png;base64, prefix
          resolve({
            name: fileObj.name,
            type: fileObj.type,
            data: base64
          });
        };
        reader.onerror = reject;
        reader.readAsDataURL(fileObj.file);
      });
    }));
    payload.files = processedFiles;
  }

  const response = await api.post('/api/chat', payload);
  return unwrapData(response, {});
};

export const getHistory = async () => {
  const response = await api.get('/api/history');
  return response.data;
};

export const getChat = async (chatId) => {
  const response = await api.get(`/api/history/${chatId}`);
  return response.data;
};

/**
 * Run Scout analysis to check if web search is needed
 * Returns: { decision, confidence, search_type, reason, recommended_model }
 */
export const scoutAnalyze = async (message, history = []) => {
  const response = await api.post('/api/chat/scout', { message, history });
  return unwrapData(response, {});
};

/**
 * Delete a conversation by ID
 */
export const deleteConversation = async (chatId) => {
  const response = await api.delete(`/api/history/${chatId}`);
  return response.data;
};

/**
 * Toggle pin status of a conversation
 */
export const pinConversation = async (chatId) => {
  const response = await api.post(`/api/pin/${chatId}`);
  return response.data;
};

/**
 * Run Elite Council Mode (3 top models voting)
 */
export const runCouncil = async (message, history, chatId = null) => {
  try {
    const payload = { message, history };
    if (chatId) payload.chat_id = chatId;
    const response = await api.post('/api/council', payload);
    return unwrapData(response, {});
  } catch (error) {
    console.error('Error running council:', error);
    return { error: error.message };
  }
};

/**
 * Run Hive Mode (6 DeepSeek personas)
 */
export const runHive = async (message, history, chatId = null) => {
  try {
    const payload = { message, history };
    if (chatId) payload.chat_id = chatId;
    const response = await api.post('/api/hive', payload);
    return unwrapData(response, {});
  } catch (error) {
    console.error('Error running hive:', error);
    return { error: error.message };
  }
};

/**
 * Run MEGA Mode (Elite + Hive → Ultimate Chairman)
 */
export const runMega = async (message, history, chatId = null) => {
  try {
    const payload = { message, history };
    if (chatId) payload.chat_id = chatId;
    const response = await api.post('/api/mega', payload);
    return unwrapData(response, {});
  } catch (error) {
    console.error('Error running mega:', error);
    return { error: error.message };
  }
};


export const getAllData = async () => {
  const response = await api.get('/api/data');
  return response.data;
};

/**
 * Get a specific data file
 */
export const getDataFile = async (filename) => {
  const response = await api.get(`/api/data/${filename}`);
  return response.data;
};

/**
 * Update a specific data file
 */
export const updateDataFile = async (filename, data) => {
  const response = await api.put(`/api/data/${filename}`, { data });
  return response.data;
};

/**
 * Get available models and current selection
 */
export const getModels = async () => {
  const response = await api.get('/api/config');
  return response.data;
};

/**
 * Set the default model and provider
 */
export const setModel = async (provider, model) => {
  const response = await api.post('/api/models', { provider, model });
  return response.data;
};

/**
 * Execute a function call (after user approval)
 */
export const executeFunction = async (functionName, args) => {
  const response = await api.post('/api/function-call/execute', {
    function_name: functionName,
    args,
  });
  return unwrapData(response, { success: false, message: 'Execution failed' });
};

/**
 * Get API keys status
 */
export const getApiKeysStatus = async () => {
  const response = await api.get('/api/config/api-keys');
  return response.data;
};

/**
 * Set API keys
 */
export const setApiKeys = async (keys) => {
  const response = await api.post('/api/config/api-keys', keys);
  return response.data;
};

// =============================================================================
// BACKUP & RESTORE
// =============================================================================

/**
 * Get conversations for backup selection
 */
export const getBackupConversations = async () => {
  const response = await api.get('/api/backup/conversations');
  // Backend returns { success: true, data: { conversations: [...] } }
  return response.data?.data || { conversations: [] };
};

/**
 * Download backup as ZIP file
 * @param {string[]|null} conversationIds - List of conversation IDs, null for all
 * @returns {Blob} ZIP file blob
 */
export const downloadBackup = async (conversationIds = null) => {
  const response = await api.post('/api/backup/download',
    { conversation_ids: conversationIds },
    { responseType: 'blob' }
  );
  return response.data;
};

/**
 * Validate an uploaded backup file
 * @param {File} file - ZIP file to validate
 */
export const validateBackup = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/backup/validate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  // Backend returns { success: true, data: { valid, errors, warnings, ... } }
  return response.data?.data || {
    valid: false,
    errors: ['Invalid validation response'],
    warnings: [],
    manifest: null,
    files: []
  };
};

/**
 * Restore from a backup file (OVERWRITES ALL DATA!)
 * @param {File} file - ZIP file to restore from
 */
export const restoreBackup = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/backup/restore', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  // Backend returns { success: true, data: { success, restored_files, errors } }
  return response.data?.data || {
    success: false,
    restored_files: [],
    errors: ['Invalid restore response']
  };
};

export default api;
