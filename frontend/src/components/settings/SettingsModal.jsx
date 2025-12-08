/**
 * SettingsModal - Main settings modal container
 * 
 * Uses modular sub-components:
 * - ModelSettings: AI model selection
 * - DataEditor: JSON data editing
 * - BackupRestore: Backup/restore functionality
 */

import React, { useState } from 'react';
import { useSettings } from './hooks/useSettings';
import ModelSettings from './ModelSettings';
import DataEditor, { DataEditorPanel } from './DataEditor';
import BackupRestore from './BackupRestore';
import '../SettingsModal.css';

const SettingsModal = ({ isOpen, onClose }) => {
    const [activeTab, setActiveTab] = useState('data');

    const {
        dataFiles,
        selectedFile,
        setSelectedFile,
        jsonContent,
        setJsonContent,
        selectedModel,
        selectedProvider,
        handleModelChange,
        conversations,
        selectedConversations,
        setSelectedConversations,
        handleSaveData,
        updateLanguage,
        loadData,
        loadConversations,
        status,
        setStatus
    } = useSettings(isOpen);

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

                        <ModelSettings
                            selectedModel={selectedModel}
                            selectedProvider={selectedProvider}
                            onModelChange={handleModelChange}
                            language={dataFiles.profile?.language}
                            onLanguageChange={updateLanguage}
                        />

                        {activeTab === 'data' && (
                            <DataEditor
                                dataFiles={dataFiles}
                                selectedFile={selectedFile}
                                onSelectFile={setSelectedFile}
                                jsonContent={jsonContent}
                                onJsonChange={setJsonContent}
                            />
                        )}
                    </div>

                    {/* Main content area */}
                    {activeTab === 'data' ? (
                        <DataEditorPanel
                            jsonContent={jsonContent}
                            onJsonChange={setJsonContent}
                        />
                    ) : (
                        <BackupRestore
                            conversations={conversations}
                            selectedConversations={selectedConversations}
                            setSelectedConversations={setSelectedConversations}
                            setStatus={setStatus}
                            onDataReload={async () => {
                                await loadData();
                                await loadConversations();
                            }}
                        />
                    )}
                </div>

                <div className="modal-footer">
                    <span className="status-msg">{status}</span>
                    {activeTab === 'data' && (
                        <button className="save-btn" onClick={handleSaveData}>Save Changes</button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SettingsModal;
