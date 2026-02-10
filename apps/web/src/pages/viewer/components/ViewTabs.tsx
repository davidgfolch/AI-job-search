
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

const ViewTabs: React.FC<ViewTabsProps> = ({ 
    activeTab, 
    onTabChange, 
    hasNewJobs, 
    newJobsCount, 
    onReload,
    onDelete,
    selectedCount = 0,
    hasSelection
}) => {
    return (
        <>
            <button 
                className={`tab-button ${activeTab === 'list' ? 'active' : ''}`} 
                onClick={() => onTabChange('list')}
                title="List view"
            >
                List
            </button>
            {hasNewJobs && (
                <button 
                    className="tab-button has-new-jobs"
                    onClick={onReload}
                    title="Click to reload list"
                >
                     <span className="reload-icon">↻</span>
                     {newJobsCount && newJobsCount > 0 ? `${newJobsCount} new` : 'New jobs'}
                </button>
            )}
            <button className={`tab-button ${activeTab === 'edit' ? 'active' : ''}`} onClick={() => onTabChange('edit')}>
                Edit
            </button>
            <button className={`tab-button ${activeTab === 'create' ? 'active' : ''}`} onClick={() => onTabChange('create')}>
                Create
            </button>
            {hasSelection && onDelete && (
                <button 
                    className="tab-button delete-button"
                    onClick={() => onDelete(selectedCount)}
                    title="Delete selected jobs"
                    style={{ backgroundColor: '#dc3545', color: 'white', marginLeft: 'auto' }}
                >
                    🗑️ Delete {selectedCount > 1 ? `(${selectedCount})` : ''}
                </button>
            )}
        </>
    );
};

export default ViewTabs;
