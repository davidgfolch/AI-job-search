import { useState } from 'react';
import { Modal } from '../../common/components/core/Modal';
import { SHORTCUT_ACTIONS, type ShortcutAction, type ShortcutCombo } from '../shortcutsConfig';
import './ShortcutsControls.css';

interface ShortcutsControlsProps {
    enabled: boolean;
    onToggle: () => void;
    shortcuts: Record<ShortcutAction, ShortcutCombo>;
}

export default function ShortcutsControls({ enabled, onToggle, shortcuts }: ShortcutsControlsProps) {
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
                    </tbody>
                </table>
            </Modal>
        </div>
    );
}
