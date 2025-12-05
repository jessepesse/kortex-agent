/**
 * FunctionCallModal Component - Approve/reject function calls
 */

import React from 'react';
import './FunctionCallModal.css';

const FunctionCallModal = ({ functionCalls, onApprove, onReject }) => {
    if (!functionCalls || functionCalls.length === 0) {
        return null;
    }

    const formatFunctionName = (name) => {
        return name.replace('update_', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    return (
        <div className="modal-overlay">
            <div className="modal">
                <div className="modal-header">
                    <h2>🔧 Function Call Approval</h2>
                </div>

                <div className="modal-content">
                    <p className="modal-description">
                        AI wants to update the following data:
                    </p>

                    {functionCalls.map((fc, idx) => (
                        <div key={idx} className="function-call">
                            <h3>📝 {formatFunctionName(fc.name)}</h3>
                            <pre className="function-call-data">
                                {JSON.stringify(fc.args.data || fc.args, null, 2)}
                            </pre>
                        </div>
                    ))}
                </div>

                <div className="modal-actions">
                    <button className="modal-button modal-button-reject" onClick={onReject}>
                        ✗ Reject
                    </button>
                    <button className="modal-button modal-button-approve" onClick={onApprove}>
                        ✓ Approve
                    </button>
                </div>
            </div>
        </div>
    );
};

export default FunctionCallModal;
