/**
 * ModelSettings - AI model selection component
 */

import React from 'react';

const ModelSettings = ({
    selectedModel,
    selectedProvider,
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
                    value={selectedModel}
                    onChange={handleChange}
                >
                    <optgroup label="Google">
                        <option value="gemini-2.5-flash">Gemini 2.5 Flash (Default)</option>
                        <option value="gemini-2.5-flash-lite">Gemini 2.5 Flash Lite</option>
                        <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                        <option value="gemini-3-pro-preview">Gemini 3 Pro Preview</option>
                    </optgroup>
                    <optgroup label="OpenAI">
                        <option value="gpt-5-mini">GPT-5 Mini</option>
                        <option value="gpt-5-nano">GPT-5 Nano</option>
                        <option value="gpt-5">GPT-5</option>
                        <option value="gpt-5.1">GPT-5.1</option>
                    </optgroup>
                    <optgroup label="Anthropic">
                        <option value="claude-haiku-4-5">Claude Haiku 4.5</option>
                        <option value="claude-haiku-3-5">Claude Haiku 3.5</option>
                        <option value="claude-haiku-3">Claude Haiku 3</option>
                    </optgroup>
                </select>
            </div>

            <div className="setting-group">
                <label>Council Chairman</label>
                <select className="model-select">
                    <option value="gemini-3-pro-preview">Gemini 3 Pro Preview (Default)</option>
                    <option value="gpt-5">GPT-5</option>
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
