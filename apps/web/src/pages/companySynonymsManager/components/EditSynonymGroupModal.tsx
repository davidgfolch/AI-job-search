import { useState, useEffect, useRef } from 'react';
import { Modal } from '../../common/components/core/Modal';

interface EditSynonymGroupModalProps {
  groupId?: number;
  existingNames?: string[];
  onSave: (names: string[]) => void;
  onClose: () => void;
}

export function EditSynonymGroupModal({ groupId, onSave, onClose }: EditSynonymGroupModalProps) {
  const [names, setNames] = useState<string[]>(['', '']);
  const namesRef = useRef(names);
  const onSaveRef = useRef(onSave);
  useEffect(() => { namesRef.current = names; }, [names]);
  useEffect(() => { onSaveRef.current = onSave; }, [onSave]);

  const updateName = (index: number, value: string) => {
    const updated = [...names];
    updated[index] = value;
    setNames(updated);
  };

  const addRow = () => setNames([...names, '']);

  const removeRow = (index: number) => {
    if (names.length <= 2) return;
    setNames(names.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    const filtered = names.map(n => n.trim()).filter(Boolean);
    if (filtered.length >= 2) {
      onSave(filtered);
    }
  };

  const valid = names.filter(n => n.trim()).length >= 2;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const current = namesRef.current;
      const filtered = current.map(n => n.trim()).filter(Boolean);
      if (e.key === 'Enter' && filtered.length >= 2) {
        e.preventDefault();
        onSaveRef.current(filtered);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <Modal isOpen={true} onClose={onClose}>
      <div className="modal-content">
        <h2>{groupId ? 'Add Synonym' : 'New Synonym Group'}</h2>
        {names.map((name, i) => (
          <div key={i} className="synonym-input-row">
            <input
              type="text"
              value={name}
              onChange={(e) => updateName(i, e.target.value)}
              placeholder={`Company name ${i + 1}`}
              className="form-input"
              autoFocus={i === names.length - 1}
            />
            {names.length > 2 && (
              <button className="btn-danger btn-small" onClick={() => removeRow(i)}>×</button>
            )}
          </div>
        ))}
        <button className="btn-secondary" onClick={addRow}>+ Add another</button>
        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSubmit} disabled={!valid}>Save</button>
        </div>
      </div>
    </Modal>
  );
}
