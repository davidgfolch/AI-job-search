
import { useState } from 'react';
import Messages from '../Messages';

interface MessageContainerProps {
    message: { text: string; type: 'success' | 'error' } | null;
    error: unknown;
    onDismissMessage: () => void;
}

export default function MessageContainer({ message, error, onDismissMessage }: MessageContainerProps) {
    const [expanded, setExpanded] = useState(false);
    if (!message && !error) return null;

    const errorMessage = error instanceof Error ? error.message : String(error);
    const isLongError = error && errorMessage.length > 200;

    return (
        <>
            {message && (
                <Messages message={message.text} type={message.type} onDismiss={onDismissMessage} />
            )}
            {error && (
                <div onClick={() => isLongError && setExpanded(!expanded)} style={{ maxHeight: expanded ? 'none' : '5rem', overflow: 'hidden' }}>
                    <Messages message={errorMessage} type="error" onDismiss={onDismissMessage} />
                </div>
            )}
        </>
    );
}
