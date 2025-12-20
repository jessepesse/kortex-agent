import React, { useState, useEffect } from 'react';
import { getAllData, updateDataFile, getBackupConversations, downloadBackup, validateBackup, restoreBackup } from '../services/api';
import './SettingsModal.css';

const SettingsModal = ({ isOpen, onClose }) => {
    const [dataFiles, setDataFiles] = useState({});
    const [selectedFile, setSelectedFile] = useState('profile');
    const [jsonContent, setJsonContent] = useState('');
    const [status, setStatus] = useState('');
    const [selectedModel, setSelectedModel] = useState('gemini-2.5-flash');
    const [selectedProvider, setSelectedProvider] = useState('google');
    const [availableModels, setAvailableModels] = useState({});

    // Backup state
    const [conversations, setConversations] = useState([]);
    const [selectedConversations, setSelectedConversations] = useState([]);
    const [backupLoading, setBackupLoading] = useState(false);
    const [restoreFile, setRestoreFile] = useState(null);
    const [validationResult, setValidationResult] = useState(null);
    const [activeTab, setActiveTab] = useState('data'); // 'data' or 'backup'

    useEffect(() => {
        if (isOpen) {
            loadData();
            loadModelSettings();
            loadConversations();
        }
    }, [isOpen]);

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
            // Select all by default
            setSelectedConversations(result.conversations?.map(c => c.id) || []);
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    };

    const loadModelSettings = async () => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5001'}/api/config`);
            const config = await response.json();
            console.log('📥 Loaded model settings:', config.default_model, config.default_provider, config.providers);
            console.log('📥 OPENROUTER:', config.providers?.openrouter);
            alert('Providers loaded: ' + Object.keys(config.providers || {}).join(', '));
            setSelectedModel(config.default_model || 'gemini-2.5-flash');
            setSelectedProvider(config.default_provider || 'google');
            setAvailableModels(config.providers || {});
        } catch (error) {
            console.error('Failed to load model settings:', error);
        }
    };

    const handleModelChange = async (e) => {
        const value = e.target.value;
        // Value format: "provider:model_id"
        const [provider, model] = value.split(':');
        console.log('🔄 Changing model to:', model, 'provider:', provider);
        setSelectedModel(model);
        setSelectedProvider(provider);
        console.log('📤 Saving to backend:', { provider, model });

        // Save to backend
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5001'}/api/models`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider, model })
            });
            const result = await response.json();
            console.log('✅ Backend response:', result);
            setStatus('Model updated!');
            setTimeout(() => setStatus(''), 2000);

            // Find if model supports thinking
            const modelData = availableModels[provider]?.find(m => 
                (typeof m === 'object' ? m.id : m) === model
            );
            const supportsThinking = typeof modelData === 'object' && modelData.thinking === true;

            // Trigger reload of Chat component's model settings
            window.dispatchEvent(new CustomEvent('modelChanged', { detail: { model, provider, supportsThinking } }));
        } catch (error) {
            console.error('❌ Failed to save model:', error);
            setStatus(`Error: ${error.message}`);
        }
    };

    const handleSave = async () => {
        try {
            setStatus('Saving...');
            const parsedData = JSON.parse(jsonContent);
            await updateDataFile(selectedFile, parsedData);
            setStatus('Saved!');
            setTimeout(() => setStatus(''), 2000);

            // Update local state
            setDataFiles(prev => ({
                ...prev,
                [selectedFile]: parsedData
            }));
        } catch (error) {
            setStatus(`Error: ${error.message}`);
        }
    };

    // Backup functions
    const handleDownloadBackup = async () => {
        try {
            setBackupLoading(true);
            setStatus('Creating backup...');

            // Pass selected conversation IDs, or null for all
            const convIds = selectedConversations.length === conversations.length
                ? null  // All selected = include all
                : selectedConversations.length === 0
                    ? []  // None selected = no conversations
                    : selectedConversations;

            const blob = await downloadBackup(convIds);

            // Trigger download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `kortex_backup_${new Date().toISOString().split('T')[0]}.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            setStatus('✅ Backup downloaded!');
            setTimeout(() => setStatus(''), 3000);
        } catch (error) {
            console.error('Backup failed:', error);
            setStatus(`❌ Error: ${error.message}`);
        } finally {
            setBackupLoading(false);
        }
    };

    const handleFileSelect = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setRestoreFile(file);
        setStatus('Validating backup...');

        try {
            const result = await validateBackup(file);
            setValidationResult(result);

            if (result.valid) {
                setStatus('✅ Backup is valid');
            } else {
                setStatus('❌ Backup validation failed');
            }
        } catch (error) {
            console.error('Validation failed:', error);
            setValidationResult({ valid: false, errors: [error.message] });
            setStatus('❌ Validation error');
        }
    };

    const handleRestore = async () => {
        if (!restoreFile || !validationResult?.valid) return;

        // Confirm with user
        const confirmed = window.confirm(
            '⚠️ VAROITUS!\n\n' +
            'Tämä toiminto YLIKIRJOITTAA kaiken nykyisen datan.\n' +
            'Tätä ei voi peruuttaa!\n\n' +
            'Haluatko varmasti jatkaa?'
        );

        if (!confirmed) return;

        try {
            setBackupLoading(true);
            setStatus('Restoring backup...');

            const result = await restoreBackup(restoreFile);

            if (result.success) {
                setStatus(`✅ Restored ${result.restored_files.length} files!`);
                // Reload data
                await loadData();
                await loadConversations();
                // Reset restore state
                setRestoreFile(null);
                setValidationResult(null);
            } else {
                setStatus(`❌ Restore failed: ${result.errors.join(', ')}`);
            }
        } catch (error) {
            console.error('Restore failed:', error);
            setStatus(`❌ Error: ${error.message}`);
        } finally {
            setBackupLoading(false);
        }
    };

    const toggleConversation = (id) => {
        setSelectedConversations(prev =>
            prev.includes(id)
                ? prev.filter(x => x !== id)
                : [...prev, id]
        );
    };

    const toggleAllConversations = () => {
        if (selectedConversations.length === conversations.length) {
            setSelectedConversations([]);
        } else {
            setSelectedConversations(conversations.map(c => c.id));
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content settings-modal">
                <div className="modal-header">
                    <h2>Settings</h2>
                    <button className="close-button" onClick={onClose}>&times;</button>
                </div>

                <div className="modal-body">
                    <div className="settings-sidebar">
                        {/* Tab buttons */}
                        <div className="settings-tabs">
                            <button
                                className={`tab-btn ${activeTab === 'data' ? 'active' : ''}`}
                                onClick={() => setActiveTab('data')}
                            >
                                📁 System Data
                            </button>
                            <button
                                className={`tab-btn ${activeTab === 'backup' ? 'active' : ''}`}
                                onClick={() => setActiveTab('backup')}
                            >
                                💾 Backup
                            </button>
                        </div>

                        <h3>AI Configuration</h3>
                        {/* Debug: show available models count */}
                        <p style={{fontSize: '10px', color: '#666'}}>
                            Providers: {Object.keys(availableModels).join(', ') || 'none loaded'}
                        </p>
                        <div className="setting-group">
                            <label>Standard Chat Model</label>
                            <select
                                className="model-select"
                                value={`${selectedProvider}:${selectedModel}`}
                                onChange={handleModelChange}
                            >
                                {Object.entries(availableModels).map(([provider, models]) => (
                                    <optgroup key={provider} label={provider.charAt(0).toUpperCase() + provider.slice(1)}>
                                        {models.map((model) => {
                                            const modelId = typeof model === 'object' ? model.id : model;
                                            const displayName = modelId.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                                            return (
                                                <option key={modelId} value={`${provider}:${modelId}`}>
                                                    {displayName}
                                                </option>
                                            );
                                        })}
                                    </optgroup>
                                ))}
                            </select>
                        </div>
                        <div className="setting-group">
                            <label>Council Chairman</label>
                            <select className="model-select">
                                <option value="gemini-3-pro-preview">Gemini 3 Pro Preview (Default)</option>
                                <option value="gpt-5.2">GPT-5.2</option>
                                <option value="claude-opus-4-5">Claude Opus 4.5</option>
                            </select>
                        </div>

                        <div className="setting-group">
                            <label>Language / Kieli</label>
                            <select
                                className="model-select"
                                value={dataFiles.profile?.language || 'Finnish'}
                                onChange={async (e) => {
                                    const newLanguage = e.target.value;
                                    try {
                                        const updatedProfile = { ...dataFiles.profile, language: newLanguage };
                                        await updateDataFile('profile', updatedProfile);
                                        setDataFiles(prev => ({ ...prev, profile: updatedProfile }));
                                        setStatus('Language updated!');
                                        setTimeout(() => setStatus(''), 2000);
                                    } catch (error) {
                                        setStatus(`Error: ${error.message}`);
                                    }
                                }}
                            >
                                <option value="Finnish">🇫🇮 Suomi (Finnish)</option>
                                <option value="English">🇬🇧 English</option>
                                <option value="Swedish">🇸🇪 Svenska (Swedish)</option>
                                <option value="German">🇩🇪 Deutsch (German)</option>
                                <option value="Spanish">🇪🇸 Español (Spanish)</option>
                                <option value="French">🇫🇷 Français (French)</option>
                            </select>
                        </div>

                        {activeTab === 'data' && (
                            <>
                                <h3>Data Files</h3>
                                <div className="file-list">
                                    {Object.keys(dataFiles).map(filename => (
                                        <button
                                            key={filename}
                                            className={`file-btn ${selectedFile === filename ? 'active' : ''}`}
                                            onClick={() => setSelectedFile(filename)}
                                        >
                                            {filename}.json
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}
                    </div>

                    {/* Main content area */}
                    {activeTab === 'data' ? (
                        <div className="editor-container">
                            <textarea
                                value={jsonContent}
                                onChange={(e) => setJsonContent(e.target.value)}
                                spellCheck="false"
                            />
                        </div>
                    ) : (
                        <div className="backup-container">
                            {/* Download Backup */}
                            <div className="backup-section">
                                <h3>📥 Lataa varmuuskopio</h3>
                                <p className="backup-desc">
                                    Lataa kaikki datasi ZIP-tiedostona. Valitse mitkä keskustelut otetaan mukaan.
                                </p>

                                <div className="conversation-selector">
                                    <label className="checkbox-label select-all">
                                        <input
                                            type="checkbox"
                                            checked={selectedConversations.length === conversations.length && conversations.length > 0}
                                            onChange={toggleAllConversations}
                                        />
                                        <span>Valitse kaikki keskustelut ({conversations.length})</span>
                                    </label>

                                    <div className="conversation-list">
                                        {conversations.map(conv => (
                                            <label key={conv.id} className="checkbox-label">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedConversations.includes(conv.id)}
                                                    onChange={() => toggleConversation(conv.id)}
                                                />
                                                <span className="conv-title">
                                                    {conv.pinned && '📌 '}
                                                    {conv.title}
                                                </span>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                <button
                                    className="backup-btn download-btn"
                                    onClick={handleDownloadBackup}
                                    disabled={backupLoading}
                                >
                                    {backupLoading ? '⏳ Creating...' : '📥 Lataa Backup'}
                                </button>
                            </div>

                            {/* Restore Backup */}
                            <div className="backup-section restore-section">
                                <h3>📤 Palauta varmuuskopiosta</h3>
                                <p className="backup-desc warning">
                                    ⚠️ Huomio: Palautus ylikirjoittaa kaiken nykyisen datan!
                                </p>

                                <input
                                    type="file"
                                    accept=".zip"
                                    onChange={handleFileSelect}
                                    className="file-input"
                                    id="restore-file-input"
                                />
                                <label htmlFor="restore-file-input" className="file-input-label">
                                    {restoreFile ? `📎 ${restoreFile.name}` : '📁 Valitse ZIP-tiedosto'}
                                </label>

                                {validationResult && (
                                    <div className={`validation-result ${validationResult.valid ? 'valid' : 'invalid'}`}>
                                        <div className="validation-header">
                                            {validationResult.valid ? '✅ Validi backup' : '❌ Virheellinen backup'}
                                        </div>
                                        {validationResult.manifest && (
                                            <div className="validation-details">
                                                <span>📅 {new Date(validationResult.manifest.created_at).toLocaleString('fi-FI')}</span>
                                                <span>📁 {validationResult.manifest.stats?.data_files || 0} datatiedostoa</span>
                                                <span>💬 {validationResult.manifest.stats?.conversations || 0} keskustelua</span>
                                            </div>
                                        )}
                                        {validationResult.errors?.length > 0 && (
                                            <ul className="error-list">
                                                {validationResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                                            </ul>
                                        )}
                                        {validationResult.warnings?.length > 0 && (
                                            <ul className="warning-list">
                                                {validationResult.warnings.map((w, i) => <li key={i}>{w}</li>)}
                                            </ul>
                                        )}
                                    </div>
                                )}

                                <button
                                    className="backup-btn restore-btn"
                                    onClick={handleRestore}
                                    disabled={!validationResult?.valid || backupLoading}
                                >
                                    {backupLoading ? '⏳ Restoring...' : '⚠️ Palauta Backup'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                <div className="modal-footer">
                    <span className="status-msg">{status}</span>
                    {activeTab === 'data' && (
                        <button className="save-btn" onClick={handleSave}>Save Changes</button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SettingsModal;
