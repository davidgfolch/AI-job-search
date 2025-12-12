
import React from 'react';

interface ViewTabsProps {
    activeTab: 'list' | 'edit';
    onTabChange: (tab: 'list' | 'edit') => void;
}

const ViewTabs: React.FC<ViewTabsProps> = ({ activeTab, onTabChange }) => {
    return (
        <>
            <button className={`tab-button ${activeTab === 'list' ? 'active' : ''}`} onClick={() => onTabChange('list')}>
                List
            </button>
            <button className={`tab-button ${activeTab === 'edit' ? 'active' : ''}`} onClick={() => onTabChange('edit')}>
                Edit
            </button>
        </>
    );
};

export default ViewTabs;
