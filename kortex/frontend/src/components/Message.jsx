/**
 * Message Component - Individual chat message bubble
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import './Message.css';

const Message = ({ message }) => {
    const isUser = message.role === 'user';

    return (
        <div className={`message ${isUser ? 'user' : 'assistant'}`}>
            <div className="message-avatar">
                {isUser ? '👤' : '🤖'}
            </div>
            <div className="message-content">
                {isUser ? (
                    <p>{message.content}</p>
                ) : (
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                )}
            </div>
        </div>
    );
};

export default Message;
