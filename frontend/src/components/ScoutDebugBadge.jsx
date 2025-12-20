/**
 * ScoutDebugBadge - Shows Scout recommendation vs used model for FORCE searches
 */

import React from 'react';
import './ScoutCard.css';

const ScoutDebugBadge = ({ scoutInfo }) => {
  if (!scoutInfo || !scoutInfo.override_reason) return null;

  const { recommended_model, used_model, search_type, confidence } = scoutInfo;
  
  // Extract model names for display
  const recommendedName = recommended_model?.includes('perplexity') ? 'Perplexity' : 'Grok';
  const usedName = used_model?.includes('perplexity') ? 'Perplexity' : 'Grok';

  return (
    <div className="scout-debug-badge">
      <span>🕵️ Scout {confidence}%:</span>
      <span className="recommended">Suositus: {recommendedName}</span>
      <span>→</span>
      <span className="used">Käytetty: {usedName}</span>
      <span className={`scout-type ${search_type?.toLowerCase()}`}>
        {search_type === 'NEWS' ? '📰' : '🔬'}
      </span>
    </div>
  );
};

export default ScoutDebugBadge;
