/**
 * useSettings - Custom hook for settings state management
 */

import { useState, useEffect } from 'react';
import { getAllData, updateDataFile, getBackupConversations } from '../../../services/api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

export function useSettings(isOpen) {
    const [dataFiles, setDataFiles] = useState({});
    const [selectedFile, setSelectedFile] = useState('profile');
    const [jsonContent, setJsonContent] = useState('');
    const [status, setStatus] = useState('');
    const [selectedModel, setSelectedModel] = useState('gemini-2.5-flash');
    const [selectedProvider, setSelectedProvider] = useState('google');
    const [conversations, setConversations] = useState([]);
    const [selectedConversations, setSelectedConversations] = useState([]);

    // Load data when modal opens
    useEffect(() => {
        if (isOpen) {
            loadData();
            loadModelSettings();
            loadConversations();
        }
    }, [isOpen]);

    // Update JSON content when file changes
    useEffect(() => {
        if (dataFiles[selectedFile]) {
            setJsonContent(JSON.stringify(dataFiles[selectedFile], null, 2));
        }
    }, [selectedFile, dataFiles]);

    const loadData = async () => {
        try {
            const data = await getAllData();
            setDataFiles(data);
            if (data[selectedFile]) {
                setJsonContent(JSON.stringify(data[selectedFile], null, 2));
            }
        } catch (error) {
            console.error('Failed to load data:', error);
        }
    };

    const loadConversations = async () => {
        try {
            const result = await getBackupConversations();
            setConversations(result.conversations || []);
            setSelectedConversations(result.conversations?.map(c => c.id) || []);
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    };

    const loadModelSettings = async () => {
        try {
            const response = await fetch(`${API_URL}/api/config`);
            const config = await response.json();
            setSelectedModel(config.default_model || 'gemini-2.5-flash');
            setSelectedProvider(config.default_provider || 'google');
        } catch (error) {
            console.error('Failed to load model settings:', error);
        }
    };

    const handleModelChange = async (model) => {
        setSelectedModel(model);

        // Determine provider from model name
        let provider = 'google';
        if (model.startsWith('gpt')) provider = 'openai';
        else if (model.startsWith('claude')) provider = 'anthropic';
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
            window.dispatchEvent(new CustomEvent('modelChanged', { detail: { model, provider } }));
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
        handleModelChange,

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
