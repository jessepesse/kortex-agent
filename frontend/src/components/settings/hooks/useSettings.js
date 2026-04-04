/**
 * useSettings - Custom hook for settings state management
 */

import { useState, useEffect, useCallback } from 'react';
import { getAllData, updateDataFile, getBackupConversations } from '../../../services/api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

export function useSettings(isOpen) {
    const [dataFiles, setDataFiles] = useState({});
    const [selectedFile, setSelectedFile] = useState('profile');
    const [jsonContent, setJsonContent] = useState('');
    const [status, setStatus] = useState('');
    const [selectedModel, setSelectedModel] = useState('gemini-3-flash-preview');
    const [selectedProvider, setSelectedProvider] = useState('google');
    const [availableModels, setAvailableModels] = useState({});
    const [conversations, setConversations] = useState([]);
    const [selectedConversations, setSelectedConversations] = useState([]);

    const loadData = useCallback(async () => {
        try {
            const data = await getAllData();
            setDataFiles(data);
            if (data[selectedFile]) {
                setJsonContent(JSON.stringify(data[selectedFile], null, 2));
            }
        } catch (error) {
            console.error('Failed to load data:', error);
        }
    }, [selectedFile]);

    const loadConversations = useCallback(async () => {
        try {
            const result = await getBackupConversations();
            setConversations(result.conversations || []);
            setSelectedConversations(result.conversations?.map(c => c.id) || []);
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    }, []);

    const [ollamaStatus, setOllamaStatus] = useState({ available: false, error: null });

    const loadOllamaModels = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/api/ollama/models`);
            const result = await response.json();
            const data = result.data || result;
            setOllamaStatus({ available: data.available, error: data.error || null });
            return data.available ? data.models.map(m => ({ id: m.id, display_name: m.display_name, size_gb: m.size_gb })) : [];
        } catch {
            setOllamaStatus({ available: false, error: 'Failed to fetch Ollama models' });
            return [];
        }
    }, []);

    const loadModelSettings = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/api/config`);
            const result = await response.json();
            const config = result.data || result;
            console.log('📥 Loaded model settings:', config.default_model, config.default_provider, config.providers);
            setSelectedModel(config.default_model || 'gemini-3-flash-preview');
            setSelectedProvider(config.default_provider || 'google');

            // Fetch Ollama models dynamically
            const ollamaModels = await loadOllamaModels();
            const providers = { ...(config.providers || {}) };
            if (ollamaModels.length > 0) {
                providers.ollama = ollamaModels.map(m => ({ id: m.id }));
            } else if (!providers.ollama || providers.ollama.length === 0) {
                // Keep ollama in list but empty so UI can show status
                providers.ollama = [];
            }
            setAvailableModels(providers);
        } catch (error) {
            console.error('Failed to load model settings:', error);
        }
    }, [loadOllamaModels]);

    // Load data when modal opens
    useEffect(() => {
        if (isOpen) {
            loadData();
            loadModelSettings();
            loadConversations();
        }
    }, [isOpen, loadData, loadModelSettings, loadConversations]);

    // Update JSON content when file changes
    useEffect(() => {
        if (dataFiles[selectedFile]) {
            setJsonContent(JSON.stringify(dataFiles[selectedFile], null, 2));
        }
    }, [selectedFile, dataFiles]);

    const handleModelChange = async (providerAndModel) => {
        // Value format: "provider:model_id" (model_id may contain colons, e.g. "qwen3:8b")
        const sepIndex = providerAndModel.indexOf(':');
        const provider = providerAndModel.substring(0, sepIndex);
        const model = providerAndModel.substring(sepIndex + 1);
        console.log('🔄 Changing model to:', model, 'provider:', provider);
        setSelectedModel(model);
        setSelectedProvider(provider);

        try {
            const response = await fetch(`${API_URL}/api/models`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider, model })
            });
            await response.json();
            setStatus('Model updated!');
            setTimeout(() => setStatus(''), 2000);

            // Find if model supports thinking
            const modelData = availableModels[provider]?.find(m =>
                (typeof m === 'object' ? m.id : m) === model
            );
            const supportsThinking = typeof modelData === 'object' && modelData.thinking === true;

            window.dispatchEvent(new CustomEvent('modelChanged', { detail: { model, provider, supportsThinking } }));
        } catch (error) {
            setStatus(`Error: ${error.message}`);
        }
    };

    const handleSaveData = async () => {
        try {
            setStatus('Saving...');
            const parsedData = JSON.parse(jsonContent);
            await updateDataFile(selectedFile, parsedData);
            setStatus('Saved!');
            setTimeout(() => setStatus(''), 2000);
            setDataFiles(prev => ({ ...prev, [selectedFile]: parsedData }));
        } catch (error) {
            setStatus(`Error: ${error.message}`);
        }
    };

    const updateLanguage = async (newLanguage) => {
        try {
            const updatedProfile = { ...dataFiles.profile, language: newLanguage };
            await updateDataFile('profile', updatedProfile);
            setDataFiles(prev => ({ ...prev, profile: updatedProfile }));
            setStatus('Language updated!');
            setTimeout(() => setStatus(''), 2000);
        } catch (error) {
            setStatus(`Error: ${error.message}`);
        }
    };

    return {
        // Data state
        dataFiles,
        selectedFile,
        setSelectedFile,
        jsonContent,
        setJsonContent,

        // Model state
        selectedModel,
        selectedProvider,
        availableModels,
        handleModelChange,
        ollamaStatus,

        // Backup state
        conversations,
        selectedConversations,
        setSelectedConversations,

        // Actions
        handleSaveData,
        updateLanguage,
        loadData,
        loadConversations,

        // Status
        status,
        setStatus
    };
}
