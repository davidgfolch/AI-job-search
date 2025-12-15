
import Messages from './Messages';

interface MessageContainerProps {
    message: { text: string; type: 'success' | 'error' } | null;
    error: unknown;
    onDismissMessage: () => void;
}

export default function MessageContainer({ message, error, onDismissMessage }: MessageContainerProps) {
    if (!message && !error) return null;

    const errorMessage = error instanceof Error ? error.message : String(error);

    return (
        <>
            {message && (
                <Messages message={message.text} type={message.type} onDismiss={onDismissMessage} />
            )}
            {error && (
                <Messages message={errorMessage} type="error" onDismiss={onDismissMessage} />
            )}
        </>
    );
}
