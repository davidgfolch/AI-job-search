import { useState } from 'react';
import { Modal } from '../../common/components/core/Modal';
import { SHORTCUT_ACTIONS, type ShortcutAction, type ShortcutCombo } from '../shortcutsConfig';
import './ShortcutsControls.css';

interface PinnedShortcut {
    name: string;
    index: number;
}

interface ShortcutsControlsProps {
    enabled: boolean;
    onToggle: () => void;
    shortcuts: Record<ShortcutAction, ShortcutCombo>;
    pinnedShortcuts?: PinnedShortcut[];
}

export default function ShortcutsControls({ enabled, onToggle, shortcuts, pinnedShortcuts = [] }: ShortcutsControlsProps) {
    const [showHelp, setShowHelp] = useState(false);
    return (
        <div className="shortcuts-controls">
            <button className="shortcuts-button" onClick={onToggle} aria-pressed={enabled} title={`Keyboard shortcuts ${enabled ? 'enabled' : 'disabled'}`}>
                ⌨
            </button>
            <button className="shortcuts-button" onClick={() => setShowHelp(true)} title="Show keyboard shortcuts">
                ?
            </button>
            <Modal isOpen={showHelp} onClose={() => setShowHelp(false)} title="Keyboard shortcuts">
                <table className="shortcuts-table">
                    <thead>
                        <tr><th>Action</th><th>Shortcut</th></tr>
                    </thead>
                    <tbody>
                        {SHORTCUT_ACTIONS.map(info => (
                            <tr key={info.action}>
                                <td>
                                    <strong>{info.label}</strong>
                                    <div className="shortcuts-description">{info.description}</div>
                                </td>
                                <td><kbd>{shortcuts[info.action].display}</kbd></td>
                            </tr>
                        ))}
                        {pinnedShortcuts.length > 0 && (
                            <tr className="shortcuts-section-header">
                                <td colSpan={2}>
                                    <strong>Load pinned filters:</strong>
                                </td>
                            </tr>
                        )}
                        {pinnedShortcuts.map(s => (
                            <tr key={s.index}>
                                <td>{s.name}</td>
                                <td><kbd>Alt+{s.index}</kbd></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </Modal>
        </div>
    );
}
