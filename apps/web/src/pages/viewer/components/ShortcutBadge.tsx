import './ShortcutBadge.css';

interface ShortcutBadgeProps {
    display: string;
    visible: boolean;
}

export default function ShortcutBadge({ display, visible }: ShortcutBadgeProps) {
    if (!visible) return null;
    return <span className="shortcut-badge" aria-hidden="true">{display}</span>;
}