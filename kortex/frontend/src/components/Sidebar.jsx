import React, { useState, useEffect } from 'react';
import { getHistory, deleteConversation, pinConversation } from '../services/api';
import './Sidebar.css';

const Sidebar = ({ isOpen, onToggle, onSelectChat, onNewChat, onOpenSettings, contextData }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isOpen) {
            loadHistory();
        }
    }, [isOpen]);

    // Also reload when new messages are created - listen for chat updates
    useEffect(() => {
        const handleChatUpdate = () => {
            console.log('🔄 Reloading chat history...');
            loadHistory();
        };

        window.addEventListener('chatHistoryChanged', handleChatUpdate);

        // Also reload periodically if sidebar is open
        let interval;
        if (isOpen) {
            interval = setInterval(() => {
                loadHistory();
            }, 5000); // Reload every 5 seconds when sidebar is open
        }

        return () => {
            window.removeEventListener('chatHistoryChanged', handleChatUpdate);
            if (interval) clearInterval(interval);
        };
    }, [isOpen]);

    const handleDeleteChat = async (e, chatId, title) => {
        e.stopPropagation(); // Prevent selecting the chat
        if (window.confirm(`Are you sure you want to delete "${title}"?`)) {
            try {
                await deleteConversation(chatId);
                // Refresh history immediately
                loadHistory();
            } catch (error) {
                console.error('Failed to delete chat:', error);
                alert('Failed to delete chat');
            }
        }
    };

    const loadHistory = async () => {
        try {
            const data = await getHistory();
            setHistory(data);
        } catch (error) {
            console.error('Failed to load history:', error);
        } finally {
            setLoading(false);
        }
    };

    // Handle pin/unpin
    const handlePin = async (chatId, e) => {
        e.stopPropagation(); // Prevent chat selection
        try {
            await pinConversation(chatId);
            // Reload history to get updated pin status
            loadHistory();
        } catch (error) {
            console.error('Failed to pin conversation:', error);
        }
    };

    // Sort by lastModified (newest first)
    const sortByLastModified = (a, b) => {
        const aTime = a.lastModified || a.timestamp || 0;
        const bTime = b.lastModified || b.timestamp || 0;
        return bTime - aTime;
    };

    // Split history into pinned and recent
    const pinnedChats = history
        .filter(chat => chat.pinned)
        .sort(sortByLastModified);

    const recentChats = history
        .filter(chat => !chat.pinned)
        .sort(sortByLastModified);

    const groupedHistory = {
        ...(pinnedChats.length > 0 && { 'Pinned': pinnedChats }),
        'Recent': recentChats
    };

    return (
        <>
            <button
                className={`sidebar-toggle ${isOpen ? 'open' : ''}`}
                onClick={onToggle}
                aria-label="Toggle Sidebar"
            >
                {isOpen ? '✕' : '☰'}
            </button>

            <div className={`sidebar ${isOpen ? 'open' : ''}`}>
                {/* 1. HEADER: Logo Only */}
                <div className="sidebar-header">
                    <div className="sidebar-logo">
                        <div className="status-dot"></div>
                        <h1>KORTEX &gt;_</h1>
                    </div>
                    {/* Close button for mobile */}
                    <button
                        className="sidebar-close-mobile"
                        onClick={onToggle}
                        aria-label="Close Sidebar"
                    >
                        ✕
                    </button>
                </div>

                {/* 2. CONTEXT WIDGET: Separate section below header */}
                <div className="context-widget-wrapper">
                    <div className="live-context">
                        <div className="context-item">
                            <div className="context-row">
                                <span className="label">Energy</span>
                                <span className="value">{contextData.energy}%</span>
                            </div>
                            <div className="progress-bar">
                                <div className="progress" style={{ width: `${contextData.energy}%` }}></div>
                            </div>
                        </div>
                        <div className="context-item">
                            <span className="label">📍 Location</span>
                            <span className="value">{contextData.location}</span>
                        </div>
                        <div className="context-item">
                            <span className="label">🎯 Focus</span>
                            <span className="value">{contextData.focus}</span>
                        </div>
                    </div>
                </div>

                {/* 3. NAVIGATION (Scrollable) */}
                <div className="sidebar-content">
                    <button className="new-chat-btn" onClick={onNewChat}>
                        + New Chat
                    </button>

                    <div className="history-list">
                        {loading ? (
                            <div className="loading">Loading history...</div>
                        ) : (
                            Object.entries(groupedHistory).map(([group, items]) => (
                                <div key={group} className={`history-group ${group.toLowerCase()}-section`}>
                                    <h3>{group}</h3>
                                    {items.map(chat => (
                                        <div key={chat.id} className="history-item-wrapper">
                                            <button
                                                className="history-item"
                                                onClick={() => onSelectChat(chat.id)}
                                            >
                                                <span className="title">{chat.title}</span>
                                                <span className="preview">{chat.preview}</span>
                                            </button>
                                            <button
                                                className={`pin-chat-btn ${chat.pinned ? 'pinned' : ''}`}
                                                onClick={(e) => handlePin(chat.id, e)}
                                                title={chat.pinned ? "Unpin Chat" : "Pin Chat"}
                                            >
                                                📌
                                            </button>
                                            <button
                                                className="delete-chat-btn"
                                                onClick={(e) => handleDeleteChat(e, chat.id, chat.title)}
                                                title="Delete Chat"
                                            >
                                                ×
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            ))
                        )}
                    </div>
                </div>

                <div className="sidebar-footer">
                    <button className="settings-btn" onClick={onOpenSettings}>
                        ⚙️ System Data
                    </button>
                </div>
            </div>
        </>
    );
};

export default Sidebar;
