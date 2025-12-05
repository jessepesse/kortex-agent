import React from 'react';
import './FilePreview.css';

const FilePreview = ({ files, onRemove }) => {
    if (!files || files.length === 0) return null;

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    const getFileIcon = (type) => {
        if (type.startsWith('image/')) return '🖼️';
        if (type === 'application/pdf') return '📄';
        if (type.startsWith('text/')) return '📝';
        return '📎';
    };

    return (
        <div className="file-preview-container">
            {files.map((file, index) => (
                <div key={index} className="file-preview-item">
                    {file.type.startsWith('image/') ? (
                        <img
                            src={file.preview}
                            alt={file.name}
                            className="file-preview-image"
                        />
                    ) : (
                        <div className="file-preview-icon">
                            {getFileIcon(file.type)}
                        </div>
                    )}
                    <div className="file-preview-info">
                        <span className="file-preview-name">{file.name}</span>
                        <span className="file-preview-size">{formatFileSize(file.size)}</span>
                    </div>
                    <button
                        className="file-preview-remove"
                        onClick={() => onRemove(index)}
                        aria-label="Remove file"
                    >
                        ✕
                    </button>
                </div>
            ))}
        </div>
    );
};

export default FilePreview;
