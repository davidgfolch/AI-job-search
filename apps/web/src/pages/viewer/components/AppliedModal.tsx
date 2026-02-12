import { useState, useRef, useEffect } from 'react';
import { useAutoResizeTextArea } from '../../common/hooks/useAutoResizeTextArea';
import '../../common/components/core/ConfirmModal.css';

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

    // Auto-resize textarea
    useAutoResizeTextArea(textareaRef, comment, [isOpen]);

    // Reset form when modal opens
    useEffect(() => {
        if (isOpen) {
            setComment(defaultComment);
            // Focus textarea after a short delay to ensure modal is rendered
            setTimeout(() => {
                textareaRef.current?.focus();
            }, 50);
        }
    }, [isOpen, defaultComment]);

    // Handle keyboard events
    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onConfirm(true, comment);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                onConfirm(false, '');
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, comment, onConfirm]);

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">Mark as Applied</div>
                <div className="modal-body">
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
                        Press Enter to confirm with comment, Esc to confirm without comment
                    </div>
                </div>
                <div className="modal-footer">
                    <button 
                        className="modal-button cancel" 
                        onClick={() => onConfirm(false, '')}
                    >
                        Don't set (Esc)
                    </button>
                    <button 
                        className="modal-button confirm" 
                        onClick={() => onConfirm(true, comment)}
                    >
                        OK
                    </button>
                </div>
            </div>
        </div>
    );
}