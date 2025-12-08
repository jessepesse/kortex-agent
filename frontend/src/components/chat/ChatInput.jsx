/**
 * ChatInput - Message input with file attachment support
 */

import React, { useRef } from 'react';
import FilePreview from '../FilePreview';

const ChatInput = ({
    inputValue,
    setInputValue,
    attachedFiles,
    setAttachedFiles,
    onSubmit,
    isLoading,
    selectedMode,
    setSelectedMode,
    supportsImages
}) => {
    const fileInputRef = useRef(null);
    const textareaRef = useRef(null);

    const handleFileSelect = async (e) => {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        const processedFiles = [];
        for (const file of files) {
            if (file.type.startsWith('image/')) {
                const base64 = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result);
                    reader.readAsDataURL(file);
                });
                processedFiles.push({
                    name: file.name,
                    type: file.type,
                    size: file.size,
                    base64: base64
                });
            } else if (file.type === 'application/pdf') {
                processedFiles.push({
                    name: file.name,
                    type: file.type,
                    size: file.size,
                    base64: null
                });
            }
        }

        setAttachedFiles(prev => [...prev, ...processedFiles]);
        e.target.value = '';
    };

    const handleRemoveFile = (index) => {
        setAttachedFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSubmit(e);
        }
    };

    return (
        <div className="chat-input-container">
            {attachedFiles.length > 0 && (
                <div className="attached-files">
                    {attachedFiles.map((file, index) => (
                        <FilePreview
                            key={index}
                            file={file}
                            onRemove={() => handleRemoveFile(index)}
                        />
                    ))}
                </div>
            )}

            <div className="input-row">
                <div className="mode-selector">
                    <select
                        value={selectedMode}
                        onChange={(e) => setSelectedMode(e.target.value)}
                        className="mode-dropdown"
                    >
                        <option value="normal">💬 Normal</option>
                        <option value="elite">👑 Elite Council</option>
                        <option value="hive">🐝 Hive Council</option>
                        <option value="mega">🔥 MEGA Council</option>
                    </select>
                </div>

                <div className="input-wrapper">
                    <textarea
                        ref={textareaRef}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type a message..."
                        rows={1}
                        disabled={isLoading}
                    />

                    <div className="input-actions">
                        {supportsImages && (
                            <>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    onChange={handleFileSelect}
                                    accept="image/*,.pdf"
                                    multiple
                                    style={{ display: 'none' }}
                                />
                                <button
                                    type="button"
                                    className="attach-btn"
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={isLoading}
                                    title="Attach files"
                                >
                                    📎
                                </button>
                            </>
                        )}

                        <button
                            type="submit"
                            className="send-btn"
                            disabled={isLoading || (!inputValue.trim() && attachedFiles.length === 0)}
                            onClick={onSubmit}
                        >
                            {isLoading ? '⏳' : '➤'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatInput;
