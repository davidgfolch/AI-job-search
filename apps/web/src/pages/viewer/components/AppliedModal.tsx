import { useState, useRef, useEffect } from 'react';
import { useAutoResizeTextArea } from '../../common/hooks/useAutoResizeTextArea';
import { Modal } from '../../common/components/core/Modal';
import '../../common/components/core/Modal.css';

interface AppliedModalProps {
    isOpen: boolean;
    defaultComment: string;
    onConfirm: (includeComment: boolean, comment: string) => void;
    onCancel: () => void;
}

export default function AppliedModal({ 
    isOpen, 
    defaultComment, 
    onConfirm, 
    onCancel 
}: AppliedModalProps) {
    const [comment, setComment] = useState<string>('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useAutoResizeTextArea(textareaRef, comment, [isOpen]);

    useEffect(() => {
        if (isOpen) {
            setComment(defaultComment);
            setTimeout(() => {
                textareaRef.current?.focus();
            }, 50);
        }
    }, [isOpen, defaultComment]);

    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onConfirm(true, comment);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                onConfirm(true, '');
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, comment, onConfirm]);

    return (
        <Modal isOpen={isOpen} onClose={onCancel} title="Mark as Applied" closeOnEscape={false} fullWidthHeader={false}>
            <div style={{ marginBottom: '12px' }}>
                Add a comment (optional):
            </div>
            <textarea
                ref={textareaRef}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Enter comment..."
                style={{
                    width: '100%',
                    minHeight: '60px',
                    maxHeight: '200px',
                    padding: '8px',
                    border: '1px solid var(--border-color, #d1d5db)',
                    borderRadius: '4px',
                    fontFamily: 'inherit',
                    fontSize: '14px',
                    lineHeight: '1.4',
                    resize: 'none',
                    outline: 'none',
                    boxSizing: 'border-box'
                }}
            />
            <div style={{ 
                fontSize: '12px', 
                color: 'var(--text-secondary, #6b7280)', 
                marginTop: '4px' 
            }}>
                Press Enter to save comment, Esc to apply without comment
            </div>
            <div className="modal-footer">
                <button 
                    className="modal-button cancel" 
                    onClick={() => onConfirm(false, '')}
                >
                    Cancel
                </button>
                <button 
                    className="modal-button confirm" 
                    onClick={() => onConfirm(true, comment)}
                >
                    OK
                </button>
            </div>
        </Modal>
    );
}
