import React from 'react';
import './ConfirmModal.css';

interface ConfirmModalProps {
    isOpen: boolean;
    title?: string;
    message: string;
    onConfirm: () => void;
    onCancel: () => void;
}

export default function ConfirmModal({ 
    isOpen, 
    title = 'Confirm', 
    message, 
    onConfirm, 
    onCancel 
}: ConfirmModalProps) {
    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (isOpen && (e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                onConfirm();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onConfirm]);

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">{title}</div>
                <div className="modal-body">{message}</div>
                <div className="modal-footer">
                    <button className="modal-button cancel" onClick={onCancel}>Cancel</button>
                    <button className="modal-button confirm" onClick={onConfirm}>Confirm</button>
                </div>
            </div>
        </div>
    );
}
