
import React from 'react';
import './ViewTabs.css';

interface ViewTabsProps {
    activeTab: 'list' | 'edit';
    onTabChange: (tab: 'list' | 'edit') => void;
    hasNewJobs?: boolean;
    newJobsCount?: number;
}

const ViewTabs: React.FC<ViewTabsProps> = ({ activeTab, onTabChange, hasNewJobs, newJobsCount }) => {
    return (
        <>
            <button 
                className={`tab-button ${activeTab === 'list' ? 'active' : ''} ${hasNewJobs ? 'has-new-jobs' : ''}`} 
                onClick={() => onTabChange('list')}
                title={hasNewJobs ? "Click to update list" : "List view"}
            >
                {hasNewJobs && <span className="new-badge" />}
                List
                {hasNewJobs && newJobsCount && newJobsCount > 0 ? ` (${newJobsCount} new)` : ''}
            </button>
            <button className={`tab-button ${activeTab === 'edit' ? 'active' : ''}`} onClick={() => onTabChange('edit')}>
                Edit
            </button>
        </>
    );
};

export default ViewTabs;
