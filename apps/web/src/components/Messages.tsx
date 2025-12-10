import './Messages.css';

interface MessagesProps {
    message: string;
    type: 'success' | 'error';
    onDismiss: () => void;
}

export default function Messages({ message, type, onDismiss }: MessagesProps) {
    return (
        <div className={`message ${type}`} onClick={onDismiss}>
            {message}
        </div>
    );
}
