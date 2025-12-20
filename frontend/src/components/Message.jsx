/**
 * Message Component - Individual chat message bubble
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import './Message.css';

const Message = ({ message }) => {
    const isUser = message.role === 'user';
    
    // Handle content that might be a string or an object (e.g., API response)
    const getContent = (content) => {
        if (typeof content === 'string') {
            return content;
        }
        if (content && typeof content === 'object') {
            // If it's an API response object, extract the response field
            return content.response || content.error || JSON.stringify(content);
        }
        return String(content || '');
    };
    
    const content = getContent(message.content);

    return (
        <div className={`message ${isUser ? 'user' : 'assistant'}`}>
            <div className="message-avatar">
                {isUser ? '👤' : '🤖'}
            </div>
            <div className="message-content">
                {isUser ? (
                    <p>{content}</p>
                ) : (
                    <ReactMarkdown>{content}</ReactMarkdown>
                )}
            </div>
        </div>
    );
};

export default Message;
