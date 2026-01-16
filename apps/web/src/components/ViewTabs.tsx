
import React from 'react';
import './ViewTabs.css';

interface ViewTabsProps {
    activeTab: 'list' | 'edit' | 'create';
    onTabChange: (tab: 'list' | 'edit' | 'create') => void;
    hasNewJobs?: boolean;
    newJobsCount?: number;
    onReload?: () => void;
}

const ViewTabs: React.FC<ViewTabsProps> = ({ activeTab, onTabChange, hasNewJobs, newJobsCount, onReload }) => {
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
        </>
    );
};

export default ViewTabs;
