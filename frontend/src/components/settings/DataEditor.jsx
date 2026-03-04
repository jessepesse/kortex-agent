/**
 * DataEditor - JSON data file editor component
 */

import React from 'react';

const DataEditor = ({
    dataFiles,
    selectedFile,
    onSelectFile
}) => {
    return (
        <>
            <h3>Data Files</h3>
            <div className="file-list">
                {Object.keys(dataFiles).map(filename => (
                    <button
                        key={filename}
                        className={`file-btn ${selectedFile === filename ? 'active' : ''}`}
                        onClick={() => onSelectFile(filename)}
                    >
                        {filename}.json
                    </button>
                ))}
            </div>
        </>
    );
};

export const DataEditorPanel = ({ jsonContent, onJsonChange }) => {
    return (
        <div className="editor-container">
            <textarea
                value={jsonContent}
                onChange={(e) => onJsonChange(e.target.value)}
                spellCheck="false"
            />
        </div>
    );
};

export default DataEditor;
