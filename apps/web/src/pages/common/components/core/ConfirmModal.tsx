import { useEffect } from 'react';
import { Modal } from './Modal';
import './Modal.css';

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
    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                onConfirm();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onConfirm]);

    return (
        <Modal isOpen={isOpen} onClose={onCancel} title={title} closeOnEscape>
            {message}
            <div className="modal-footer">
                <button className="modal-button cancel" onClick={onCancel}>Cancel</button>
                <button className="modal-button confirm" onClick={onConfirm}>Confirm</button>
            </div>
        </Modal>
    );
}
