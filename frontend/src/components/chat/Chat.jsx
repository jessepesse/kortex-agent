/**
 * Chat - Main chat interface container
 * 
 * Uses modular sub-components:
 * - ChatMessages: Message list rendering
 * - ChatInput: Input with file attachments
 */

import React, { useState, useEffect, useRef } from 'react';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import '../Chat.css';

const Chat = ({
    messages,
    onSendMessage,
    isLoading,
    isSidebarOpen,
    councilLoading
}) => {
    const [inputValue, setInputValue] = useState('');
    const [selectedMode, setSelectedMode] = useState('normal');
    const [attachedFiles, setAttachedFiles] = useState([]);
    const [selectedProvider, setSelectedProvider] = useState('google');
    const messagesEndRef = useRef(null);

    async function loadSettings() {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5001'}/api/config`);
            const config = await response.json();
            setSelectedProvider(config.default_provider || 'google');
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Load model settings
    useEffect(() => {
        loadSettings();

        const handleModelChange = (event) => {
            setSelectedProvider(event.detail.provider);
        };
        window.addEventListener('modelChanged', handleModelChange);

        return () => window.removeEventListener('modelChanged', handleModelChange);
    }, []);

    // Handle quick actions
    useEffect(() => {
        const handleQuickAction = (event) => {
            setInputValue(event.detail);
        };
        window.addEventListener('quickAction', handleQuickAction);
        return () => window.removeEventListener('quickAction', handleQuickAction);
    }, []);

    const getCurrentModelSupport = () => {
        return selectedProvider === 'google' || selectedProvider === 'openai';
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!inputValue.trim() && attachedFiles.length === 0) return;

        let message = inputValue.trim();

        // Add mode prefix if not normal
        if (selectedMode === 'elite') {
            message = `/council ${message}`;
        } else if (selectedMode === 'hive') {
            message = `/hive ${message}`;
        } else if (selectedMode === 'mega') {
            message = `/mega ${message}`;
        }

        onSendMessage(message, attachedFiles);
        setInputValue('');
        setAttachedFiles([]);
    };

    return (
        <div className={`chat-container ${isSidebarOpen ? '' : 'full-width'}`}>
            <ChatMessages
                messages={messages}
                isLoading={isLoading}
                councilLoading={councilLoading}
                messagesEndRef={messagesEndRef}
            />

            <form onSubmit={handleSubmit} className="chat-form">
                <ChatInput
                    inputValue={inputValue}
                    setInputValue={setInputValue}
                    attachedFiles={attachedFiles}
                    setAttachedFiles={setAttachedFiles}
                    onSubmit={handleSubmit}
                    isLoading={isLoading}
                    selectedMode={selectedMode}
                    setSelectedMode={setSelectedMode}
                    supportsImages={getCurrentModelSupport()}
                />
            </form>
        </div>
    );
};

export default Chat;
