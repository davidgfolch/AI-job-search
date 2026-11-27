import { Modal } from './Modal';
import ToggleSwitch from './ToggleSwitch';
import './ShortcutsPopup.css';

export interface ShortcutRow {
    label: string;
    description: string;
    display: string;
}

export interface PinnedShortcutRow {
    name: string;
    display: string;
}

export interface ShortcutsPopupProps {
    isOpen: boolean;
    onClose: () => void;
    enabled: boolean;
    onToggle: () => void;
    shortcuts: ShortcutRow[];
    pinnedShortcuts?: PinnedShortcutRow[];
}

export type ShortcutsMenuData = Omit<ShortcutsPopupProps, 'isOpen' | 'onClose'>;

export default function ShortcutsPopup({ isOpen, onClose, enabled, onToggle, shortcuts, pinnedShortcuts = [] }: ShortcutsPopupProps) {
    const header = (
        <>
            <h3>Keyboard shortcuts</h3>
            <div className="header-actions">
                <ToggleSwitch checked={enabled} onChange={onToggle} label={`Keyboard shortcuts ${enabled ? 'enabled' : 'disabled'}`} labelText={enabled ? 'On' : 'Off'} />
            </div>
        </>
    );
    return (
        <Modal isOpen={isOpen} onClose={onClose} header={header}>
            <table className="shortcuts-table">
                <thead>
                    <tr><th>Action</th><th>Shortcut</th></tr>
                </thead>
                <tbody>
                    {shortcuts.map(info => (
                        <tr key={info.label}>
                            <td>
                                <strong>{info.label}</strong>
                                <div className="shortcuts-description">{info.description}</div>
                            </td>
                            <td><kbd>{info.display}</kbd></td>
                        </tr>
                    ))}
                    {pinnedShortcuts.length > 0 && (
                        <tr className="shortcuts-section-header">
                            <td colSpan={2}><strong>Load pinned filters:</strong></td>
                        </tr>
                    )}
                    {pinnedShortcuts.map(info => (
                        <tr key={info.display}>
                            <td>{info.name}</td>
                            <td><kbd>{info.display}</kbd></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </Modal>
    );
}
