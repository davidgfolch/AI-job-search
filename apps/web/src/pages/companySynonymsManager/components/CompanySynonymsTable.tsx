import { type SynonymGroup } from '../api/CompanySynonymsManagerApi';

interface CompanySynonymsTableProps {
  groups: SynonymGroup[];
  onAddToGroup: (groupId: number) => void;
  onRemoveName: (name: string) => void;
  onRemoveGroup: (group: SynonymGroup) => void;
}

export function CompanySynonymsTable({ groups, onAddToGroup, onRemoveName, onRemoveGroup }: CompanySynonymsTableProps) {
  return (
    <div className="synonyms-table-container">
      <table className="synonyms-table">
        <thead>
          <tr>
            <th>Group</th>
            <th>Company Names</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => (
            <tr key={group.group_id}>
              <td className="group-id-cell">{group.group_id}</td>
              <td className="names-cell">
                {group.names.map((name) => (
                  <span key={name} className="synonym-tag">
                    {name}
                    <button
                      className="synonym-tag-remove"
                      onClick={() => onRemoveName(name)}
                      title="Remove this name"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </td>
              <td className="actions-cell">
                <button
                  className="btn-secondary btn-small"
                  onClick={() => onAddToGroup(group.group_id)}
                >
                  + Add
                </button>
                <button
                  className="btn-danger btn-small"
                  onClick={() => onRemoveGroup(group)}
                >
                  × Remove All
                </button>
              </td>
            </tr>
          ))}
          {groups.length === 0 && (
            <tr>
              <td colSpan={3} className="empty-cell">No synonym groups defined yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
