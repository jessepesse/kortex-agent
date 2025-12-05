import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './MegaView.css';

const MegaView = ({ councilData }) => {
    const [showElite, setShowElite] = useState(false);
    const [showHive, setShowHive] = useState(false);

    if (!councilData) return null;

    const { elite_winner, hive_winner, mega_verdict } = councilData;

    return (
        <div className="mega-view">
            <div className="mega-header">
                <h3>🔥 MEGA COUNCIL VERDICT</h3>
                <p className="mega-subtitle">Elite + Hive → Ultimate Chairman</p>
            </div>

            {/* Mega Chairman Verdict (always visible) */}
            <div className="mega-verdict">
                <div className="verdict-header">
                    <span className="verdict-icon">👑</span>
                    <h4>Ultimate Chairman's Decision</h4>
                </div>
                <div className="verdict-content">
                    <ReactMarkdown>{mega_verdict}</ReactMarkdown>
                </div>
            </div>

            {/* Elite Winner (collapsed) */}
            <div className="council-section">
                <button
                    className="collapse-toggle"
                    onClick={() => setShowElite(!showElite)}
                >
                    <span>{showElite ? '▼' : '▶'}</span>
                    <span className="toggle-icon">🏛️</span>
                    <span>Elite Council Winner: {elite_winner?.winner_model}</span>
                    <span className="vote-count">({elite_winner?.votes?.[elite_winner.winner_model] || 0} votes)</span>
                </button>

                {showElite && (
                    <div className="collapse-content elite-content">
                        <ReactMarkdown>{elite_winner?.winner_response}</ReactMarkdown>
                    </div>
                )}
            </div>

            {/* Hive Winner (collapsed) */}
            <div className="council-section">
                <button
                    className="collapse-toggle"
                    onClick={() => setShowHive(!showHive)}
                >
                    <span>{showHive ? '▼' : '▶'}</span>
                    <span className="toggle-icon">🐝</span>
                    <span>Hive Council Winner: {hive_winner?.winner_model}</span>
                    <span className="vote-count">({hive_winner?.votes?.[hive_winner.winner_model] || 0} votes)</span>
                </button>

                {showHive && (
                    <div className="collapse-content hive-content">
                        <ReactMarkdown>{hive_winner?.winner_response}</ReactMarkdown>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MegaView;
