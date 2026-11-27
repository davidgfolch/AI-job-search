import React from 'react';
import './ViewTabs.css';

interface ViewTabsProps {
    activeTab: 'list' | 'edit' | 'create';
    onTabChange: (tab: 'list' | 'edit' | 'create') => void;
    hasNewJobs?: boolean;
    newJobsCount?: number;
    onReload?: () => void;
    onDelete?: (count: number) => void;
    selectedCount?: number;
    hasSelection?: boolean;
}

const ViewTabs: React.FC<ViewTabsProps> = ({ activeTab, onTabChange, hasNewJobs, newJobsCount, onReload, onDelete, selectedCount = 0, hasSelection }) => {
    const newJobsLabel = newJobsCount && newJobsCount > 0 ? `${newJobsCount} new` : 'New jobs';
    const deleteLabel = selectedCount > 1 ? `Delete (${selectedCount})` : 'Delete';
    return (
        <>
            <button id="tab-button-list" className={`tab-button ${activeTab === 'list' ? 'active' : ''}`} onClick={() => onTabChange('list')} title="List view" aria-label="List view">
                <span className="tab-icon" aria-hidden="true">📋</span>
                <span className="tab-label">List</span>
            </button>
            {hasNewJobs && (
                <button id="tab-button-new" className="tab-button has-new-jobs" onClick={onReload} title="Click to reload list" aria-label="Click to reload list">
                    <span className="tab-icon reload-icon" aria-hidden="true">↻</span>
                    <span className="tab-label">{newJobsLabel}</span>
                </button>
            )}
            <button id="tab-button-edit" className={`tab-button ${activeTab === 'edit' ? 'active' : ''}`} onClick={() => onTabChange('edit')} title="Edit view" aria-label="Edit view">
                <span className="tab-icon" aria-hidden="true">✏️</span>
                <span className="tab-label">Edit</span>
            </button>
            <button id="tab-button-create" className={`tab-button ${activeTab === 'create' ? 'active' : ''}`} onClick={() => onTabChange('create')} title="Create view" aria-label="Create view">
                <span className="tab-icon" aria-hidden="true">➕</span>
                <span className="tab-label">Create</span>
            </button>
            {hasSelection && onDelete && (
                <button id="tab-button-delete" className="tab-button delete-button" onClick={() => onDelete(selectedCount)} title="Delete selected jobs" aria-label="Delete selected jobs">
                    <span className="tab-icon" aria-hidden="true">🗑️</span>
                    <span className="tab-label">{deleteLabel}</span>
                </button>
            )}
        </>
    );
};

export default ViewTabs;
