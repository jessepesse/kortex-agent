/**
 * Chat Component - Main chat interface
 */

import React, { useState, useEffect, useRef } from 'react';
import Message from './Message';
import LoadingIndicator from './LoadingIndicator';
import CouncilView from './CouncilView';
import MegaView from './MegaView';
import FilePreview from './FilePreview';
import ScoutCard from './ScoutCard';
import { scoutAnalyze } from '../services/api';
import './Chat.css';

const Chat = ({ messages, onSendMessage, isLoading, contextData, councilLoading }) => {
    const [input, setInput] = useState('');
    const [attachedFiles, setAttachedFiles] = useState([]);
    const [councilMode, setCouncilMode] = useState(null); // null, 'hive', or 'elite'
    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);
    const fileInputRef = useRef(null);
    const [currentModel, setCurrentModel] = useState(null);
    const [thinkingEnabled, setThinkingEnabled] = useState(false);
    const [supportsThinking, setSupportsThinking] = useState(false);
    const [webSearchEnabled, setWebSearchEnabled] = useState(false);

    // Scout state
    const [scoutResult, setScoutResult] = useState(null);
    const [scoutLoading, setScoutLoading] = useState(false);
    const [pendingScoutMessage, setPendingScoutMessage] = useState(null);

    // Model-specific file support configuration
    const MODEL_FILE_SUPPORT = {
        'gemini-3-pro-preview': {
            accept: 'image/*,video/*,audio/*,.pdf,.txt,.md',
            types: ['image/', 'video/', 'audio/', 'application/pdf', 'text/plain', 'text/markdown'],
            description: 'Images, Video, Audio, PDF, Text'
        },
        'gemini-2.5-pro': {
            accept: 'image/*,video/*,audio/*,.pdf,.txt,.md',
            types: ['image/', 'video/', 'audio/', 'application/pdf', 'text/plain', 'text/markdown'],
            description: 'Images, Video, Audio, PDF, Text'
        },
        'gemini-3-flash-preview': {
            accept: 'image/*,video/*,audio/*,.txt,.md',
            types: ['image/', 'video/', 'audio/', 'text/plain', 'text/markdown'],
            description: 'Images, Video, Audio, Text'
        },
        'gemini-3.1-flash-lite-preview': {
            accept: 'image/*,video/*,audio/*,.pdf,.txt,.md',
            types: ['image/', 'video/', 'audio/', 'application/pdf', 'text/plain', 'text/markdown'],
            description: 'Images, Video, Audio, PDF, Text'
        },
        'gpt-5': {
            accept: 'image/*,.txt,.md',
            types: ['image/', 'text/plain', 'text/markdown'],
            description: 'Images, Text'
        },
        'gpt-5-mini': {
            accept: 'image/*,.txt,.md',
            types: ['image/', 'text/plain', 'text/markdown'],
            description: 'Images, Text'
        },
        'gpt-5-nano': {
            accept: 'image/*,.txt,.md',
            types: ['image/', 'text/plain', 'text/markdown'],
            description: 'Images, Text'
        },
        'gpt-5.1': {
            accept: 'image/*,.txt,.md',
            types: ['image/', 'text/plain', 'text/markdown'],
            description: 'Images, Text'
        },
        'claude-sonnet-4-5': {
            accept: 'image/*,.pdf,.txt,.md',
            types: ['image/', 'application/pdf', 'text/plain', 'text/markdown'],
            description: 'Images, PDF, Text'
        },
        'claude-haiku-4-5': {
            accept: 'image/*,.pdf,.txt,.md',
            types: ['image/', 'application/pdf', 'text/plain', 'text/markdown'],
            description: 'Images, PDF, Text'
        },
        'claude-opus-4-5': {
            accept: 'image/*,.pdf,.txt,.md',
            types: ['image/', 'application/pdf', 'text/plain', 'text/markdown'],
            description: 'Images, PDF, Text'
        },
        'gpt-5.2': {
            accept: 'image/*,.txt,.md',
            types: ['image/', 'text/plain', 'text/markdown'],
            description: 'Images, Text'
        },
        'grok-4': {
            accept: 'image/*,.txt,.md',
            types: ['image/', 'text/plain', 'text/markdown'],
            description: 'Images, Text'
        },
        'grok-4.1-fast': {
            accept: 'image/*,.txt,.md',
            types: ['image/', 'text/plain', 'text/markdown'],
            description: 'Images, Text'
        },
        'deepseek-v3.2-speciale': {
            accept: '.txt,.md',
            types: ['text/plain', 'text/markdown'],
            description: 'Text only'
        }
    };

    // Load current model/provider from settings
    useEffect(() => {
        const loadSettings = async () => {
            try {
                const settings = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5001'}/api/config`).then(r => r.json());
                setCurrentModel(settings.default_model);

                // Check if current model supports thinking
                const provider = settings.default_provider;
                const modelData = settings.providers?.[provider]?.find(m =>
                    (typeof m === 'object' ? m.id : m) === settings.default_model
                );
                setSupportsThinking(typeof modelData === 'object' && modelData.thinking === true);
            } catch (error) {
                console.error('Failed to load settings:', error);
                // Fallback
                setCurrentModel('gemini-3-flash-preview');
                setSupportsThinking(false);
            }
        };
        loadSettings();

        // Listen for model changes from SettingsModal
        const handleModelChange = (event) => {
            setCurrentModel(event.detail.model);
            setSupportsThinking(event.detail.supportsThinking || false);
            // Reset thinking toggle when switching models
            if (!event.detail.supportsThinking) {
                setThinkingEnabled(false);
            }
        };
        window.addEventListener('modelChanged', handleModelChange);

        return () => {
            window.removeEventListener('modelChanged', handleModelChange);
        };
    }, []);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [input]);

    const getCurrentModelSupport = () => {
        return MODEL_FILE_SUPPORT[currentModel] || MODEL_FILE_SUPPORT['gemini-3-flash-preview'];
    };

    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files);
        const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
        const modelSupport = getCurrentModelSupport();
        const ALLOWED_TYPES = modelSupport.types;

        const validFiles = files.filter(file => {
            if (file.size > MAX_FILE_SIZE) {
                alert(`${file.name} is too large (max 10MB)`);
                return false;
            }
            // Check if file type matches any allowed type prefix
            const isAllowed = ALLOWED_TYPES.some(allowedType => {
                if (allowedType.endsWith('/')) {
                    return file.type.startsWith(allowedType);
                }
                return file.type === allowedType;
            });
            if (!isAllowed) {
                alert(`${file.name} type not supported by ${currentModel}.\nSupported: ${modelSupport.description}`);
                return false;
            }
            return true;
        });

        // Create preview URLs for images
        const processedFiles = validFiles.map(file => {
            const fileData = {
                name: file.name,
                size: file.size,
                type: file.type,
                file: file
            };

            if (file.type.startsWith('image/')) {
                fileData.preview = URL.createObjectURL(file);
            }

            return fileData;
        });

        setAttachedFiles(prev => [...prev, ...processedFiles]);
        e.target.value = ''; // Reset input
    };

    const handleRemoveFile = (index) => {
        setAttachedFiles(prev => {
            const newFiles = [...prev];
            if (newFiles[index].preview) {
                URL.revokeObjectURL(newFiles[index].preview);
            }
            newFiles.splice(index, 1);
            return newFiles;
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if ((input.trim() || attachedFiles.length > 0) && !isLoading) {
            let message = input.trim();

            // Prepend council command if mode is selected
            if (councilMode === 'hive') {
                message = `/hive ${message}`;
            } else if (councilMode === 'elite') {
                message = `/elite ${message}`;
            } else if (councilMode === 'mega') {
                message = `/mega ${message}`;
            }

            // Build reasoning config if thinking is enabled
            const reasoningConfig = thinkingEnabled && supportsThinking
                ? { enabled: true }
                : null;

            // If web search is enabled, run Scout first to get recommendation
            if (webSearchEnabled && !councilMode) {
                setScoutLoading(true);
                try {
                    const scout = await scoutAnalyze(message, messages);
                    console.log('🕵️ Scout result:', scout);

                    if (scout.decision === 'NO_SEARCH') {
                        // No search needed - proceed with normal chat (no web search)
                        setScoutLoading(false);
                        onSendMessage(message, attachedFiles, reasoningConfig, false);
                        setInput('');
                        setWebSearchEnabled(false);
                        attachedFiles.forEach(file => {
                            if (file.preview) URL.revokeObjectURL(file.preview);
                        });
                        setAttachedFiles([]);
                        return;
                    } else if (scout.decision === 'FORCE_SEARCH') {
                        // Auto-search with Grok (budget protection)
                        setScoutLoading(false);
                        onSendMessage(message, attachedFiles, reasoningConfig, true, 'grok');
                        setInput('');
                        setWebSearchEnabled(false);
                        attachedFiles.forEach(file => {
                            if (file.preview) URL.revokeObjectURL(file.preview);
                        });
                        setAttachedFiles([]);
                        return;
                    } else {
                        // SUGGEST_SEARCH - show card for user decision
                        setScoutResult(scout);
                        setPendingScoutMessage({ message, files: attachedFiles, reasoningConfig });
                        setInput('');
                        setScoutLoading(false);
                        return;
                    }
                } catch (error) {
                    console.error('Scout analysis failed:', error);
                    setScoutLoading(false);
                    // Fall through to regular web search
                }
            }

            onSendMessage(message, attachedFiles, reasoningConfig, webSearchEnabled);
            setInput('');
            setCouncilMode(null); // Reset council mode after sending
            setWebSearchEnabled(false); // Reset web search after sending
            // Clean up preview URLs
            attachedFiles.forEach(file => {
                if (file.preview) URL.revokeObjectURL(file.preview);
            });
            setAttachedFiles([]);
        }
    };

    // Scout action handlers
    const handleScoutSearchWithGrok = () => {
        if (pendingScoutMessage) {
            onSendMessage(
                pendingScoutMessage.message,
                pendingScoutMessage.files,
                pendingScoutMessage.reasoningConfig,
                true, // webSearchEnabled
                'grok' // forceSearchModel
            );
            clearScoutState();
        }
    };

    const handleScoutSearchWithPerplexity = () => {
        if (pendingScoutMessage) {
            onSendMessage(
                pendingScoutMessage.message,
                pendingScoutMessage.files,
                pendingScoutMessage.reasoningConfig,
                true, // webSearchEnabled
                'perplexity' // forceSearchModel
            );
            clearScoutState();
        }
    };

    const handleScoutSkip = () => {
        if (pendingScoutMessage) {
            // Send without web search
            onSendMessage(
                pendingScoutMessage.message,
                pendingScoutMessage.files,
                pendingScoutMessage.reasoningConfig,
                false // webSearchEnabled = false (skip search)
            );
            clearScoutState();
        }
    };

    const clearScoutState = () => {
        setScoutResult(null);
        setPendingScoutMessage(null);
        setWebSearchEnabled(false);
        // Clean up files
        attachedFiles.forEach(file => {
            if (file.preview) URL.revokeObjectURL(file.preview);
        });
        setAttachedFiles([]);
    };

    const handleKeyDown = (e) => {
        // Submit on Enter (without Shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    // Dynamic Welcome Screen Logic
    const isLowEnergy = contextData?.energy < 30 ||
        (contextData?.focus && (contextData.focus.includes('Sairas') || contextData.focus.includes('Sick')));

    const handleActionClick = (action) => {
        onSendMessage(action);
    };

    return (
        <div className="chat">
            {messages.length === 0 ? (
                <div className={`chat-empty ${isLowEnergy ? 'low-energy' : ''}`}>
                    {isLowEnergy ? (
                        <>
                            <div className="system-alert">
                                <h2>⚠️ System Alert: Low Energy</h2>
                                <p>Recovery protocols recommended. Minimizing cognitive load.</p>
                            </div>
                            <div className="action-chips">
                                <button onClick={() => handleActionClick("Log current health status")}>📉 Log Health</button>
                                <button onClick={() => handleActionClick("Clear my schedule for today")}>📅 Clear Schedule</button>
                                <button onClick={() => handleActionClick("Find food delivery options")}>🍲 Food Delivery</button>
                            </div>
                        </>
                    ) : (
                        <>
                            <h2>KORTEX &gt;_ Online</h2>
                            <p>Systems nominal. Ready for /council.</p>
                            <p className="hint">Ask me anything about your life, projects, health, or routines.</p>
                        </>
                    )}
                </div>
            ) : (
                <div className="chat-messages">
                    {messages.map((msg, index) => (
                        msg.type === 'council' ?
                            (msg.councilType === 'mega' ?
                                <MegaView key={index} councilData={msg.councilData} /> :
                                <CouncilView key={index} councilData={msg.councilData} />) :
                            <Message key={index} message={msg} />
                    ))}
                    {councilLoading && (
                        <div className={`council-loading ${councilLoading}-loading`}>
                            <div className="loading-spinner"></div>
                            <p>
                                {councilLoading === 'hive'
                                    ? '🐝 Consulting Hive (6 personas analyzing...)'
                                    : councilLoading === 'mega'
                                        ? '🔥 MEGA Council Battle (Elite + Hive → Chairman...)'
                                        : '🏛️ Consulting Elite Council (3 models debating...)'}
                            </p>
                        </div>
                    )}
                    {isLoading && !councilLoading && <LoadingIndicator />}
                    <div ref={messagesEndRef} />
                </div>
            )}

            {/* Scout Card - shows when Scout has analyzed and is waiting for user decision */}
            {scoutResult && pendingScoutMessage && (() => {
                console.log('🎴 Rendering ScoutCard:', { scoutResult, pendingScoutMessage });
                return (
                    <ScoutCard
                        scoutResult={scoutResult}
                        onSearchWithGrok={handleScoutSearchWithGrok}
                        onSearchWithPerplexity={handleScoutSearchWithPerplexity}
                        onSkip={handleScoutSkip}
                        onClose={clearScoutState}
                    />
                );
            })()}

            <form className="chat-input-form" onSubmit={handleSubmit}>
                {attachedFiles.length > 0 && (
                    <FilePreview files={attachedFiles} onRemove={handleRemoveFile} />
                )}
                <div className="chat-input-wrapper">
                    <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept={getCurrentModelSupport().accept}
                        onChange={handleFileSelect}
                        style={{ display: 'none' }}
                    />
                    <div className="council-dropdown">
                        <button
                            type="button"
                            className={`council-toggle ${councilMode ? 'active' : ''}`}
                            title="Select council mode"
                            disabled={isLoading}
                            onClick={(e) => {
                                e.stopPropagation();
                                const dropdown = e.currentTarget.nextElementSibling;
                                dropdown.classList.toggle('show');
                            }}
                        >
                            {councilMode === 'hive' ? '🐝' : councilMode === 'elite' ? '🏛️' : councilMode === 'mega' ? '🔥' : '👥'}
                        </button>
                        <div className="council-menu">
                            <button
                                type="button"
                                onClick={() => {
                                    setCouncilMode(councilMode === 'hive' ? null : 'hive');
                                    document.querySelector('.council-menu').classList.remove('show');
                                }}
                                className={councilMode === 'hive' ? 'selected' : ''}
                            >
                                🐝 Hive
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setCouncilMode(councilMode === 'elite' ? null : 'elite');
                                    document.querySelector('.council-menu').classList.remove('show');
                                }}
                                className={councilMode === 'elite' ? 'selected' : ''}
                            >
                                🏛️ Elite
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setCouncilMode(councilMode === 'mega' ? null : 'mega');
                                    document.querySelector('.council-menu').classList.remove('show');
                                }}
                                className={councilMode === 'mega' ? 'selected' : ''}
                            >
                                🔥 MEGA
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setCouncilMode(null);
                                    document.querySelector('.council-menu').classList.remove('show');
                                }}
                                className={!councilMode ? 'selected' : ''}
                            >
                                💬 Standard
                            </button>
                        </div>
                    </div>
                    {supportsThinking && (
                        <button
                            type="button"
                            className={`thinking-toggle ${thinkingEnabled ? 'active' : ''}`}
                            title={thinkingEnabled ? 'Thinking mode enabled' : 'Enable thinking mode'}
                            disabled={isLoading}
                            onClick={() => setThinkingEnabled(!thinkingEnabled)}
                        >
                            🧠
                        </button>
                    )}
                    <button
                        type="button"
                        className={`web-search-toggle ${webSearchEnabled ? 'active' : ''}`}
                        title={webSearchEnabled ? 'Web Search enabled (Scout → Grok/Perplexity → Your Model)' : 'Enable Web Search'}
                        disabled={isLoading || scoutLoading}
                        onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                    >
                        {scoutLoading ? '🔄' : '🌐'}
                    </button>
                    <button
                        type="button"
                        className="chat-attach-button"
                        title="Attach file"
                        disabled={isLoading}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        📎
                    </button>
                    <textarea
                        ref={textareaRef}
                        className="chat-input"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type a message..."
                        rows={1}
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        className="chat-send-button"
                        disabled={!input.trim() || isLoading}
                    >
                        {isLoading ? '...' : '➤'}
                    </button>
                </div>
            </form>

            {/* Placeholder for FunctionCallModal - assuming it will be defined elsewhere */}
            {/* <FunctionCallModal 
                isOpen={showModal}
                toolCall={currentToolCall}
                onApprove={handleApproveTool}
                onReject={handleRejectTool}
            /> */}
        </div>
    );
};

export default Chat;
