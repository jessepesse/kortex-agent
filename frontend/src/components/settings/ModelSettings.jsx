/**
 * ModelSettings - AI model selection component
 */

import React from 'react';

const ModelSettings = ({
    selectedModel,
    selectedProvider,
    availableModels,
    onModelChange,
    language,
    onLanguageChange
}) => {
    const handleChange = (e) => {
        onModelChange(e.target.value);
    };

    return (
        <>
            <h3>AI Configuration</h3>
            <div className="setting-group">
                <label>Standard Chat Model</label>
                <select
                    className="model-select"
                    value={`${selectedProvider}:${selectedModel}`}
                    onChange={handleChange}
                >
                    {Object.entries(availableModels || {}).map(([provider, models]) => (
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
                    value={language || 'Finnish'}
                    onChange={(e) => onLanguageChange(e.target.value)}
                >
                    <option value="Finnish">🇫🇮 Suomi (Finnish)</option>
                    <option value="English">🇬🇧 English</option>
                    <option value="Swedish">🇸🇪 Svenska (Swedish)</option>
                    <option value="German">🇩🇪 Deutsch (German)</option>
                    <option value="Spanish">🇪🇸 Español (Spanish)</option>
                    <option value="French">🇫🇷 Français (French)</option>
                </select>
            </div>
        </>
    );
};

export default ModelSettings;
