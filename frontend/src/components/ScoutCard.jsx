/**
 * ScoutCard - Shows Scout analysis and search options
 */

import React from 'react';
import './ScoutCard.css';

const ScoutCard = ({ 
  scoutResult, 
  onSearchWithGrok, 
  onSearchWithPerplexity, 
  onSkip,
  onClose 
}) => {
  if (!scoutResult) return null;

  const { decision, confidence, search_type, reason, recommended_model } = scoutResult;
  
  // Don't show card for NO_SEARCH or FORCE_SEARCH (quiet mode)
  if (decision === 'NO_SEARCH' || decision === 'FORCE_SEARCH') {
    return null;
  }

  const isGrokRecommended = recommended_model?.includes('grok');
  return (
    <div className="scout-card">
      <div className="scout-card-header">
        <span className="scout-icon">🕵️</span>
        <span className="scout-title">Scout</span>
        <span className={`scout-confidence ${confidence >= 80 ? 'high' : 'medium'}`}>
          {confidence}%
        </span>
        <button className="scout-close" onClick={onClose}>×</button>
      </div>
      
      <div className="scout-card-body">
        <p className="scout-reason">{reason}</p>
        
        <div className="scout-recommendation">
          {search_type === 'NEWS' ? (
            <span className="scout-type news">📰 Uutiset/X</span>
          ) : (
            <span className="scout-type research">🔬 Tutkimus</span>
          )}
          <span className="scout-suggests">
            Suositus: {isGrokRecommended ? 'Grok' : 'Perplexity'}
          </span>
        </div>
      </div>
      
      <div className="scout-card-actions">
        {/* Show recommended option first and highlighted */}
        {isGrokRecommended ? (
          <>
            <button 
              className="scout-btn primary" 
              onClick={onSearchWithGrok}
            >
              🐦 Hae Grokilla
            </button>
            <button 
              className="scout-btn secondary" 
              onClick={onSearchWithPerplexity}
            >
              🔬 Perplexity
            </button>
          </>
        ) : (
          <>
            <button 
              className="scout-btn primary" 
              onClick={onSearchWithPerplexity}
            >
              🔬 Hae Perplexityllä
            </button>
            <button 
              className="scout-btn secondary" 
              onClick={onSearchWithGrok}
            >
              🐦 Grok
            </button>
          </>
        )}
        <button 
          className="scout-btn skip" 
          onClick={onSkip}
        >
          💬 Ohita
        </button>
      </div>
    </div>
  );
};

export default ScoutCard;
