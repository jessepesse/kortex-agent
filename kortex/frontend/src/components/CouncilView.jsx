import React from 'react';
import ReactMarkdown from 'react-markdown';
import './CouncilView.css';

const CouncilView = ({ councilData, isLoading }) => {
    if (isLoading) {
        return (
            <div className="council-view loading">
                <div className="council-grid">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="council-card loading-card">
                            <div className="loading-spinner"></div>
                            <p>Consulting Council Member {i}...</p>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (!councilData) return null;

    const { council_responses, chairman_response, council_type } = councilData;
    const isHive = council_type === 'hive';

    return (
        <div className={`council-view ${isHive ? 'hive-mode' : 'elite-mode'}`}>
            <div className="council-header">
                <h3>{isHive ? '🐝 The Hive Has Spoken' : '🏛️ The Council Has Spoken'}</h3>
            </div>

            <div className="council-grid">
                {council_responses.map((member, index) => (
                    <div key={index} className={`council-card ${member.status}`}>
                        <div className="member-header">
                            <span className="member-icon">🤖</span>
                            <span className="member-name">{member.model}</span>
                        </div>
                        <div className="member-content">
                            <ReactMarkdown>{member.response}</ReactMarkdown>
                        </div>
                    </div>
                ))}
            </div>

            {/* Peer Reviews Section (Anonymous) */}
            {councilData.peer_reviews && councilData.peer_reviews.length > 0 && (
                <div className="peer-reviews-section">
                    <div className="peer-reviews-header">
                        <span className="review-icon">🔍</span>
                        <h4>Anonymous Peer Reviews</h4>
                    </div>
                    <div className="peer-reviews-grid">
                        {councilData.peer_reviews.map((review, index) => (
                            <div key={index} className="peer-review-card">
                                <div className="reviewer-label">{review.reviewer}</div>
                                <div className="review-content">
                                    <ReactMarkdown>{review.review}</ReactMarkdown>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="chairman-verdict">
                <div className="chairman-header">
                    <span className="chairman-icon">👑</span>
                    <h4>Chairman's Verdict</h4>
                </div>
                <div className="chairman-content">
                    <ReactMarkdown>{chairman_response}</ReactMarkdown>
                </div>
            </div>
        </div>
    );
};

export default CouncilView;
