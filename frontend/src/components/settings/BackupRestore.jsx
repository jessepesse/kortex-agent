/**
 * BackupRestore - Backup download and restore component
 */

import React, { useState } from 'react';
import { downloadBackup, validateBackup, restoreBackup } from '../../services/api';

const BackupRestore = ({
    conversations,
    selectedConversations,
    setSelectedConversations,
    setStatus,
    onDataReload
}) => {
    const [backupLoading, setBackupLoading] = useState(false);
    const [restoreFile, setRestoreFile] = useState(null);
    const [validationResult, setValidationResult] = useState(null);

    const toggleConversation = (id) => {
        setSelectedConversations(prev =>
            prev.includes(id)
                ? prev.filter(x => x !== id)
                : [...prev, id]
        );
    };

    const toggleAllConversations = () => {
        if (selectedConversations.length === conversations.length) {
            setSelectedConversations([]);
        } else {
            setSelectedConversations(conversations.map(c => c.id));
        }
    };

    const handleDownloadBackup = async () => {
        try {
            setBackupLoading(true);
            setStatus('Creating backup...');

            const convIds = selectedConversations.length === conversations.length
                ? null
                : selectedConversations.length === 0
                    ? []
                    : selectedConversations;

            const blob = await downloadBackup(convIds);

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `kortex_backup_${new Date().toISOString().split('T')[0]}.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            setStatus('✅ Backup downloaded!');
            setTimeout(() => setStatus(''), 3000);
        } catch (error) {
            setStatus(`❌ Error: ${error.message}`);
        } finally {
            setBackupLoading(false);
        }
    };

    const handleFileSelect = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setRestoreFile(file);
        setStatus('Validating backup...');

        try {
            const result = await validateBackup(file);
            setValidationResult(result);
            setStatus(result.valid ? '✅ Backup is valid' : '❌ Backup validation failed');
        } catch (error) {
            setValidationResult({ valid: false, errors: [error.message] });
            setStatus('❌ Validation error');
        }
    };

    const handleRestore = async () => {
        if (!restoreFile || !validationResult?.valid) return;

        const confirmed = window.confirm(
            '⚠️ VAROITUS!\n\n' +
            'Tämä toiminto YLIKIRJOITTAA kaiken nykyisen datan.\n' +
            'Tätä ei voi peruuttaa!\n\n' +
            'Haluatko varmasti jatkaa?'
        );

        if (!confirmed) return;

        try {
            setBackupLoading(true);
            setStatus('Restoring backup...');

            const result = await restoreBackup(restoreFile);

            if (result.success) {
                setStatus(`✅ Restored ${result.restored_files.length} files!`);
                await onDataReload();
                setRestoreFile(null);
                setValidationResult(null);
            } else {
                setStatus(`❌ Restore failed: ${result.errors.join(', ')}`);
            }
        } catch (error) {
            setStatus(`❌ Error: ${error.message}`);
        } finally {
            setBackupLoading(false);
        }
    };

    return (
        <div className="backup-container">
            {/* Download Backup */}
            <div className="backup-section">
                <h3>📥 Lataa varmuuskopio</h3>
                <p className="backup-desc">
                    Lataa kaikki datasi ZIP-tiedostona. Valitse mitkä keskustelut otetaan mukaan.
                </p>

                <div className="conversation-selector">
                    <label className="checkbox-label select-all">
                        <input
                            type="checkbox"
                            checked={selectedConversations.length === conversations.length && conversations.length > 0}
                            onChange={toggleAllConversations}
                        />
                        <span>Valitse kaikki keskustelut ({conversations.length})</span>
                    </label>

                    <div className="conversation-list">
                        {conversations.map(conv => (
                            <label key={conv.id} className="checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={selectedConversations.includes(conv.id)}
                                    onChange={() => toggleConversation(conv.id)}
                                />
                                <span className="conv-title">
                                    {conv.pinned && '📌 '}
                                    {conv.title}
                                </span>
                            </label>
                        ))}
                    </div>
                </div>

                <button
                    className="backup-btn download-btn"
                    onClick={handleDownloadBackup}
                    disabled={backupLoading}
                >
                    {backupLoading ? '⏳ Creating...' : '📥 Lataa Backup'}
                </button>
            </div>

            {/* Restore Backup */}
            <div className="backup-section restore-section">
                <h3>📤 Palauta varmuuskopiosta</h3>
                <p className="backup-desc warning">
                    ⚠️ Huomio: Palautus ylikirjoittaa kaiken nykyisen datan!
                </p>

                <input
                    type="file"
                    accept=".zip"
                    onChange={handleFileSelect}
                    className="file-input"
                    id="restore-file-input"
                />
                <label htmlFor="restore-file-input" className="file-input-label">
                    {restoreFile ? `📎 ${restoreFile.name}` : '📁 Valitse ZIP-tiedosto'}
                </label>

                {validationResult && (
                    <div className={`validation-result ${validationResult.valid ? 'valid' : 'invalid'}`}>
                        <div className="validation-header">
                            {validationResult.valid ? '✅ Validi backup' : '❌ Virheellinen backup'}
                        </div>
                        {validationResult.manifest && (
                            <div className="validation-details">
                                <span>📅 {new Date(validationResult.manifest.created_at).toLocaleString('fi-FI')}</span>
                                <span>📁 {validationResult.manifest.stats?.data_files || 0} datatiedostoa</span>
                                <span>💬 {validationResult.manifest.stats?.conversations || 0} keskustelua</span>
                            </div>
                        )}
                        {validationResult.errors?.length > 0 && (
                            <ul className="error-list">
                                {validationResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                            </ul>
                        )}
                    </div>
                )}

                <button
                    className="backup-btn restore-btn"
                    onClick={handleRestore}
                    disabled={!validationResult?.valid || backupLoading}
                >
                    {backupLoading ? '⏳ Restoring...' : '⚠️ Palauta Backup'}
                </button>
            </div>
        </div>
    );
};

export default BackupRestore;
