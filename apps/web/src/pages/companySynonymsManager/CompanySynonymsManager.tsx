import { useState } from 'react';
import { useCompanySynonyms } from './hooks/useCompanySynonyms';
import { CompanySynonymsTable } from './components/CompanySynonymsTable';
import { EditSynonymGroupModal } from './components/EditSynonymGroupModal';
import PageHeader from '../common/components/PageHeader';
import { type SynonymGroup } from './api/CompanySynonymsManagerApi';
import './CompanySynonymsManager.css';

const CompanySynonymsManager = () => {
  const { groups, isLoading, error, createGroup, addToGroup, removeName } = useCompanySynonyms();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [addToGroupId, setAddToGroupId] = useState<number | null>(null);

  const handleCreateGroup = async (names: string[]) => {
    await createGroup(names);
    setShowCreateModal(false);
  };

  const handleAddToGroup = async (names: string[]) => {
    if (addToGroupId != null && names.length > 0) {
      await addToGroup({ groupId: addToGroupId, name: names[0] });
      setAddToGroupId(null);
    }
  };

  const handleRemoveName = async (name: string) => {
    if (window.confirm(`Remove "${name}" from its synonym group?`)) {
      await removeName(name);
    }
  };

  const handleRemoveGroup = async (group: SynonymGroup) => {
    if (window.confirm(`Remove all names in group ${group.group_id} (${group.names.join(', ')})?`)) {
      for (const name of group.names) {
        await removeName(name);
      }
    }
  };

  return (
    <>
      <PageHeader title="Company Synonyms" />
      <div className="synonyms-manager">
        <div className="actions-group">
          <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
            + Add Synonym Group
          </button>
        </div>

        {error && <div className="error-message" style={{ color: 'red', margin: '10px 0' }}>{String(error)}</div>}
        {isLoading && <div className="loading-indicator">Loading synonym groups...</div>}

        {!isLoading && (
          <CompanySynonymsTable
            groups={groups}
            onAddToGroup={(gid) => setAddToGroupId(gid)}
            onRemoveName={handleRemoveName}
            onRemoveGroup={handleRemoveGroup}
          />
        )}

        {showCreateModal && (
          <EditSynonymGroupModal
            onSave={handleCreateGroup}
            onClose={() => setShowCreateModal(false)}
          />
        )}

        {addToGroupId != null && (
          <EditSynonymGroupModal
            groupId={addToGroupId}
            existingNames={groups.find(g => g.group_id === addToGroupId)?.names}
            onSave={handleAddToGroup}
            onClose={() => setAddToGroupId(null)}
          />
        )}
      </div>
    </>
  );
};

export default CompanySynonymsManager;
