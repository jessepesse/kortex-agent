/**
 * ChatMessages - Message list rendering component
 */

import React from 'react';
import Message from '../Message';
import CouncilView from '../CouncilView';
import MegaView from '../MegaView';
import LoadingIndicator from '../LoadingIndicator';

const ChatMessages = ({
    messages,
    isLoading,
    councilLoading,
    messagesEndRef
}) => {
    return (
        <div className="messages-container">
            {messages.length === 0 ? (
                <div className="empty-state">
                    <h2>🧠 Kortex Agent</h2>
                    <p>Your personal AI assistant with memory</p>
                    <div className="quick-actions">
                        <button onClick={() => window.dispatchEvent(new CustomEvent('quickAction', { detail: 'What can you help me with?' }))}>
                            💡 What can you do?
                        </button>
                        <button onClick={() => window.dispatchEvent(new CustomEvent('quickAction', { detail: 'Tell me about my current goals' }))}>
                            🎯 My Goals
                        </button>
                        <button onClick={() => window.dispatchEvent(new CustomEvent('quickAction', { detail: 'How am I doing today?' }))}>
                            ❤️ Check-in
                        </button>
                    </div>
                </div>
            ) : (
                messages.map((msg, idx) => {
                    // Council message
                    if (msg.type === 'council') {
                        if (msg.councilType === 'mega') {
                            return <MegaView key={idx} data={msg.councilData} />;
                        }
                        return (
                            <CouncilView
                                key={idx}
                                data={msg.councilData}
                                type={msg.councilType}
                            />
                        );
                    }
                    // Regular message
                    return <Message key={idx} message={msg} />;
                })
            )}

            {/* Loading indicators */}
            {councilLoading && (
                <LoadingIndicator type={councilLoading} />
            )}
            {isLoading && !councilLoading && (
                <div className="loading-message">
                    <span className="typing-indicator">⏳ Thinking...</span>
                </div>
            )}

            <div ref={messagesEndRef} />
        </div>
    );
};

export default ChatMessages;
